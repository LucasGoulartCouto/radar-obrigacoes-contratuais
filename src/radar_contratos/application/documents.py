"""Casos de uso da entrada documental; nenhuma análise ou confirmação implícita."""

from radar_contratos.application.inputs import fingerprint, text
from radar_contratos.application.inputs import request_id as validate_id
from radar_contratos.application.ports import DocumentStore
from radar_contratos.domain.documents import (
    DocumentInput,
    DocumentLimits,
    DocumentRevision,
    PreparedDocument,
    SubmissionReceipt,
    prepare_documents,
    revision_fingerprint,
)
from radar_contratos.errors import ValidationError


class DocumentService:
    def __init__(self, store: DocumentStore, limits: DocumentLimits | None = None) -> None:
        self.store = store
        self.limits = limits if limits is not None else DocumentLimits()

    def submit(
        self,
        *,
        contract_id: str,
        documents: tuple[DocumentInput, ...],
        expected_version: int,
        actor: str,
        request_id: str,
        synthetic: bool,
        allow_empty: bool = False,
    ) -> SubmissionReceipt:
        if synthetic is not True:
            raise ValidationError("Confirme que os documentos pertencem ao case sintético.")
        if type(expected_version) is not int or expected_version < 0:
            raise ValidationError("A revisão exibida é inválida. Atualize a tela.")
        if not isinstance(documents, tuple):
            raise ValidationError("Informe o conjunto documental completo como uma tupla.")
        if not documents and (allow_empty is not True or expected_version == 0):
            raise ValidationError("Adicione documentos ou confirme a retirada do conjunto atual.")
        actor = text(actor, label="Responsável pelo envio", maximum=80)
        contract_id = validate_id(contract_id)
        request_id = validate_id(request_id)
        prepared = prepare_documents(documents, self.limits)
        payload = {
            "operation": "documents_submit",
            "contract_id": contract_id,
            "expected_version": expected_version,
            "actor": actor,
            "allow_empty": allow_empty,
            "documents": [
                {"filename": item.filename, "role": item.role, "raw_sha256": item.raw_sha256}
                for item in prepared
            ],
        }
        return self.store.submit(
            contract_id=contract_id,
            expected_version=expected_version,
            actor=actor,
            request_id=request_id,
            fingerprint=fingerprint(payload),
            revision_key=revision_fingerprint(prepared),
            documents=prepared,
        )

    def list_revisions(self, contract_id: str) -> list[DocumentRevision]:
        return self.store.list_revisions(validate_id(contract_id))

    def list_submissions(self, contract_id: str, revision_id: str) -> list[SubmissionReceipt]:
        return self.store.list_submissions(validate_id(contract_id), validate_id(revision_id))

    def get_documents(
        self, contract_id: str, revision_id: str, request_id: str
    ) -> tuple[PreparedDocument, ...]:
        return self.store.get_documents(
            validate_id(contract_id), validate_id(revision_id), validate_id(request_id)
        )

    def current_states(self) -> dict[str, str]:
        return self.store.current_states()
