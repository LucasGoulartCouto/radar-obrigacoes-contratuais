"""Levantamentos imutáveis e conferência atômica vinculada à base atual."""

import logging
import sqlite3
from collections.abc import Callable
from datetime import UTC, date, datetime
from time import perf_counter
from uuid import uuid4

from sqlalchemy import Engine, select, update
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from radar_contratos.application.inputs import fingerprint as content_fingerprint
from radar_contratos.domain import assisted
from radar_contratos.domain import reviews as rules
from radar_contratos.domain.reviews import (
    AnalysisSnapshot,
    AnalysisSummary,
    EvidenceInput,
    ManualDraft,
    ReferenceDocument,
    prepare_manual_analysis,
)
from radar_contratos.errors import (
    IdempotencyConflictError,
    StaleRecordError,
    StorageBusyError,
    ValidationError,
)
from radar_contratos.infrastructure.local_classifier import method_kernel
from radar_contratos.infrastructure.persistence.analysis_method import (
    method_is_current,
    selected_execution_join,
)
from radar_contratos.infrastructure.persistence.models import (
    AnalysisRow,
    AuditRow,
    ConfirmedEventRow,
    ContractRow,
    DocumentRevisionRow,
    DocumentUploadRow,
    ExtractionRunRow,
    OperationRow,
    ReviewRow,
)

logger = logging.getLogger(__name__)


def _replay(row: OperationRow | None, fingerprint: str) -> dict | None:
    if row is None:
        return None
    if row.fingerprint != fingerprint:
        raise IdempotencyConflictError("A operação já foi usada com outros dados. Atualize a tela.")
    return row.response


def _known_amendment(session: Session, contract_id: str) -> bool:
    if session.scalar(
        select(ContractRow.known_textual_amendment).where(ContractRow.id == contract_id)
    ):
        return True
    return (
        session.scalar(
            select(DocumentUploadRow.id)
            .join(DocumentRevisionRow, DocumentRevisionRow.id == DocumentUploadRow.revision_id)
            .where(
                DocumentRevisionRow.contract_id == contract_id, DocumentUploadRow.role == "aditivo"
            )
            .limit(1)
        )
        is not None
    )


def _references(session: Session, revision: DocumentRevisionRow) -> tuple[ReferenceDocument, ...]:
    rows = session.execute(
        select(
            DocumentUploadRow.id,
            DocumentUploadRow.position,
            DocumentUploadRow.reference_text,
            DocumentUploadRow.reference_sha256,
            DocumentUploadRow.normalization_version,
            DocumentUploadRow.role,
        )
        .where(
            DocumentUploadRow.request_id == revision.source_request_id,
            DocumentUploadRow.revision_id == revision.id,
        )
        .order_by(DocumentUploadRow.position)
    )
    return tuple(ReferenceDocument(*row) for row in rows)


