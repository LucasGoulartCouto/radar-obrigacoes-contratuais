"""Levantamento manual com evidências; não interpreta cláusulas nem confirma resultados."""

from dataclasses import asdict, dataclass
from datetime import date

from radar_contratos.domain.dates import calculate_notice_date
from radar_contratos.domain.documents import NORMALIZATION_VERSION
from radar_contratos.errors import ValidationError

RULE_VERSION = "AVISO_CORRIDOS_V1"
METHOD_VERSION = "MANUAL_V1"


def current_method(version: str) -> bool:
    from radar_contratos.domain.assisted import METHOD_VERSION as assisted_method

    return version in {METHOD_VERSION, assisted_method}


@dataclass(frozen=True, slots=True)
class EvidenceInput:
    document_position: int
    start_line: int
    end_line: int
    quote: str


@dataclass(frozen=True, slots=True)
class ReferenceDocument:
    id: str
    position: int
    reference_text: str
    reference_sha256: str
    normalization_version: str
    role: str = "base"


@dataclass(frozen=True, slots=True)
class ManualDraft:
    mode: str = "events"
    end_date: date | None = None
    end_evidence: EvidenceInput | None = None
    notice_days: int | None = None
    notice_evidence: EvidenceInput | None = None
    notice_unit: str = "calendar_days"
    notice_anchor: str = "end_date"
    blocker_reason: str = ""
    blocker_evidence: EvidenceInput | None = None


def draft_payload(draft: ManualDraft) -> dict:
    if not isinstance(draft, ManualDraft):
        raise ValidationError("Informe um levantamento manual válido.")
    if draft.end_date is not None and type(draft.end_date) is not date:
        raise ValidationError("Informe uma data de término sem horário.")
    result = asdict(draft)
    result["end_date"] = draft.end_date.isoformat() if draft.end_date else None
    return result


def locate_evidence(evidence: EvidenceInput, documents: tuple[ReferenceDocument, ...]) -> dict:
    if not isinstance(evidence, EvidenceInput):
        raise ValidationError("Cada campo precisa de uma evidência localizada.")
    if type(evidence.document_position) is not int:
        raise ValidationError("A referência do documento é inválida.")
    document = next(
        (item for item in documents if item.position == evidence.document_position), None
    )
    if document is None or document.normalization_version != NORMALIZATION_VERSION:
        raise ValidationError("A evidência não pertence ao texto de referência desta revisão.")
    lines = document.reference_text.split("\n")
    start, end = evidence.start_line, evidence.end_line
    if type(start) is not int or type(end) is not int or not 1 <= start <= end <= len(lines):
        raise ValidationError("O intervalo de linhas da evidência é inválido.")
    quote = "\n".join(lines[start - 1 : end])
    if not isinstance(evidence.quote, str) or not quote.strip() or evidence.quote != quote:
        raise ValidationError("A citação deve corresponder literalmente às linhas do documento.")
    return {
        "document_id": document.id,
        "document_position": document.position,
        "start_line": start,
        "end_line": end,
        "quote": quote,
        "reference_sha256": document.reference_sha256,
        "normalization_version": document.normalization_version,
    }


def prepare_manual_analysis(
    draft: ManualDraft,
    documents: tuple[ReferenceDocument, ...],
    *,
    known_amendment: bool = False,
) -> dict:
    payload = draft_payload(draft)
    if not isinstance(draft.mode, str) or draft.mode not in {"events", "empty", "blocked"}:
        raise ValidationError("Escolha o resultado do levantamento manual.")
    evidence, candidates, blockers = {}, [], []
    if draft.mode == "events":
        if draft.end_date is None:
            raise ValidationError("Informe o término explícito ou registre o impedimento.")
        if draft.blocker_reason or draft.blocker_evidence is not None:
            raise ValidationError("Registre impedimentos no modo correspondente.")
        evidence["end_date"] = locate_evidence(draft.end_evidence, documents)
        candidates.append({"kind": "termination", "date": draft.end_date.isoformat()})
        if draft.notice_days is not None:
            if type(draft.notice_days) is not int or draft.notice_days < 0:
                raise ValidationError("A antecedência deve ser um inteiro não negativo.")
            evidence["notice_rule"] = locate_evidence(draft.notice_evidence, documents)
            if not isinstance(draft.notice_unit, str) or draft.notice_unit not in {
                "calendar_days",
                "undefined",
                "other",
            }:
                raise ValidationError("A unidade informada é inválida.")
            if not isinstance(draft.notice_anchor, str) or draft.notice_anchor not in {
                "end_date",
                "unknown",
                "other",
            }:
                raise ValidationError("A referência do prazo é inválida.")
            if draft.notice_unit != "calendar_days":
                blockers.append("Unidade de dias corridos não está explicitamente definida.")
            if draft.notice_anchor != "end_date":
                blockers.append("Prazo não está ligado a um término explícito suportado.")
            if not blockers:
                notice = calculate_notice_date(draft.end_date, draft.notice_days)
                candidates.append({"kind": "non_renewal_notice", "date": notice.isoformat()})
        elif draft.notice_evidence is not None:
            raise ValidationError("Informe a antecedência ou registre o impedimento.")
        elif draft.notice_unit != "calendar_days" or draft.notice_anchor != "end_date":
            raise ValidationError("Uma regra de aviso exige antecedência e evidência.")
    else:
        if draft.notice_unit != "calendar_days" or draft.notice_anchor != "end_date":
            raise ValidationError("Este modo não aceita uma regra de aviso.")
        if any(
            value is not None
            for value in (
                draft.end_date,
                draft.end_evidence,
                draft.notice_days,
                draft.notice_evidence,
            )
        ):
            raise ValidationError("O modo sem eventos ou bloqueado não aceita campos de marcos.")
        if draft.mode == "blocked":
            if (
                not isinstance(draft.blocker_reason, str)
                or not draft.blocker_reason.strip()
                or len(draft.blocker_reason) > 500
                or any(ord(char) < 32 for char in draft.blocker_reason)
            ):
                raise ValidationError("Descreva o impedimento em até 500 caracteres, sem quebras.")
            evidence["blocker"] = locate_evidence(draft.blocker_evidence, documents)
            blockers.append(draft.blocker_reason.strip())
        elif draft.blocker_reason or draft.blocker_evidence is not None:
            raise ValidationError("Registre o impedimento em vez de declarar um resultado vazio.")
    if known_amendment:
        blockers.append("Há aditivo declarado no histórico; consolidação fora deste recorte.")
    if blockers:
        candidates = []
    return {
        "input": payload,
        "evidence": evidence,
        "candidate_events": candidates,
        "blockers": blockers,
        "method_version": METHOD_VERSION,
        "rule_version": RULE_VERSION,
    }


@dataclass(frozen=True, slots=True)
class AnalysisSnapshot:
    id: str
    contract_id: str
    revision_id: str
    document_version: int
    analysis_version: int
    actor: str
    created_at_utc: str
    payload: dict
    is_current: bool
    review_id: str | None
    reviewer: str | None
    reviewed_at_utc: str | None
    change_reason: str = ""


@dataclass(frozen=True, slots=True)
class AnalysisSummary:
    id: str
    number: int
    document_version: int
    is_current: bool
    is_reviewed: bool
