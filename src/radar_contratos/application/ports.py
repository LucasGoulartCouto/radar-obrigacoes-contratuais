"""Fronteira de persistência para o cadastro inicial."""

from typing import Protocol

from radar_contratos.domain.contracts import Contract
from radar_contratos.domain.documents import DocumentRevision, PreparedDocument, SubmissionReceipt


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


class DocumentStore(Protocol):
    def submit(
        self,
        *,
        contract_id: str,
        expected_version: int,
        actor: str,
        request_id: str,
        fingerprint: str,
        revision_key: str,
        documents: tuple[PreparedDocument, ...],
    ) -> SubmissionReceipt: ...

    def list_revisions(self, contract_id: str) -> list[DocumentRevision]: ...

    def list_submissions(self, contract_id: str, revision_id: str) -> list[SubmissionReceipt]: ...

    def get_documents(
        self, contract_id: str, revision_id: str, request_id: str
    ) -> tuple[PreparedDocument, ...]: ...

    def current_states(self) -> dict[str, str]: ...
