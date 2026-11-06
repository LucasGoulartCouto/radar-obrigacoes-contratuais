"""Cada teste usa seu próprio banco temporário em arquivo."""

import pytest

from radar_contratos.application.contracts import ContractService
from radar_contratos.application.extractions import ExtractionService
from radar_contratos.domain.assisted import literal_lines
from radar_contratos.infrastructure.local_classifier import OllamaLineClassifier, method_kernel
from radar_contratos.infrastructure.persistence.contracts import SqliteContractStore
from radar_contratos.infrastructure.persistence.database import initialize_database, make_engine
from radar_contratos.infrastructure.persistence.extractions import SqliteExtractionStore


@pytest.fixture
def engine(tmp_path):
    database_engine = make_engine(tmp_path / "radar.sqlite3")
    initialize_database(database_engine)
    yield database_engine
    database_engine.dispose()


@pytest.fixture
def service(engine):
    return ContractService(SqliteContractStore(engine))


class SimulatedClassifier:
    """Substitui somente a inferência, mantendo entrada e persistência reais nos testes."""

    def __init__(self):
        self.calls = 0
        self.failure = False
        self.abstained = False
        self.hook = None
        self.labels = None

    def descriptor(self):
        return {"kernel": method_kernel(), "model": "simulated-test", "digest": "a" * 64}

    def validate_input(self, documents):
        OllamaLineClassifier("a" * 64).validate_input(documents)

    def classify(self, documents):
        self.calls += 1
        if self.hook:
            self.hook()
        if self.failure:
            raise RuntimeError("Texto documental não deve aparecer em logs de falha.")
        labels = {}
        for line in literal_lines(documents):
            if not line.text.strip():
                continue
            lower = line.text.casefold()
            if lower.startswith("instrução ao assistente:"):
                kind = "unsupported"
            elif "exemplo" in lower:
                kind = "illustrative"
            elif lower.startswith("não há"):
                kind = "no_event"
            elif "aditivo" in lower:
                kind = "amendment"
            elif "término do ciclo" in lower or "vigência efetiva" in lower:
                kind = "termination"
            elif "dias" in lower:
                kind = "notice"
            else:
                kind = "context"
            labels[line.alias] = kind
        return {
            "classifications": self.labels if self.labels is not None else labels,
            "abstained": self.abstained,
            "runtime_version": "simulated",
        }


@pytest.fixture
def classifier():
    return SimulatedClassifier()


@pytest.fixture
def extractions(engine, classifier):
    return ExtractionService(SqliteExtractionStore(engine), classifier, method_kernel())
