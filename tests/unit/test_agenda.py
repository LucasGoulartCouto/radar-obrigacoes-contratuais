from datetime import date, datetime

import pytest

from radar_contratos.domain.agenda import (
    AgendaEvent,
    CoverageState,
    PortfolioContract,
    PortfolioSnapshot,
    build_agenda,
    coverage_for,
)
from radar_contratos.domain.dates import TemporalStatus
from radar_contratos.errors import ValidationError


def event(day, *, identifier="e1", kind="termination", contract_id="c1", title="Contrato"):
    return AgendaEvent(identifier, contract_id, title, kind, day, 1, "a1", 1, "r1", "Marina", "UTC")


def portfolio(events=()):
    return PortfolioSnapshot(
        tuple(
            PortfolioContract(str(i), state.value, state, "Detalhe")
            for i, state in enumerate(CoverageState)
        ),
        tuple(events),
    )


@pytest.mark.parametrize(
    ("day", "expected", "days"),
    [
        (date(2027, 4, 30), TemporalStatus.PAST, -1),
        (date(2027, 5, 1), TemporalStatus.TODAY, 0),
        (date(2027, 5, 31), TemporalStatus.SOON, 30),
        (date(2027, 6, 1), TemporalStatus.LATER, 31),
    ],
)
def test_agenda_classifies_spec_boundaries_without_losing_past_events(day, expected, days):
    view = build_agenda(portfolio([event(day)]), date(2027, 5, 1))
    assert view.items[0].temporal_status == expected
    assert view.items[0].days_until == days


def test_temporal_and_kind_filters_do_not_change_portfolio_coverage():
    snapshot = portfolio(
        [
            event(date(2027, 5, 31), kind="non_renewal_notice"),
            event(date(2027, 6, 30), identifier="e2"),
        ]
    )
    view = build_agenda(
        snapshot, date(2027, 5, 1), statuses=(TemporalStatus.SOON,), kinds=("non_renewal_notice",)
    )
    assert [item.event.kind for item in view.items] == ["non_renewal_notice"]
    assert dict(view.coverage) == dict.fromkeys(CoverageState, 1)
    assert sum(count for _, count in view.coverage) == len(snapshot.contracts) == 6
    assert len(view.portfolio.events) == 2


@pytest.mark.parametrize("filters", [{"statuses": ()}, {"kinds": ()}])
def test_empty_filter_returns_no_events_without_treating_portfolio_as_reviewed(filters):
    view = build_agenda(portfolio([event(date(2027, 5, 1))]), date(2027, 5, 1), **filters)
    assert view.items == ()
    assert dict(view.coverage)[CoverageState.PENDING_REVIEW] == 1


def test_date_order_ties_and_two_kinds_on_same_date_are_deterministic():
    day = date(2027, 5, 1)
    events = [
        event(day, identifier="b", title="Zulu"),
        event(day, identifier="a", kind="termination", title="Alfa"),
        event(day, identifier="c", kind="non_renewal_notice", title="Alfa"),
        event(date(2027, 4, 30), identifier="d"),
    ]
    view = build_agenda(portfolio(events), day)
    assert [item.event.id for item in view.items] == ["d", "c", "a", "b"]


def test_reference_changes_only_the_view_and_supports_date_extremes():
    snapshot = portfolio([event(date.max)])
    first = build_agenda(snapshot, date.min)
    second = build_agenda(snapshot, date.max)
    assert first.items[0].temporal_status == TemporalStatus.LATER
    assert second.items[0].temporal_status == TemporalStatus.TODAY
    assert first.portfolio is second.portfolio is snapshot
    assert first.items[0].event == snapshot.events[0]


@pytest.mark.parametrize("reference", [None, "2027-05-01", datetime(2027, 5, 1)])
def test_reference_requires_date_without_time(reference):
    with pytest.raises(ValidationError):
        build_agenda(portfolio(), reference)


@pytest.mark.parametrize("filters", [{"statuses": ("Hoje",)}, {"kinds": ("payment",)}])
def test_unsupported_filter_is_rejected(filters):
    with pytest.raises(ValidationError):
        build_agenda(portfolio(), date(2027, 5, 1), **filters)


FACTS = dict(
    known_amendment=False,
    has_documents=True,
    has_analysis=True,
    blocked=False,
    current_rule=True,
    reviewed=True,
    candidate_count=2,
    event_count=2,
)


@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        ({"known_amendment": True, "has_documents": False}, CoverageState.BLOCKED),
        ({"blocked": True, "current_rule": False}, CoverageState.BLOCKED),
        ({"has_documents": False, "has_analysis": False}, CoverageState.WAITING_DOCUMENTS),
        ({"has_analysis": False}, CoverageState.WAITING_ANALYSIS),
        ({"current_rule": False}, CoverageState.PENDING_REVIEW),
        ({"reviewed": False}, CoverageState.PENDING_REVIEW),
        ({"event_count": 1}, CoverageState.PENDING_REVIEW),
        ({}, CoverageState.WITH_EVENTS),
        ({"candidate_count": 0, "event_count": 0}, CoverageState.WITHOUT_EVENTS),
    ],
)
def test_coverage_is_exclusive_and_blocks_incomplete_confirmation(changes, expected):
    state, detail = coverage_for(**(FACTS | changes))
    assert state is expected
    assert detail


def test_empty_portfolio_has_all_zero_counts():
    view = build_agenda(PortfolioSnapshot((), ()), date(2027, 5, 1))
    assert view.items == ()
    assert all(count == 0 for _, count in view.coverage)
