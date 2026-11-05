"""Operações atômicas do cadastro, com reenvio e edição concorrente controlados."""

import logging
import sqlite3
from collections.abc import Callable
from dataclasses import asdict
from datetime import UTC, datetime
from time import perf_counter
from uuid import uuid4

from sqlalchemy import Engine, select, update
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from radar_contratos.domain.contracts import Contract
from radar_contratos.errors import (
    IdempotencyConflictError,
    StaleRecordError,
    StorageBusyError,
    ValidationError,
)
from radar_contratos.infrastructure.persistence.models import AuditRow, ContractRow, OperationRow

logger = logging.getLogger(__name__)


def _contract(row: ContractRow) -> Contract:
    return Contract(
        row.id,
        row.title,
        row.record_version,
        row.created_at_utc,
        row.updated_at_utc,
        row.document_version,
    )


def _replay(operation: OperationRow | None, fingerprint: str) -> Contract | None:
    if operation is None:
        return None
    if operation.fingerprint != fingerprint:
        raise IdempotencyConflictError("A operação já foi usada com outros dados. Atualize a tela.")
    return Contract(**operation.response)


class SqliteContractStore:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def list_contracts(self) -> list[Contract]:
        with Session(self.engine) as session:
            rows = session.scalars(select(ContractRow).order_by(ContractRow.created_at_utc))
            return [_contract(row) for row in rows]

    def _change(
        self,
        *,
        request_id: str,
        fingerprint: str,
        actor: str,
        action: str,
        write: Callable[[Session, str], Contract],
    ) -> Contract:
        started = perf_counter()
        outcome = "failed"
        try:
            with Session(self.engine) as session, session.begin():
                previous = _replay(session.get(OperationRow, request_id), fingerprint)
                if previous is not None:
                    outcome = "replayed"
                    return previous
                at_utc = datetime.now(UTC).isoformat()
                result = write(session, at_utc)
                session.add(
                    OperationRow(
                        request_id=request_id,
                        fingerprint=fingerprint,
                        contract_id=result.id,
                        response=asdict(result),
                    )
                )
                session.flush()
                session.add(
                    AuditRow(
                        id=str(uuid4()),
                        request_id=request_id,
                        contract_id=result.id,
                        action=action,
                        actor=actor,
                        at_utc=at_utc,
                        details={"record_version": result.record_version},
                    )
                )
            outcome = "committed"
            return result
        except IntegrityError:
            # Outra tentativa pode ter concluído a mesma operação enquanto esperávamos.
            with Session(self.engine) as session:
                previous = _replay(session.get(OperationRow, request_id), fingerprint)
            if previous is not None:
                outcome = "replayed"
                return previous
            raise
        except OperationalError as exc:
            code = getattr(exc.orig, "sqlite_errorcode", 0) & 0xFF
            if code in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED):
                raise StorageBusyError("O banco está ocupado. Aguarde e tente novamente.") from exc
            raise
        finally:
            logger.info(
                "operation=%s request_id=%s outcome=%s duration_ms=%.2f",
                action,
                request_id,
                outcome,
                (perf_counter() - started) * 1000,
            )

    def register(self, *, title: str, actor: str, request_id: str, fingerprint: str) -> Contract:
        def write(session: Session, at_utc: str) -> Contract:
            row = ContractRow(
                id=str(uuid4()),
                title=title,
                record_version=1,
                created_at_utc=at_utc,
                updated_at_utc=at_utc,
            )
            session.add(row)
            session.flush()
            return _contract(row)

        return self._change(
            request_id=request_id,
            fingerprint=fingerprint,
            actor=actor,
            action="contract_registered",
            write=write,
        )

    def rename(
        self,
        *,
        contract_id: str,
        title: str,
        expected_version: int,
        actor: str,
        request_id: str,
        fingerprint: str,
    ) -> Contract:
        def write(session: Session, at_utc: str) -> Contract:
            row = session.get(ContractRow, contract_id)
            if row is None:
                raise ValidationError("O contrato não foi encontrado.")
            result = session.execute(
                update(ContractRow)
                .where(
                    ContractRow.id == contract_id, ContractRow.record_version == expected_version
                )
                .values(title=title, record_version=expected_version + 1, updated_at_utc=at_utc)
                .execution_options(synchronize_session=False)
            )
            if result.rowcount != 1:
                raise StaleRecordError(
                    "O contrato mudou em outra edição. Atualize antes de salvar."
                )
            session.refresh(row)
            return _contract(row)

        return self._change(
            request_id=request_id,
            fingerprint=fingerprint,
            actor=actor,
            action="contract_renamed",
            write=write,
        )
