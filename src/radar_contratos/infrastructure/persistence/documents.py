"""Revisão, recibo, arquivos originais e histórico na mesma transação SQLite."""

import logging
import sqlite3
from dataclasses import asdict
from datetime import UTC, datetime
from time import perf_counter
from uuid import uuid4

from sqlalchemy import Engine, select, update
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from radar_contratos.domain.documents import (
    DocumentRevision,
    DocumentRole,
    PreparedDocument,
    SubmissionReceipt,
)
from radar_contratos.errors import (
    IdempotencyConflictError,
    StaleRecordError,
    StorageBusyError,
    ValidationError,
)
from radar_contratos.infrastructure.persistence.models import (
    AuditRow,
    ContractRow,
    DocumentRevisionRow,
    DocumentUploadRow,
    OperationRow,
)

logger = logging.getLogger(__name__)


def _replay(row: OperationRow | None, fingerprint: str) -> SubmissionReceipt | None:
    if row is None:
        return None
    if row.fingerprint != fingerprint:
        raise IdempotencyConflictError("A operação já foi usada com outros dados. Atualize a tela.")
    return SubmissionReceipt(**row.response)


class SqliteDocumentStore:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def submit(
        self,
        *,
        contract_id: str,
        expected_version: int,
        actor: str,
        request_id: str,
        fingerprint: str,
        revision_key: str,
        documents: tuple[PreparedDocument, ...],
    ) -> SubmissionReceipt:
        started, outcome = perf_counter(), "failed"
        total_bytes = sum(len(item.original_bytes) for item in documents)
        try:
            with Session(self.engine) as session, session.begin():
                previous = _replay(session.get(OperationRow, request_id), fingerprint)
                if previous is not None:
                    outcome = "replayed"
                    return previous
                # A escrita condicional adquire o bloqueio antes da leitura da base atual.
                locked = session.execute(
                    update(ContractRow)
                    .where(
                        ContractRow.id == contract_id,
                        ContractRow.document_version == expected_version,
                    )
                    .values(document_version=expected_version)
                    .execution_options(synchronize_session=False)
                )
                if locked.rowcount != 1:
                    if session.get(ContractRow, contract_id) is None:
                        raise ValidationError("O contrato não foi encontrado.")
                    raise StaleRecordError(
                        "Os documentos mudaram em outro envio. Atualize antes de salvar."
                    )
                current = session.scalar(
                    select(DocumentRevisionRow).where(
                        DocumentRevisionRow.contract_id == contract_id,
                        DocumentRevisionRow.number == expected_version,
                    )
                )
                created = current is None or current.fingerprint != revision_key
                at_utc = datetime.now(UTC).isoformat()
                revision_id = str(uuid4()) if created else current.id
                number = expected_version + 1 if created else expected_version
                receipt = SubmissionReceipt(request_id, revision_id, number, created, actor, at_utc)
                session.add(
                    OperationRow(
                        request_id=request_id,
                        fingerprint=fingerprint,
                        contract_id=contract_id,
                        response=asdict(receipt),
                    )
                )
                session.flush()
                if created:
                    session.add(
                        DocumentRevisionRow(
                            id=revision_id,
                            contract_id=contract_id,
                            number=number,
                            fingerprint=revision_key,
                            source_request_id=request_id,
                            document_count=len(documents),
                            total_bytes=total_bytes,
                            actor=actor,
                            created_at_utc=at_utc,
                        )
                    )
                    session.flush()
                    session.execute(
                        update(ContractRow)
                        .where(ContractRow.id == contract_id)
                        .values(
                            document_version=number,
                        )
                    )
                for position, item in enumerate(documents):
                    session.add(
                        DocumentUploadRow(
                            id=str(uuid4()),
                            revision_id=revision_id,
                            request_id=request_id,
                            position=position,
                            **asdict(item),
                        )
                    )
                if created:
                    session.add(
                        AuditRow(
                            id=str(uuid4()),
                            request_id=request_id,
                            contract_id=contract_id,
                            action="documents_revised",
                            actor=actor,
                            at_utc=at_utc,
                            details={
                                "document_revision": number,
                                "document_count": len(documents),
                                "total_bytes": total_bytes,
                            },
                        )
                    )
            outcome = "revised" if created else "unchanged"
            return receipt
        except IntegrityError:
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
                "operation=documents_submit request_id=%s outcome=%s documents=%d bytes=%d "
                "duration_ms=%.2f",
                request_id,
                outcome,
                len(documents),
                total_bytes,
                (perf_counter() - started) * 1000,
            )

    def list_revisions(self, contract_id: str) -> list[DocumentRevision]:
        with Session(self.engine) as session:
            rows = session.scalars(
                select(DocumentRevisionRow)
                .where(DocumentRevisionRow.contract_id == contract_id)
                .order_by(DocumentRevisionRow.number.desc())
            )
            return [
                DocumentRevision(
                    row.id,
                    row.contract_id,
                    row.number,
                    row.source_request_id,
                    row.document_count,
                    row.total_bytes,
                    row.actor,
                    row.created_at_utc,
                )
                for row in rows
            ]

    def list_submissions(self, contract_id: str, revision_id: str) -> list[SubmissionReceipt]:
        with Session(self.engine) as session:
            revision = session.get(DocumentRevisionRow, revision_id)
            if revision is None or revision.contract_id != contract_id:
                raise ValidationError("A revisão não pertence a este contrato.")
            # Recibos de entrada documental são identificados pelo vínculo da revisão no JSON.
            rows = session.scalars(
                select(OperationRow).where(
                    OperationRow.contract_id == contract_id,
                    OperationRow.response["revision_id"].as_string() == revision_id,
                )
            )
            return sorted(
                [SubmissionReceipt(**row.response) for row in rows],
                key=lambda receipt: receipt.received_at_utc,
                reverse=True,
            )

    def get_documents(
        self, contract_id: str, revision_id: str, request_id: str
    ) -> tuple[PreparedDocument, ...]:
        with Session(self.engine) as session:
            receipt = session.get(OperationRow, request_id)
            revision = session.get(DocumentRevisionRow, revision_id)
            if (
                revision is None
                or revision.contract_id != contract_id
                or receipt is None
                or receipt.contract_id != contract_id
                or receipt.response.get("revision_id") != revision_id
            ):
                raise ValidationError("O envio não pertence à revisão deste contrato.")
            rows = session.scalars(
                select(DocumentUploadRow)
                .where(
                    DocumentUploadRow.revision_id == revision_id,
                    DocumentUploadRow.request_id == request_id,
                )
                .order_by(DocumentUploadRow.position)
            )
            return tuple(
                PreparedDocument(
                    row.filename,
                    DocumentRole(row.role),
                    row.original_bytes,
                    row.raw_sha256,
                    row.reference_text,
                    row.reference_sha256,
                    row.normalization_version,
                )
                for row in rows
            )

    def current_states(self) -> dict[str, str]:
        with Session(self.engine) as session:
            rows = session.execute(
                select(
                    DocumentRevisionRow.contract_id,
                    DocumentRevisionRow.document_count,
                    DocumentUploadRow.role,
                )
                .join(
                    ContractRow,
                    (ContractRow.id == DocumentRevisionRow.contract_id)
                    & (ContractRow.document_version == DocumentRevisionRow.number),
                )
                .outerjoin(
                    DocumentUploadRow,
                    (DocumentUploadRow.request_id == DocumentRevisionRow.source_request_id),
                )
            )
            states = {}
            for contract_id, count, role in rows:
                if count == 0:
                    states[contract_id] = "Aguardando documentos"
                elif role == DocumentRole.AMENDMENT:
                    states[contract_id] = "Bloqueado: aditivo declarado"
                elif states.get(contract_id) != "Bloqueado: aditivo declarado":
                    states[contract_id] = "Aguardando análise"
            known_amendments = session.scalars(
                select(DocumentRevisionRow.contract_id)
                .join(DocumentUploadRow, DocumentUploadRow.revision_id == DocumentRevisionRow.id)
                .where(DocumentUploadRow.role == DocumentRole.AMENDMENT)
                .distinct()
            )
            for contract_id in known_amendments:
                states[contract_id] = "Bloqueado: aditivo declarado"
            return states
