"""Tentativas duráveis e seleção assistida; inferência não ocorre nesta camada."""

from dataclasses import asdict
from datetime import UTC, datetime
from uuid import NAMESPACE_URL, uuid4, uuid5

from sqlalchemy import func, select, update
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from radar_contratos.application.inputs import fingerprint as content_key
from radar_contratos.domain.assisted import (
    METHOD_VERSION,
    literal_lines,
    prepare_assisted_analysis,
    restore_context,
)
from radar_contratos.domain.literal_extraction import AFFIRMATIVE_AMENDMENT
from radar_contratos.domain.reviews import RULE_VERSION
from radar_contratos.errors import RadarError, StaleRecordError, StorageBusyError, ValidationError
from radar_contratos.infrastructure.local_classifier import method_kernel
from radar_contratos.infrastructure.persistence.analysis_method import (
    method_is_current,
    selected_execution_join,
)
from radar_contratos.infrastructure.persistence.models import (
    AnalysisRow,
    ContractRow,
    DocumentRevisionRow,
    ExtractionRunRow,
)
from radar_contratos.infrastructure.persistence.reviews import (
    SqliteReviewStore,
    _known_amendment,
    _lock,
    _references,
)


def analysis_key(payload: dict) -> str:
    return content_key({key: value for key, value in payload.items() if key != "execution_id"})


def _snapshot(row: ExtractionRunRow, version: int) -> dict:
    return {
        "run_id": row.id,
        "number": row.number,
        "contract_id": row.contract_id,
        "revision_id": row.revision_id,
        "document_version": version,
        "analysis_version": row.analysis_version,
        "status": row.status,
        "input_sha256": row.input_sha256,
        "method": row.method,
        "output": row.output,
        "blocked": row.blocked,
        "error_code": row.error_code,
        "actor": row.actor,
        "created_at_utc": row.created_at_utc,
        "started_at_utc": row.started_at_utc,
        "finished_at_utc": row.finished_at_utc,
        "duration_ms": row.duration_ms,
    }


def _run(session, contract_id, run_id):
    row = session.get(ExtractionRunRow, run_id)
    if row is None or row.contract_id != contract_id:
        raise ValidationError("A tentativa não pertence a este contrato.")
    return row


def _payload(session, run, revision, **context_review):
    documents = _references(session, revision)
    if content_key({"documents": [asdict(document) for document in documents]}) != run.input_sha256:
        raise StaleRecordError("A origem armazenada mudou. Refaça a análise.")
    payload = prepare_assisted_analysis(
        documents,
        run.output["classifications"],
        run.output["abstained"],
        known_amendment=_known_amendment(session, run.contract_id),
        **context_review,
    )
    payload["execution_id"] = run.id
    return payload


def rebuild_assisted(session, analysis, revision):
    if not analysis.execution_id or analysis.execution_id != analysis.payload.get("execution_id"):
        raise StaleRecordError("A referência da execução mudou. Refaça a análise e a conferência.")
    run = _run(session, analysis.contract_id, analysis.payload["execution_id"])
    if (
        analysis.method_version != METHOD_VERSION
        or run.status != "completed"
        or run.revision_id != revision.id
        or run.method["kernel"] != method_kernel()
    ):
        raise StaleRecordError("A execução ou o método mudou. Refaça a análise e a conferência.")
    return _payload(session, run, revision, **restore_context(analysis.payload))


