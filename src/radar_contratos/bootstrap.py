"""Ligação dos módulos concretos, sem estado de negócio na interface."""

from sqlalchemy import Engine

from radar_contratos.application.agenda import AgendaService
from radar_contratos.application.contracts import ContractService
from radar_contratos.application.documents import DocumentService
from radar_contratos.application.extractions import ExtractionService
from radar_contratos.application.reviews import ReviewService
from radar_contratos.config import Settings
from radar_contratos.infrastructure.local_classifier import OllamaLineClassifier, method_kernel
from radar_contratos.infrastructure.persistence.agenda import SqliteAgendaStore
from radar_contratos.infrastructure.persistence.contracts import SqliteContractStore
from radar_contratos.infrastructure.persistence.database import make_engine, require_current_schema
from radar_contratos.infrastructure.persistence.documents import SqliteDocumentStore
from radar_contratos.infrastructure.persistence.extractions import SqliteExtractionStore
from radar_contratos.infrastructure.persistence.read_errors import read_error
from radar_contratos.infrastructure.persistence.reviews import SqliteReviewStore


def build_service(settings: Settings) -> tuple[ContractService, Engine]:
    try:
        engine = make_engine(settings.database_path, create_if_missing=False)
    except OSError as exc:
        raise read_error(
            exc,
            operation="database_open",
            message="Não foi possível acessar o armazenamento local. Verifique o acesso "
            "e a preparação do ambiente antes de tentar novamente.",
        ) from exc
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


def build_extraction_service(settings: Settings, engine: Engine) -> ExtractionService:
    try:
        classifier = (
            OllamaLineClassifier(settings.local_model_digest)
            if settings.local_model_digest
            else None
        )
    except ValueError:
        classifier = None
    return ExtractionService(SqliteExtractionStore(engine), classifier, method_kernel())
