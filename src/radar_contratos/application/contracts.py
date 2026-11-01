"""Validação das operações, sem importar a interface ou o mecanismo do banco."""

import hashlib
import json
from uuid import UUID

from radar_contratos.application.ports import ContractStore
from radar_contratos.domain.contracts import Contract
from radar_contratos.errors import ValidationError


def _text(value: str, *, label: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"{label}: informe um texto.")
    value = value.strip()
    if not value or len(value) > maximum or any(ord(char) < 32 for char in value):
        raise ValidationError(
            f"{label}: informe entre 1 e {maximum} caracteres, sem quebras de linha."
        )
    return value


def _request_id(value: str) -> str:
    try:
        return str(UUID(value))
    except (ValueError, AttributeError, TypeError) as exc:
        raise ValidationError("A identificação da operação é inválida. Atualize a tela.") from exc


def _fingerprint(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


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