class SqliteExtractionStore(SqliteReviewStore):
    """Reutiliza somente o executor transacional/recibos do repositório de conferência."""

    def context(self, contract_id: str, run_id: str | None = None) -> dict:
        with Session(self.engine) as session:
            contract = session.get(ContractRow, contract_id)
            if contract is None:
                raise ValidationError("Contrato não encontrado.")
            run = _run(session, contract_id, run_id) if run_id else None
            revision = (
                session.get(DocumentRevisionRow, run.revision_id)
                if run
                else session.scalar(
                    select(DocumentRevisionRow).where(
                        DocumentRevisionRow.contract_id == contract_id,
                        DocumentRevisionRow.number == contract.document_version,
                    )
                )
            )
            if revision is None or revision.document_count == 0:
                raise ValidationError("Receba documentos antes de iniciar a análise.")
            return {
                "documents": _references(session, revision),
                "known_amendment": _known_amendment(session, contract_id),
                "run": _snapshot(run, revision.number) if run else None,
                "current_document_version": contract.document_version,
                "current_analysis_version": contract.analysis_version,
            }

    def request(
        self,
        *,
        contract_id,
        expected_document_version,
        expected_analysis_version,
        actor,
        request_id,
        fingerprint,
        method,
        input_sha256,
    ):
        def write(session, at_utc):
            _lock(session, contract_id, expected_document_version, expected_analysis_version)
            revision = session.scalar(
                select(DocumentRevisionRow).where(
                    DocumentRevisionRow.contract_id == contract_id,
                    DocumentRevisionRow.number == expected_document_version,
                )
            )
            if revision is None or revision.document_count == 0:
                raise ValidationError("Receba documentos antes de iniciar a análise.")
            documents = _references(session, revision)
            if any(AFFIRMATIVE_AMENDMENT.search(line.text) for line in literal_lines(documents)):
                session.execute(
                    update(ContractRow)
                    .where(ContractRow.id == contract_id)
                    .values(
                        known_textual_amendment=True,
                    )
                )
            if content_key({"documents": [asdict(d) for d in documents]}) != input_sha256:
                raise StaleRecordError("A origem mudou antes de reservar a análise.")
            if session.scalar(
                select(ExtractionRunRow.id).where(
                    ExtractionRunRow.contract_id == contract_id,
                    ExtractionRunRow.revision_id == revision.id,
                    ExtractionRunRow.status.in_(("pending", "running")),
                )
            ):
                raise ValidationError(
                    "Há uma tentativa incompleta. Consulte e encerre-a antes de refazer."
                )
            number = (
                session.scalar(
                    select(func.max(ExtractionRunRow.number)).where(
                        ExtractionRunRow.contract_id == contract_id,
                    )
                )
                or 0
            )
            row = ExtractionRunRow(
                id=str(uuid4()),
                contract_id=contract_id,
                revision_id=revision.id,
                number=number + 1,
                analysis_version=expected_analysis_version,
                status="pending",
                input_sha256=input_sha256,
                method=method,
                output=None,
                blocked=False,
                error_code="",
                actor=actor,
                created_at_utc=at_utc,
            )
            session.add(row)
            session.flush()
            return {"run_id": row.id, "status": "pending"}, True

        return self._change(
            contract_id=contract_id,
            request_id=request_id,
            fingerprint=fingerprint,
            actor=actor,
            operation="extraction_requested",
            write=write,
        )

    def claim(self, contract_id: str, run_id: str) -> bool:
        try:
            return self._claim_pending(contract_id, run_id)
        except OperationalError as exc:
            code = getattr(exc.orig, "sqlite_errorcode", 0) & 0xFF
            if code in {5, 6}:
                raise StorageBusyError(
                    "O banco está ocupado. Aguarde e atualize a tentativa."
                ) from exc
            raise RadarError(
                "Não foi possível iniciar a tentativa. Atualize e confira o armazenamento."
            ) from exc

    def _claim_pending(self, contract_id: str, run_id: str) -> bool:
        with Session(self.engine) as session, session.begin():
            result = session.execute(
                update(ExtractionRunRow)
                .where(
                    ExtractionRunRow.id == run_id,
                    ExtractionRunRow.contract_id == contract_id,
                    ExtractionRunRow.status == "pending",
                )
                .values(status="running", started_at_utc=datetime.now(UTC).isoformat())
                .execution_options(synchronize_session=False)
            )
            if result.rowcount == 0:
                _run(session, contract_id, run_id)
            return result.rowcount == 1

    def finish(self, contract_id, run_id, *, status, output, duration_ms):
        if status not in {"completed", "failed", "interrupted"}:
            raise ValidationError("Estado final de tentativa inválido.")

        def write(session, at_utc):
            row = _run(session, contract_id, run_id)
            result = session.execute(
                update(ExtractionRunRow)
                .where(
                    ExtractionRunRow.id == run_id,
                    ExtractionRunRow.status == "running",
                )
                .values(status=status)
                .execution_options(synchronize_session=False)
            )
            if result.rowcount != 1:
                raise StaleRecordError(
                    "A tentativa já terminou ou foi encerrada. Nenhum resultado selecionado."
                )
            if status == "completed":
                revision = session.get(DocumentRevisionRow, row.revision_id)
                payload = prepare_assisted_analysis(
                    _references(session, revision),
                    output["classifications"],
                    output["abstained"],
                    known_amendment=_known_amendment(session, contract_id),
                )
                row.blocked = bool(payload["blockers"])
                # Conhecimento textual afirmativo persiste mesmo em revisão que depois for retirada.
                if any(
                    AFFIRMATIVE_AMENDMENT.search(line.text)
                    for line in literal_lines(_references(session, revision))
                ):
                    session.execute(
                        update(ContractRow)
                        .where(ContractRow.id == contract_id)
                        .values(
                            known_textual_amendment=True,
                        )
                    )
            row.status, row.output = status, output
            row.error_code = (
                ""
                if status == "completed"
                else "EXTRACTION_FAILED"
                if status == "failed"
                else "INTERRUPTED"
            )
            row.finished_at_utc, row.duration_ms = at_utc, duration_ms
            return {"run_id": run_id, "status": status}, True

        return self._change(
            contract_id=contract_id,
            request_id=str(uuid5(NAMESPACE_URL, f"radar:finish:{run_id}")),
            fingerprint=content_key({"run_id": run_id, "status": status, "output": output}),
            actor="Execução local",
            operation="extraction_finished",
            write=write,
        )

    def interrupt(self, *, contract_id, run_id, actor, request_id, fingerprint):
        def write(session, at_utc):
            row = _run(session, contract_id, run_id)
            result = session.execute(
                update(ExtractionRunRow)
                .where(
                    ExtractionRunRow.id == run_id,
                    ExtractionRunRow.status.in_(("pending", "running")),
                )
                .values(status="interrupted", error_code="INTERRUPTED", finished_at_utc=at_utc)
            )
            if result.rowcount != 1:
                raise StaleRecordError("A tentativa já terminou. Atualize antes de continuar.")
            return {"run_id": row.id, "status": "interrupted"}, True

        return self._change(
            contract_id=contract_id,
            request_id=request_id,
            fingerprint=fingerprint,
            actor=actor,
            operation="extraction_interrupted",
            write=write,
        )

    def select_result(
        self,
        *,
        contract_id,
        run_id,
        expected_document_version,
        expected_analysis_version,
        actor,
        request_id,
        fingerprint,
        change_reason,
        decisions,
        expected_source,
        acknowledged,
        kernel,
    ):
        def write(session, at_utc):
            _lock(session, contract_id, expected_document_version, expected_analysis_version)
            run = _run(session, contract_id, run_id)
            revision = session.get(DocumentRevisionRow, run.revision_id)
            if (
                run.status != "completed"
                or revision.number != expected_document_version
                or run.method["kernel"] != kernel
                or kernel != method_kernel()
            ):
                raise StaleRecordError("A tentativa não corresponde à revisão e ao método atuais.")
            payload = _payload(
                session,
                run,
                revision,
                decisions=decisions,
                expected_source=expected_source,
                actor=actor,
                acknowledged=acknowledged,
            )
            key = analysis_key(payload)
            current = session.scalar(
                select(AnalysisRow).where(
                    AnalysisRow.contract_id == contract_id,
                    AnalysisRow.number == expected_analysis_version,
                    AnalysisRow.revision_id == revision.id,
                )
            )
            changed = current is None or current.fingerprint != key
            if not changed:
                selected_run = session.scalar(
                    select(ExtractionRunRow)
                    .select_from(AnalysisRow)
                    .join(ExtractionRunRow, selected_execution_join())
                    .where(AnalysisRow.id == current.id)
                )
                changed = selected_run is None or not method_is_current(
                    current.method_version, selected_run.status, selected_run.method, kernel=kernel
                )
            if changed:
                if run.analysis_version != expected_analysis_version and (
                    current is None or current.payload.get("execution_id") != run.id
                ):
                    raise StaleRecordError(
                        "O levantamento mudou durante a tentativa. Refaça a análise."
                    )
                if current is not None and not change_reason:
                    raise ValidationError(
                        "Explique por que deseja substituir o levantamento atual."
                    )
                current = AnalysisRow(
                    id=str(uuid4()),
                    contract_id=contract_id,
                    revision_id=revision.id,
                    number=expected_analysis_version + 1,
                    fingerprint=key,
                    payload=payload,
                    method_version=METHOD_VERSION,
                    execution_id=run.id,
                    rule_version=RULE_VERSION,
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
                    .values(
                        analysis_version=current.number,
                    )
                )
            return {
                "run_id": run_id,
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
            operation="assisted_analysis_selected",
            write=write,
        )

    def list_runs(self, contract_id: str) -> list[dict]:
        with Session(self.engine) as session:
            rows = session.execute(
                select(ExtractionRunRow, DocumentRevisionRow.number)
                .join(
                    DocumentRevisionRow,
                    DocumentRevisionRow.id == ExtractionRunRow.revision_id,
                )
                .where(ExtractionRunRow.contract_id == contract_id)
                .order_by(ExtractionRunRow.number.desc())
            )
            return [_snapshot(row, version) for row, version in rows]