def _lock(session: Session, contract_id: str, document_version: int, analysis_version: int) -> None:
    result = session.execute(
        update(ContractRow)
        .where(
            ContractRow.id == contract_id,
            ContractRow.document_version == document_version,
            ContractRow.analysis_version == analysis_version,
        )
        .values(analysis_version=analysis_version)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        raise StaleRecordError("A base ou o levantamento mudou. Atualize antes de continuar.")


def _restore_draft(payload: dict) -> ManualDraft:
    try:
        data = dict(payload["input"])
        data["end_date"] = date.fromisoformat(data["end_date"]) if data["end_date"] else None
        for key in ("end_evidence", "notice_evidence", "blocker_evidence"):
            if data[key] is not None:
                data[key] = EvidenceInput(**data[key])
        return ManualDraft(**data)
    except (ValueError, TypeError, KeyError) as exc:
        raise ValidationError("O levantamento armazenado precisa ser refeito.") from exc


class SqliteReviewStore:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def _change(
        self,
        *,
        contract_id: str,
        request_id: str,
        fingerprint: str,
        actor: str,
        operation: str,
        write: Callable[[Session, str], tuple[dict, bool]],
    ) -> dict:
        started, outcome = perf_counter(), "failed"
        try:
            # Recibos persistidos são imutáveis. Reenvio não precisa reservar escritor.
            # Fechar esta leitura antes da escrita evita promover um snapshot DEFERRED.
            with Session(self.engine) as session:
                previous = _replay(session.get(OperationRow, request_id), fingerprint)
            if previous is not None:
                outcome = "replayed"
                return previous
            with Session(self.engine) as session, session.begin():
                # Reserve a escrita antes de abrir um snapshot de leitura (SQLite DEFERRED).
                session.execute(
                    update(ContractRow)
                    .where(ContractRow.id == contract_id)
                    .values(analysis_version=ContractRow.analysis_version)
                    .execution_options(synchronize_session=False)
                )
                previous = _replay(session.get(OperationRow, request_id), fingerprint)
                if previous is not None:
                    # Outro executor pode ter concluído após a leitura inicial.
                    # Desfazer a reserva neutra evita um commit de escrita sem efeito.
                    session.rollback()
                    outcome = "replayed"
                    return previous
                at_utc = datetime.now(UTC).isoformat()
                response, changed = write(session, at_utc)
                session.add(
                    OperationRow(
                        request_id=request_id,
                        fingerprint=fingerprint,
                        contract_id=contract_id,
                        response=response,
                    )
                )
                session.flush()
                if changed:
                    session.add(
                        AuditRow(
                            id=str(uuid4()),
                            request_id=request_id,
                            contract_id=contract_id,
                            action=operation,
                            actor=actor,
                            at_utc=at_utc,
                            details={
                                key: response[key]
                                for key in ("analysis_id", "analysis_version", "run_id", "status")
                                if key in response
                            },
                        )
                    )
            outcome = "committed" if changed else "unchanged"
            return response
        except IntegrityError, StaleRecordError:
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
                operation,
                request_id,
                outcome,
                (perf_counter() - started) * 1000,
            )

    def register(
        self,
        *,
        contract_id: str,
        expected_document_version: int,
        expected_analysis_version: int,
        actor: str,
        request_id: str,
        fingerprint: str,
        draft: ManualDraft,
        change_reason: str,
    ) -> dict:
        def write(session: Session, at_utc: str) -> tuple[dict, bool]:
            _lock(session, contract_id, expected_document_version, expected_analysis_version)
            revision = session.scalar(
                select(DocumentRevisionRow).where(
                    DocumentRevisionRow.contract_id == contract_id,
                    DocumentRevisionRow.number == expected_document_version,
                )
            )
            if revision is None or revision.document_count == 0:
                raise ValidationError("Receba documentos antes de registrar um levantamento.")
            payload = prepare_manual_analysis(
                draft,
                _references(session, revision),
                known_amendment=_known_amendment(session, contract_id),
            )
            content_key = content_fingerprint(payload)
            current = session.scalar(
                select(AnalysisRow).where(
                    AnalysisRow.contract_id == contract_id,
                    AnalysisRow.number == expected_analysis_version,
                    AnalysisRow.revision_id == revision.id,
                )
            )
            changed = current is None or current.fingerprint != content_key
            if changed:
                if current is not None and not change_reason:
                    raise ValidationError(
                        "Explique o motivo da correção antes de alterar o levantamento."
                    )
                current = AnalysisRow(
                    id=str(uuid4()),
                    contract_id=contract_id,
                    revision_id=revision.id,
                    number=expected_analysis_version + 1,
                    fingerprint=content_key,
                    payload=payload,
                    rule_version=rules.RULE_VERSION,
                    method_version=rules.METHOD_VERSION,
                    blocked=bool(payload["blockers"]),
                    candidate_count=len(payload["candidate_events"]),
                    change_reason=change_reason,
                    actor=actor,
                    created_at_utc=at_utc,
                )
                session.add(current)
                session.flush()
                session.execute(
                    update(ContractRow)
                    .where(ContractRow.id == contract_id)
                    .values(analysis_version=current.number)
                )
            return {
                "analysis_id": current.id,
                "analysis_version": current.number,
                "document_version": expected_document_version,
                "created": changed,
            }, changed

        return self._change(
            contract_id=contract_id,
            request_id=request_id,
            fingerprint=fingerprint,
            actor=actor,
            operation="manual_analysis_registered",
            write=write,
        )

    def confirm(
        self,
        *,
        contract_id: str,
        analysis_id: str,
        expected_document_version: int,
        expected_analysis_version: int,
        expected_rule_version: str,
        actor: str,
        request_id: str,
        fingerprint: str,
        empty_acknowledged: bool,
    ) -> dict:
        def write(session: Session, at_utc: str) -> tuple[dict, bool]:
            _lock(session, contract_id, expected_document_version, expected_analysis_version)
            analysis = session.get(AnalysisRow, analysis_id)
            revision = session.get(DocumentRevisionRow, analysis.revision_id) if analysis else None
            if (
                analysis is None
                or analysis.contract_id != contract_id
                or analysis.number != expected_analysis_version
                or revision is None
                or revision.number != expected_document_version
                or analysis.rule_version != rules.RULE_VERSION
                or expected_rule_version != rules.RULE_VERSION
            ):
                raise StaleRecordError("O levantamento exibido não corresponde à base atual.")
            if analysis.method_version == rules.METHOD_VERSION:
                payload = prepare_manual_analysis(
                    _restore_draft(analysis.payload),
                    _references(session, revision),
                    known_amendment=_known_amendment(session, contract_id),
                )
            else:
                from radar_contratos.infrastructure.persistence.extractions import rebuild_assisted

                payload = rebuild_assisted(session, analysis, revision)
            if analysis.method_version == rules.METHOD_VERSION:
                checked_key = content_fingerprint(payload)
            else:
                from radar_contratos.infrastructure.persistence.extractions import analysis_key

                checked_key = analysis_key(payload)
            if payload != analysis.payload or checked_key != analysis.fingerprint:
                raise StaleRecordError("A evidência ou regra mudou. Refaça o levantamento.")
            if payload["blockers"]:
                raise ValidationError("O contrato tem impedimento. Não é possível confirmar.")
            if not payload["candidate_events"] and not empty_acknowledged:
                raise ValidationError("Confira explicitamente a ausência de eventos no recorte.")
            review = session.scalar(select(ReviewRow).where(ReviewRow.analysis_id == analysis.id))
            changed = review is None
            if changed:
                review = ReviewRow(
                    id=str(uuid4()), analysis_id=analysis.id, actor=actor, reviewed_at_utc=at_utc
                )
                session.add(review)
                session.flush()
                for candidate in payload["candidate_events"]:
                    session.add(
                        ConfirmedEventRow(
                            id=str(uuid4()),
                            review_id=review.id,
                            kind=candidate["kind"],
                            event_date=candidate["date"],
                        )
                    )
            return {
                "analysis_id": analysis.id,
                "analysis_version": analysis.number,
                "document_version": revision.number,
                "review_id": review.id,
                "created": changed,
            }, changed

        return self._change(
            contract_id=contract_id,
            request_id=request_id,
            fingerprint=fingerprint,
            actor=actor,
            operation="analysis_confirmed",
            write=write,
        )

    def get_analysis(
        self, contract_id: str, analysis_id: str | None = None
    ) -> AnalysisSnapshot | None:
        with Session(self.engine) as session:
            query = (
                select(
                    AnalysisRow,
                    DocumentRevisionRow,
                    ContractRow,
                    ReviewRow,
                    ExtractionRunRow.status,
                    ExtractionRunRow.method,
                )
                .join(DocumentRevisionRow, DocumentRevisionRow.id == AnalysisRow.revision_id)
                .join(ContractRow, ContractRow.id == AnalysisRow.contract_id)
                .outerjoin(ReviewRow, ReviewRow.analysis_id == AnalysisRow.id)
                .outerjoin(ExtractionRunRow, selected_execution_join())
                .where(AnalysisRow.contract_id == contract_id)
            )
            if analysis_id is None:
                query = query.where(
                    AnalysisRow.number == ContractRow.analysis_version,
                    DocumentRevisionRow.number == ContractRow.document_version,
                )
            else:
                query = query.where(AnalysisRow.id == analysis_id)
            result = session.execute(query).first()
            if result is None:
                return None
            analysis, revision, contract, review, run_status, run_method = result
            return AnalysisSnapshot(
                analysis.id,
                contract.id,
                revision.id,
                revision.number,
                analysis.number,
                analysis.actor,
                analysis.created_at_utc,
                analysis.payload,
                analysis.number == contract.analysis_version
                and revision.number == contract.document_version
                and analysis.rule_version == rules.RULE_VERSION
                and method_is_current(
                    analysis.method_version, run_status, run_method, kernel=method_kernel()
                )
                and (analysis.blocked or not _known_amendment(session, contract_id)),
                review.id if review else None,
                review.actor if review else None,
                review.reviewed_at_utc if review else None,
                analysis.change_reason,
            )

    def list_history(self, contract_id: str) -> list[AnalysisSummary]:
        with Session(self.engine) as session:
            known_amendment = _known_amendment(session, contract_id)
            rows = session.execute(
                select(
                    AnalysisRow.id,
                    AnalysisRow.number,
                    DocumentRevisionRow.number,
                    ContractRow.document_version,
                    ContractRow.analysis_version,
                    AnalysisRow.rule_version,
                    AnalysisRow.method_version,
                    AnalysisRow.blocked,
                    ReviewRow.id,
                    ExtractionRunRow.status,
                    ExtractionRunRow.method,
                )
                .join(DocumentRevisionRow, DocumentRevisionRow.id == AnalysisRow.revision_id)
                .join(ContractRow, ContractRow.id == AnalysisRow.contract_id)
                .outerjoin(ReviewRow, ReviewRow.analysis_id == AnalysisRow.id)
                .outerjoin(ExtractionRunRow, selected_execution_join())
                .where(AnalysisRow.contract_id == contract_id)
                .order_by(AnalysisRow.number.desc())
            )
            kernel = method_kernel()
            return [
                AnalysisSummary(
                    identifier,
                    number,
                    doc_number,
                    number == current_number
                    and doc_number == current_doc
                    and rule == rules.RULE_VERSION
                    and method_is_current(method, run_status, run_method, kernel=kernel)
                    and (blocked or not known_amendment),
                    review is not None,
                )
                for (
                    identifier,
                    number,
                    doc_number,
                    current_doc,
                    current_number,
                    rule,
                    method,
                    blocked,
                    review,
                    run_status,
                    run_method,
                ) in rows
            ]

    def current_states(self) -> dict[str, str]:
        with Session(self.engine) as session:
            rows = session.execute(
                select(
                    AnalysisRow.contract_id,
                    AnalysisRow.blocked,
                    AnalysisRow.candidate_count,
                    AnalysisRow.rule_version,
                    AnalysisRow.method_version,
                    ReviewRow.id,
                    ExtractionRunRow.status,
                    ExtractionRunRow.method,
                )
                .join(
                    ContractRow,
                    (ContractRow.id == AnalysisRow.contract_id)
                    & (ContractRow.analysis_version == AnalysisRow.number),
                )
                .join(
                    DocumentRevisionRow,
                    (DocumentRevisionRow.id == AnalysisRow.revision_id)
                    & (DocumentRevisionRow.number == ContractRow.document_version),
                )
                .outerjoin(ReviewRow, ReviewRow.analysis_id == AnalysisRow.id)
                .outerjoin(ExtractionRunRow, selected_execution_join())
            )
            states = {}
            kernel = method_kernel()
            for contract_id, blocked, count, rule, method, review, run_status, run_method in rows:
                if blocked:
                    states[contract_id] = "Bloqueado"
                elif (
                    review is None
                    or rule != rules.RULE_VERSION
                    or not method_is_current(method, run_status, run_method, kernel=kernel)
                ):
                    states[contract_id] = "Revisão pendente"
                else:
                    states[contract_id] = (
                        "Conferido com eventos" if count else "Conferido sem eventos no recorte"
                    )
            amendments = session.scalars(
                select(DocumentRevisionRow.contract_id)
                .join(DocumentUploadRow, DocumentUploadRow.revision_id == DocumentRevisionRow.id)
                .where(DocumentUploadRow.role == "aditivo")
                .distinct()
            )
            for contract_id in amendments:
                states[contract_id] = "Bloqueado: aditivo declarado"
            for contract_id in session.scalars(
                select(ContractRow.id).where(
                    ContractRow.known_textual_amendment.is_(True),
                )
            ):
                states[contract_id] = "Bloqueado: aditivo identificado"
            return states

    def current_events(self, contract_id: str) -> list[dict]:
        with Session(self.engine) as session:
            if _known_amendment(session, contract_id):
                return []
            rows = session.execute(
                select(
                    ConfirmedEventRow,
                    AnalysisRow.method_version,
                    ExtractionRunRow.status,
                    ExtractionRunRow.method,
                )
                .join(ReviewRow, ReviewRow.id == ConfirmedEventRow.review_id)
                .join(AnalysisRow, AnalysisRow.id == ReviewRow.analysis_id)
                .join(
                    ContractRow,
                    (ContractRow.id == AnalysisRow.contract_id)
                    & (ContractRow.analysis_version == AnalysisRow.number),
                )
                .join(
                    DocumentRevisionRow,
                    (DocumentRevisionRow.id == AnalysisRow.revision_id)
                    & (DocumentRevisionRow.number == ContractRow.document_version),
                )
                .outerjoin(ExtractionRunRow, selected_execution_join())
                .where(
                    ContractRow.id == contract_id,
                    AnalysisRow.rule_version == rules.RULE_VERSION,
                    AnalysisRow.method_version.in_((rules.METHOD_VERSION, assisted.METHOD_VERSION)),
                    AnalysisRow.blocked.is_(False),
                )
                .order_by(ConfirmedEventRow.kind)
            )
            kernel = method_kernel()
            return [
                {"kind": row.kind, "date": row.event_date, "review_id": row.review_id}
                for row, method, run_status, run_method in rows
                if method_is_current(method, run_status, run_method, kernel=kernel)
            ]
