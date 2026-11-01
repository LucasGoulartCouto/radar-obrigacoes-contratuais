from pathlib import Path
from uuid import uuid4

from streamlit.testing.v1 import AppTest

from radar_contratos.application.contracts import ContractService
from radar_contratos.infrastructure.persistence.contracts import SqliteContractStore

APP_PATH = Path(__file__).parents[2] / "src/radar_contratos/ui/app.py"


def test_form_persists_and_reruns_do_not_duplicate(engine, tmp_path, monkeypatch):
    monkeypatch.setenv("RADAR_DATA_DIR", str(tmp_path))
    app = AppTest.from_file(str(APP_PATH), default_timeout=30).run()
    assert not app.exception
    app.text_input[0].set_value("Fornecedor fictício de criação")
    app.checkbox[0].check()
    app.button[0].click().run()
    assert not app.exception
    assert app.metric[0].value == "1"
    app.run()
    assert app.metric[0].value == "1"
    reopened = AppTest.from_file(str(APP_PATH), default_timeout=30).run()
    assert reopened.metric[0].value == "1"
    assert len(ContractService(SqliteContractStore(engine)).list_contracts()) == 1


def test_form_requires_acknowledgment_of_fictional_case(engine, tmp_path, monkeypatch):
    monkeypatch.setenv("RADAR_DATA_DIR", str(tmp_path))
    app = AppTest.from_file(str(APP_PATH), default_timeout=30).run()
    app.text_input[0].set_value("Fornecedor fictício")
    app.button[0].click().run()
    assert not app.exception
    assert app.warning
    assert app.metric[0].value == "0"


def test_uninitialized_database_is_presented_as_actionable_error(tmp_path, monkeypatch):
    monkeypatch.setenv("RADAR_DATA_DIR", str(tmp_path))
    app = AppTest.from_file(str(APP_PATH), default_timeout=30).run()
    assert not app.exception
    assert app.error


def test_stale_form_cannot_overwrite_another_edit(engine, tmp_path, monkeypatch):
    monkeypatch.setenv("RADAR_DATA_DIR", str(tmp_path))
    service = ContractService(SqliteContractStore(engine))
    original = service.register(title="Serviço fictício", actor="Rafael", request_id=str(uuid4()))
    app = AppTest.from_file(str(APP_PATH), default_timeout=30).run()
    service.rename(
        contract_id=original.id,
        title="Nome atualizado por Marina",
        expected_version=1,
        actor="Marina",
        request_id=str(uuid4()),
    )
    name_input = next(
        widget for widget in app.text_input if widget.label == "Novo nome do contrato"
    )
    name_input.set_value("Edição com tela antiga")
    save = next(button for button in app.button if button.label == "Salvar nome")
    save.click().run()
    assert not app.exception
    assert app.error
    assert service.list_contracts()[0].title == "Nome atualizado por Marina"
