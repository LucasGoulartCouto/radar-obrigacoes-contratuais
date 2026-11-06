"""Leitura única de metadados: carteira completa e eventos da base vigente."""

import logging
import sqlite3
from datetime import date
from time import perf_counter

from sqlalchemy import Engine, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, aliased

from radar_contratos.domain import reviews as rules
from radar_contratos.domain.agenda import (
    AgendaEvent,
    CoverageState,
    PortfolioContract,
    PortfolioSnapshot,
    coverage_for,
)
from radar_contratos.errors import RadarError, StorageBusyError
from radar_contratos.infrastructure.local_classifier import method_kernel
from radar_contratos.infrastructure.persistence.analysis_method import (
    method_is_current,
    selected_execution_join,
)
from radar_contratos.infrastructure.persistence.models import (
    AnalysisRow,
    ConfirmedEventRow,
    ContractRow,
    DocumentRevisionRow,
    DocumentUploadRow,
    ExtractionRunRow,
    ReviewRow,
)

logger = logging.getLogger(__name__)


class SqliteAgendaStore:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def read_portfolio(self) -> PortfolioSnapshot:
        started = perf_counter()
        historical_revision = aliased(DocumentRevisionRow)
        selected_run = aliased(ExtractionRunRow)
        amendment = ContractRow.known_textual_amendment | (
            select(DocumentUploadRow.id)
            .join(historical_revision, historical_revision.id == DocumentUploadRow.revision_id)
            .where(
                historical_revision.contract_id == ContractRow.id,
                DocumentUploadRow.role == "aditivo",
            )
            .correlate(ContractRow)
            .exists()
        )
        latest_run = (
            select(ExtractionRunRow.id)
            .join(historical_revision, historical_revision.id == ExtractionRunRow.revision_id)
            .where(
                ExtractionRunRow.contract_id == ContractRow.id,
                historical_revision.number == ContractRow.document_version,
            )
            .order_by(ExtractionRunRow.number.desc())
            .limit(1)
            .correlate(ContractRow)
            .scalar_subquery()
        )
        query = (
            select(
                ContractRow.id.label("contract_id"),
                ContractRow.title,
                ContractRow.document_version,
                ContractRow.analysis_version,
                DocumentRevisionRow.document_count,
                AnalysisRow.id.label("analysis_id"),
                AnalysisRow.rule_version,
                AnalysisRow.method_version,
                AnalysisRow.blocked,
                AnalysisRow.candidate_count,
                ReviewRow.id.label("review_id"),
                ReviewRow.actor.label("reviewer"),
                ReviewRow.reviewed_at_utc,
                ConfirmedEventRow.id.label("event_id"),
                ConfirmedEventRow.kind,
                ConfirmedEventRow.event_date,
                amendment.label("known_amendment"),
                ExtractionRunRow.status.label("execution_status"),
                ExtractionRunRow.blocked.label("execution_blocked"),
                selected_run.status.label("analysis_execution_status"),
                selected_run.method.label("analysis_execution_method"),
            )
            .select_from(ContractRow)
            .outerjoin(
                DocumentRevisionRow,
                (DocumentRevisionRow.contract_id == ContractRow.id)
                & (DocumentRevisionRow.number == ContractRow.document_version),
            )
            .outerjoin(
                AnalysisRow,
                (AnalysisRow.contract_id == ContractRow.id)
                & (AnalysisRow.number == ContractRow.analysis_version)
                & (AnalysisRow.revision_id == DocumentRevisionRow.id),
            )
            .outerjoin(ReviewRow, ReviewRow.analysis_id == AnalysisRow.id)
            .outerjoin(ExtractionRunRow, ExtractionRunRow.id == latest_run)
            .outerjoin(selected_run, selected_execution_join(selected_run))
            .outerjoin(ConfirmedEventRow, ConfirmedEventRow.review_id == ReviewRow.id)
            .order_by(ContractRow.id, ConfirmedEventRow.kind)
        )
        try:
            with Session(self.engine) as session:
                rows = session.execute(query).mappings().all()
        except OperationalError as exc:
            code = getattr(exc.orig, "sqlite_errorcode", 0) & 0xFF
            logger.warning("operation=portfolio_read outcome=failed sqlite_code=%d", code)
            if code in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED):
                raise StorageBusyError(
                    "O banco está ocupado. Aguarde e atualize a agenda."
                ) from exc
            raise RadarError(
                "Não foi possível consultar a carteira. Nenhuma cobertura foi calculada; "
                "verifique o banco e atualize a agenda."
            ) from exc
        grouped = {}
        for row in rows:
            grouped.setdefault(row["contract_id"], []).append(row)
        contracts, events = [], []
        kernel = method_kernel()
        for contract_id, group in grouped.items():
            row = group[0]
            event_rows = [item for item in group if item["event_id"] is not None]
            state, detail = coverage_for(
                known_amendment=row["known_amendment"],
                has_documents=bool(row["document_count"]),
                has_analysis=row["analysis_id"] is not None,
                blocked=bool(row["blocked"]),
                current_rule=row["rule_version"] == rules.RULE_VERSION
                and method_is_current(
                    row["method_version"],
                    row["analysis_execution_status"],
                    row["analysis_execution_method"],
                    kernel=kernel,
                ),
                reviewed=row["review_id"] is not None,
                candidate_count=row["candidate_count"] or 0,
                event_count=len(event_rows),
                execution_status=row["execution_status"],
                execution_blocked=bool(row["execution_blocked"]),
            )
            contracts.append(PortfolioContract(contract_id, row["title"], state, detail))
            if state != CoverageState.WITH_EVENTS:
                continue
            for item in event_rows:
                events.append(
                    AgendaEvent(
                        item["event_id"],
                        contract_id,
                        row["title"],
                        item["kind"],
                        date.fromisoformat(item["event_date"]),
                        row["document_version"],
                        row["analysis_id"],
                        row["analysis_version"],
                        row["review_id"],
                        row["reviewer"],
                        row["reviewed_at_utc"],
                    )
                )
        contracts.sort(key=lambda item: (item.title.casefold(), item.id))
        logger.info(
            "operation=portfolio_read contracts=%d events=%d duration_ms=%.2f",
            len(contracts),
            len(events),
            (perf_counter() - started) * 1000,
        )
        return PortfolioSnapshot(tuple(contracts), tuple(events))
