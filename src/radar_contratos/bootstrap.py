"""Ligação dos módulos concretos, sem estado de negócio na interface."""

from sqlalchemy import Engine

from radar_contratos.application.agenda import AgendaService
from radar_contratos.application.contracts import ContractService
from radar_contratos.application.documents import DocumentService
from radar_contratos.application.reviews import ReviewService
from radar_contratos.config import Settings
from radar_contratos.infrastructure.persistence.agenda import SqliteAgendaStore
from radar_contratos.infrastructure.persistence.contracts import SqliteContractStore
from radar_contratos.infrastructure.persistence.database import make_engine, require_current_schema
from radar_contratos.infrastructure.persistence.documents import SqliteDocumentStore
from radar_contratos.infrastructure.persistence.reviews import SqliteReviewStore


def build_service(settings: Settings) -> tuple[ContractService, Engine]:
    engine = make_engine(settings.database_path)
    try:
        require_current_schema(engine)
    except Exception:
        engine.dispose()
        raise
    return ContractService(SqliteContractStore(engine)), engine


def build_document_service(settings: Settings, engine: Engine) -> DocumentService:
    return DocumentService(SqliteDocumentStore(engine), settings.document_limits)


def build_review_service(engine: Engine) -> ReviewService:
    return ReviewService(SqliteReviewStore(engine))


def build_agenda_service(engine: Engine) -> AgendaService:
    return AgendaService(SqliteAgendaStore(engine))
