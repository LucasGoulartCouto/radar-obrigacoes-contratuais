"""Convenções aritméticas do case sintético, sem interpretação jurídica."""

from datetime import date, timedelta
from enum import StrEnum

from radar_contratos.errors import ValidationError


class TemporalStatus(StrEnum):
    PAST = "Data ultrapassada"
    TODAY = "Hoje"
    SOON = "Próximos 30 dias"
    LATER = "Depois do horizonte"


def calculate_notice_date(end_date: date, calendar_days: int) -> date:
    if type(end_date) is not date:
        raise ValidationError("Informe uma data de término sem horário.")
    if type(calendar_days) is not int or calendar_days < 0:
        raise ValidationError("A antecedência deve ser um inteiro não negativo de dias corridos.")
    try:
        return end_date - timedelta(days=calendar_days)
    except OverflowError as exc:
        raise ValidationError("A data calculada está fora do intervalo suportado.") from exc


def classify_date(event_date: date, reference_date: date) -> TemporalStatus:
    if type(event_date) is not date or type(reference_date) is not date:
        raise ValidationError("A classificação usa datas sem horário.")
    difference = (event_date - reference_date).days
    if difference < 0:
        return TemporalStatus.PAST
    if difference == 0:
        return TemporalStatus.TODAY
    if difference <= 30:
        return TemporalStatus.SOON
    return TemporalStatus.LATER
