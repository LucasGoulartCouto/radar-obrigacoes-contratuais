"""Cada teste usa seu próprio banco temporário em arquivo."""

import pytest

from radar_contratos.application.contracts import ContractService
from radar_contratos.infrastructure.persistence.contracts import SqliteContractStore
from radar_contratos.infrastructure.persistence.database import initialize_database, make_engine


@pytest.fixture
def engine(tmp_path):
    database_engine = make_engine(tmp_path / "radar.sqlite3")
    initialize_database(database_engine)
    yield database_engine
    database_engine.dispose()


@pytest.fixture
def service(engine):
    return ContractService(SqliteContractStore(engine))
