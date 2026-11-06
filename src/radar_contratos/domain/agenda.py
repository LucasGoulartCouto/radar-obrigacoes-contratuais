"""Projeção da carteira e filtros temporais, sem alterar confirmações."""

from collections import Counter
from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from radar_contratos.domain.dates import TemporalStatus, classify_date
from radar_contratos.errors import ValidationError

EVENT_LABELS = {"non_renewal_notice": "Aviso de não renovação", "termination": "Término do ciclo"}


class CoverageState(StrEnum):
    WAITING_ANALYSIS = "Aguardando análise"
    WAITING_DOCUMENTS = "Aguardando análise"  # subtipo de pendência, mesmo grupo da SPEC
    FAILED = "Falha de análise"
    PENDING_REVIEW = "Revisão pendente"
    BLOCKED = "Bloqueado"
    WITH_EVENTS = "Conferido com eventos"
    WITHOUT_EVENTS = "Conferido sem eventos no recorte"


@dataclass(frozen=True, slots=True)
class PortfolioContract:
    id: str
    title: str
    state: CoverageState
    detail: str


@dataclass(frozen=True, slots=True)
class AgendaEvent:
    id: str
    contract_id: str
    contract_title: str
    kind: str
    event_date: date
    document_version: int
    analysis_id: str
    analysis_version: int
    review_id: str
    reviewer: str
    reviewed_at_utc: str


@dataclass(frozen=True, slots=True)
class PortfolioSnapshot:
    contracts: tuple[PortfolioContract, ...]
    events: tuple[AgendaEvent, ...]


@dataclass(frozen=True, slots=True)
class AgendaItem:
    event: AgendaEvent
    temporal_status: TemporalStatus
    days_until: int


@dataclass(frozen=True, slots=True)
class AgendaView:
    portfolio: PortfolioSnapshot
    reference_date: date
    items: tuple[AgendaItem, ...]
    coverage: tuple[tuple[CoverageState, int], ...]


def coverage_for(
    *,
    known_amendment: bool,
    has_documents: bool,
    has_analysis: bool,
    blocked: bool,
    current_rule: bool,
    reviewed: bool,
    candidate_count: int,
    event_count: int,
    execution_status: str | None = None,
    execution_blocked: bool = False,
) -> tuple[CoverageState, str]:
    if known_amendment:
        return CoverageState.BLOCKED, "Aditivo declarado no histórico; efeitos não consolidados."
    if blocked:
        return CoverageState.BLOCKED, "Impedimento registrado no levantamento; resolva a pendência."
    if not has_documents:
        return CoverageState.WAITING_DOCUMENTS, "Receba os documentos sintéticos do contrato."
    if not has_analysis:
        if execution_blocked:
            return CoverageState.BLOCKED, "A análise encontrou impedimentos; consulte a tentativa."
        if execution_status in {"failed", "interrupted"}:
            return (
                CoverageState.FAILED,
                "A tentativa não foi concluída; inicie nova tentativa explícita.",
            )
        if execution_status == "completed":
            return (
                CoverageState.PENDING_REVIEW,
                "Selecione a análise concluída e confira o resultado.",
            )
        return CoverageState.WAITING_ANALYSIS, "Registre um levantamento da revisão atual."
    if not current_rule:
        return (
            CoverageState.PENDING_REVIEW,
            "O método ou a regra mudou; refaça o levantamento e a conferência.",
        )
    if not reviewed:
        return CoverageState.PENDING_REVIEW, "Confira os campos e as evidências da base atual."
    if candidate_count != event_count:
        return (
            CoverageState.PENDING_REVIEW,
            "Conferência inconsistente; revise os dados antes de usar.",
        )
    if event_count:
        return CoverageState.WITH_EVENTS, "Conferência válida para a base e a regra atuais."
    return CoverageState.WITHOUT_EVENTS, "Ausência de eventos do recorte conferida explicitamente."


def build_agenda(
    portfolio: PortfolioSnapshot,
    reference_date: date,
    *,
    statuses: tuple[TemporalStatus, ...] = tuple(TemporalStatus),
    kinds: tuple[str, ...] = tuple(EVENT_LABELS),
) -> AgendaView:
    if type(reference_date) is not date:
        raise ValidationError("Informe uma data de referência da simulação, sem horário.")
    if any(not isinstance(value, TemporalStatus) for value in statuses):
        raise ValidationError("Escolha situações de prazo válidas.")
    if any(value not in EVENT_LABELS for value in kinds):
        raise ValidationError("Escolha tipos de evento válidos.")
    items = []
    for event in portfolio.events:
        status = classify_date(event.event_date, reference_date)
        if status in statuses and event.kind in kinds:
            items.append(AgendaItem(event, status, (event.event_date - reference_date).days))
    items.sort(
        key=lambda item: (
            item.event.event_date,
            item.event.contract_title.casefold(),
            item.event.contract_id,
            item.event.kind,
            item.event.id,
        )
    )
    return AgendaView(
        portfolio,
        reference_date,
        tuple(items),
        summarize_coverage(portfolio),
    )


def summarize_coverage(portfolio: PortfolioSnapshot) -> tuple[tuple[CoverageState, int], ...]:
    counts = Counter(contract.state for contract in portfolio.contracts)
    return tuple((state, counts[state]) for state in CoverageState)
