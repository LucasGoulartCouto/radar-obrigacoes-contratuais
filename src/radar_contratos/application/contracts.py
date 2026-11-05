"""Validação das operações, sem importar a interface ou o mecanismo do banco."""

from radar_contratos.application.inputs import fingerprint as _fingerprint
from radar_contratos.application.inputs import request_id as _request_id
from radar_contratos.application.inputs import text as _text
from radar_contratos.application.ports import ContractStore
from radar_contratos.domain.contracts import Contract
from radar_contratos.errors import ValidationError


class ContractService:
    def __init__(self, store: ContractStore) -> None:
        self.store = store

    def list_contracts(self) -> list[Contract]:
        return self.store.list_contracts()

    def register(self, *, title: str, actor: str, request_id: str) -> Contract:
        title = _text(title, label="Nome do contrato", maximum=200)
        actor = _text(actor, label="Responsável pelo registro", maximum=80)
        payload = {"operation": "register", "title": title, "actor": actor}
        return self.store.register(
            title=title,
            actor=actor,
            request_id=_request_id(request_id),
            fingerprint=_fingerprint(payload),
        )

    def rename(
        self,
        *,
        contract_id: str,
        title: str,
        expected_version: int,
        actor: str,
        request_id: str,
    ) -> Contract:
        title = _text(title, label="Nome do contrato", maximum=200)
        actor = _text(actor, label="Responsável pelo registro", maximum=80)
        if type(expected_version) is not int or expected_version < 1:
            raise ValidationError("A versão exibida é inválida. Atualize a tela.")
        payload = {
            "operation": "rename",
            "contract_id": contract_id,
            "title": title,
            "expected_version": expected_version,
            "actor": actor,
        }
        return self.store.rename(
            contract_id=contract_id,
            title=title,
            expected_version=expected_version,
            actor=actor,
            request_id=_request_id(request_id),
            fingerprint=_fingerprint(payload),
        )
