"""Ligação dos módulos concretos, sem estado de negócio na interface."""

from sqlalchemy import Engine

from radar_contratos.application.contracts import ContractService
from radar_contratos.config import Settings
from radar_contratos.infrastructure.persistence.contracts import SqliteContractStore
from radar_contratos.infrastructure.persistence.database import make_engine, require_current_schema


def build_service(settings: Settings) -> tuple[ContractService, Engine]:
    engine = make_engine(settings.database_path)
    try:
        require_current_schema(engine)
    except Exception:
        engine.dispose()
        raise
    return ContractService(SqliteContractStore(engine)), engine
