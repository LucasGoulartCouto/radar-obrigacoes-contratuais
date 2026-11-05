"""Consulta de agenda em uma fotografia consistente da carteira."""

from datetime import date

from radar_contratos.application.ports import AgendaStore
from radar_contratos.domain.agenda import EVENT_LABELS, AgendaView, PortfolioSnapshot, build_agenda
from radar_contratos.domain.dates import TemporalStatus


class AgendaService:
    def __init__(self, store: AgendaStore) -> None:
        self.store = store

    def read_portfolio(self) -> PortfolioSnapshot:
        return self.store.read_portfolio()

    def read(
        self,
        reference_date: date,
        *,
        statuses: tuple[TemporalStatus, ...] = tuple(TemporalStatus),
        kinds: tuple[str, ...] = tuple(EVENT_LABELS),
    ) -> AgendaView:
        return build_agenda(
            self.store.read_portfolio(), reference_date, statuses=statuses, kinds=kinds
        )
