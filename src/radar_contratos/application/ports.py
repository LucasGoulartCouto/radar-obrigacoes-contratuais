"""Fronteira de persistência para o cadastro inicial."""

from typing import Protocol

from radar_contratos.domain.contracts import Contract


class ContractStore(Protocol):
    def list_contracts(self) -> list[Contract]: ...

    def register(
        self, *, title: str, actor: str, request_id: str, fingerprint: str
    ) -> Contract: ...

    def rename(
        self,
        *,
        contract_id: str,
        title: str,
        expected_version: int,
        actor: str,
        request_id: str,
        fingerprint: str,
    ) -> Contract: ...
