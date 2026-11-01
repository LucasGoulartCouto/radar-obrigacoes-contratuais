from datetime import date, datetime

import pytest

from radar_contratos.domain.dates import TemporalStatus, calculate_notice_date, classify_date
from radar_contratos.errors import ValidationError


@pytest.mark.parametrize(
    ("end_date", "days", "expected"),
    [
        (date(2027, 6, 30), 30, date(2027, 5, 31)),
        (date(2028, 3, 1), 1, date(2028, 2, 29)),
        (date(2027, 3, 1), 1, date(2027, 2, 28)),
        (date(2027, 6, 30), 0, date(2027, 6, 30)),
    ],
)
def test_reference_dates_from_spec(end_date, days, expected):
    assert calculate_notice_date(end_date, days) == expected


@pytest.mark.parametrize("days", [-1, 1.5, True, "30"])
def test_notice_rejects_invalid_number_of_days(days):
    with pytest.raises(ValidationError):
        calculate_notice_date(date(2027, 6, 30), days)


def test_date_underflow_is_reported_as_validation_error():
    with pytest.raises(ValidationError):
        calculate_notice_date(date.min, 1)


def test_datetime_cannot_silently_change_date_only_rule():
    with pytest.raises(ValidationError):
        calculate_notice_date(datetime(2027, 6, 30, 12), 30)


@pytest.mark.parametrize(
    ("event_date", "expected"),
    [
        (date(2027, 4, 30), TemporalStatus.PAST),
        (date(2027, 5, 1), TemporalStatus.TODAY),
        (date(2027, 5, 31), TemporalStatus.SOON),
        (date(2027, 6, 1), TemporalStatus.LATER),
    ],
)
def test_horizon_boundaries_from_spec(event_date, expected):
    assert classify_date(event_date, date(2027, 5, 1)) == expected
