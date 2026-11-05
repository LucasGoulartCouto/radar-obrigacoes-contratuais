"""Registro manual e conferência, separados da interface e do mecanismo do banco."""

from radar_contratos.application.inputs import fingerprint, text
from radar_contratos.application.inputs import request_id as valid_id
from radar_contratos.application.ports import ReviewStore
from radar_contratos.domain.reviews import (
    AnalysisSnapshot,
    AnalysisSummary,
    ManualDraft,
    draft_payload,
)
from radar_contratos.errors import ValidationError


def _versions(document_version: int, analysis_version: int) -> None:
    if (
        type(document_version) is not int
        or document_version < 1
        or type(analysis_version) is not int
        or analysis_version < 0
    ):
        raise ValidationError("A base exibida é inválida. Receba documentos e atualize a tela.")


class ReviewService:
    def __init__(self, store: ReviewStore) -> None:
        self.store = store

    def register(
        self,
        *,
        contract_id: str,
        expected_document_version: int,
        expected_analysis_version: int,
        draft: ManualDraft,
        actor: str,
        request_id: str,
        synthetic: bool,
        change_reason: str = "",
    ) -> dict:
        if synthetic is not True:
            raise ValidationError("Confirme o uso exclusivo dos documentos sintéticos do case.")
        _versions(expected_document_version, expected_analysis_version)
        contract_id, request_id = valid_id(contract_id), valid_id(request_id)
        actor = text(actor, label="Responsável pelo levantamento", maximum=80)
        if not isinstance(change_reason, str):
            raise ValidationError("Informe o motivo da correção como texto.")
        if change_reason:
            change_reason = text(change_reason, label="Motivo da correção", maximum=500)
        payload = {
            "operation": "manual_analysis",
            "contract_id": contract_id,
            "document_version": expected_document_version,
            "analysis_version": expected_analysis_version,
            "draft": draft_payload(draft),
            "change_reason": change_reason,
            "actor": actor,
        }
        return self.store.register(
            contract_id=contract_id,
            expected_document_version=expected_document_version,
            expected_analysis_version=expected_analysis_version,
            draft=draft,
            change_reason=change_reason,
            actor=actor,
            request_id=request_id,
            fingerprint=fingerprint(payload),
        )

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
        acknowledged: bool,
        empty_acknowledged: bool = False,
    ) -> dict:
        if acknowledged is not True:
            raise ValidationError(
                "Confira os campos, as evidências e a cobertura antes de confirmar."
            )
        if type(empty_acknowledged) is not bool:
            raise ValidationError("A declaração de conferência do vazio é inválida.")
        _versions(expected_document_version, expected_analysis_version)
        contract_id, analysis_id, request_id = (
            valid_id(contract_id),
            valid_id(analysis_id),
            valid_id(request_id),
        )
        actor = text(actor, label="Responsável pela conferência", maximum=80)
        payload = {
            "operation": "confirm_analysis",
            "contract_id": contract_id,
            "analysis_id": analysis_id,
            "document_version": expected_document_version,
            "analysis_version": expected_analysis_version,
            "rule": expected_rule_version,
            "actor": actor,
            "empty_acknowledged": empty_acknowledged,
        }
        return self.store.confirm(
            contract_id=contract_id,
            analysis_id=analysis_id,
            expected_document_version=expected_document_version,
            expected_analysis_version=expected_analysis_version,
            expected_rule_version=expected_rule_version,
            actor=actor,
            request_id=request_id,
            fingerprint=fingerprint(payload),
            empty_acknowledged=empty_acknowledged,
        )

    def get_analysis(
        self, contract_id: str, analysis_id: str | None = None
    ) -> AnalysisSnapshot | None:
        return self.store.get_analysis(
            valid_id(contract_id), valid_id(analysis_id) if analysis_id else None
        )

    def list_history(self, contract_id: str) -> list[AnalysisSummary]:
        return self.store.list_history(valid_id(contract_id))

    def current_states(self) -> dict[str, str]:
        return self.store.current_states()

    def current_events(self, contract_id: str) -> list[dict]:
        return self.store.current_events(valid_id(contract_id))
