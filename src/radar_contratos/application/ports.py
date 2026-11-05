"""Fronteira de persistência para o cadastro inicial."""

from typing import Protocol

from radar_contratos.domain.agenda import PortfolioSnapshot
from radar_contratos.domain.contracts import Contract
from radar_contratos.domain.documents import DocumentRevision, PreparedDocument, SubmissionReceipt
from radar_contratos.domain.reviews import AnalysisSnapshot, AnalysisSummary, ManualDraft


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


class AgendaStore(Protocol):
    def read_portfolio(self) -> PortfolioSnapshot: ...


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


class ReviewStore(Protocol):
    def register(
        self,
        *,
        contract_id: str,
        expected_document_version: int,
        expected_analysis_version: int,
        actor: str,
        request_id: str,
        fingerprint: str,
        draft: ManualDraft,
        change_reason: str,
    ) -> dict: ...

    def confirm(
        self,
        *,
        contract_id: str,
        analysis_id: str,
        expected_document_version: int,
        expected_analysis_version: int,
        expected_rule_version: str,
        actor: str,
        request_id: str,
        fingerprint: str,
        empty_acknowledged: bool,
    ) -> dict: ...

    def get_analysis(
        self, contract_id: str, analysis_id: str | None = None
    ) -> AnalysisSnapshot | None: ...

    def list_history(self, contract_id: str) -> list[AnalysisSummary]: ...

    def current_states(self) -> dict[str, str]: ...

    def current_events(self, contract_id: str) -> list[dict]: ...
