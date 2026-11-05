from pathlib import Path
from uuid import uuid4

from streamlit.testing.v1 import AppTest

from radar_contratos.application.documents import DocumentService
from radar_contratos.domain.documents import DocumentInput, DocumentRole
from radar_contratos.infrastructure.persistence.documents import SqliteDocumentStore

APP_PATH = Path(__file__).parents[2] / "src/radar_contratos/ui/app.py"


def seed(service, engine, role=DocumentRole.BASE):
    contract = service.register(title="Case documental", actor="Rafael", request_id=str(uuid4()))
    documents = DocumentService(SqliteDocumentStore(engine))
    documents.submit(
        contract_id=contract.id,
        documents=(DocumentInput("base.txt", b"Texto do case", role),),
        expected_version=0,
        actor="Rafael",
        request_id=str(uuid4()),
        synthetic=True,
    )
    return contract, documents


def test_saved_documents_and_amendment_warning_survive_ui_reruns(
    engine,
    service,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv("RADAR_DATA_DIR", str(tmp_path))
    contract, documents = seed(service, engine, DocumentRole.AMENDMENT)
    app = AppTest.from_file(str(APP_PATH), default_timeout=30).run()
    assert not app.exception
    assert any("aditivo declarado no histórico" in warning.value for warning in app.warning)
    assert app.metric[0].value == "0"
    app.run()
    assert not app.exception
    assert len(documents.list_revisions(contract.id)) == 1


def test_stale_document_form_requires_refresh_before_another_attempt(
    engine,
    service,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv("RADAR_DATA_DIR", str(tmp_path))
    contract, documents = seed(service, engine)
    app = AppTest.from_file(str(APP_PATH), default_timeout=30).run()
    documents.submit(
        contract_id=contract.id,
        documents=(DocumentInput("mudou.txt", b"Outra base", DocumentRole.BASE),),
        expected_version=1,
        actor="Marina",
        request_id=str(uuid4()),
        synthetic=True,
    )
    next(item for item in app.checkbox if item.label.startswith("Os documentos enviados")).check()
    next(item for item in app.button if item.label == "Salvar conjunto documental").click().run()
    assert not app.exception
    assert any("mudaram em outro envio" in item.value for item in app.error)
    assert not any(item.label == "Salvar conjunto documental" for item in app.button)
    app.run()
    assert any("mudaram em outro envio" in item.value for item in app.error)
    assert len(documents.list_revisions(contract.id)) == 2
    next(item for item in app.button if item.label == "Atualizar documentos").click().run()
    assert not app.exception
    assert not app.error


def test_empty_revision_is_visible_as_waiting_documents(engine, service, tmp_path, monkeypatch):
    monkeypatch.setenv("RADAR_DATA_DIR", str(tmp_path))
    contract, documents = seed(service, engine)
    documents.submit(
        contract_id=contract.id,
        documents=(),
        expected_version=1,
        actor="Rafael",
        request_id=str(uuid4()),
        synthetic=True,
        allow_empty=True,
    )
    app = AppTest.from_file(str(APP_PATH), default_timeout=30).run()
    assert not app.exception
    assert app.metric[0].value == "1"
    assert any("Conjunto vazio" in item.value for item in app.info)
