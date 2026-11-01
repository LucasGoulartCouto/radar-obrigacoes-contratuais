"""Interpretação de origem, sem pedir ao modelo para normalizar valores."""

import pytest

from radar_contratos.domain.literal_extraction import LiteralLine, interpret_lines
from radar_contratos.errors import ValidationError
from radar_contratos.infrastructure.experiments.extraction import Proposal, proposed_events


def lines(*texts, role="base"):
    return tuple(LiteralLine(f"x{i}", "origem", i, text, role) for i, text in enumerate(texts, 1))


def result_for(end="30/06/2027", duration="30 dias corridos"):
    source = lines(
        f"Término do ciclo informado: {end}.",
        f"Para não renovar, avisar com {duration} em relação à data de término.",
    )
    return interpret_lines(source, {"x1": "termination", "x2": "notice"})


def events(result):
    return proposed_events(Proposal(result.facts, result.blockers, result.abstained))


@pytest.mark.parametrize(
    "duration,code",
    [
        ("30 dias", "undefined_day_unit"),
        ("10 dias úteis", "unsupported_day_unit"),
        ("2 meses", "unsupported_day_unit"),
        ("-3 dias corridos", "invalid_notice_days"),
        ("1,5 dias corridos", "invalid_notice_days"),
        ("30 (sessenta) dias corridos", "conflicting_notice_days"),
    ],
)
def test_invalid_literals_are_blocked_instead_of_coerced(duration, code):
    result = result_for(duration=duration)
    assert code in {b["code"] for b in result.blockers}
    assert events(result) == []
    assert duration in result.blockers[0]["evidence"]["quote"]


def test_literal_zero_positive_sign_and_same_written_number_are_supported():
    for duration, days in [
        ("0 dias corridos", 0),
        ("+3 dias corridos", 3),
        ("30 (trinta) dias corridos", 30),
    ]:
        result = result_for(duration=duration)
        assert result.blockers == ()
        assert next(f["value"]["days"] for f in result.facts if f["field"] == "notice_rule") == days
    assert events(result_for(end="01/03/2028", duration="1 dia corrido"))[1]["date"] == "2028-02-29"


def test_other_anchor_and_missing_end_date_block_without_partial_events():
    source = lines(
        "Término do ciclo informado: 30/06/2027.",
        "Para não renovar, avisar 30 dias corridos após a entrega sem data.",
    )
    result = interpret_lines(source, {"x1": "termination", "x2": "notice"})
    assert result.blockers[0]["code"] == "unsupported_anchor"
    assert events(result) == []
    source = lines("Avisar com 10 dias corridos antes do término.")
    assert interpret_lines(source, {"x1": "notice"}).blockers[0]["code"] == "unsupported_anchor"


def test_date_conflict_preserves_facts_and_literal_span_including_empty_lines():
    source = lines("O ciclo termina em 30/06/2027.", "", "O mesmo ciclo termina em 31/07/2027.")
    result = interpret_lines(source, {"x1": "termination", "x3": "termination"})
    assert [f["value"] for f in result.facts] == ["2027-06-30", "2027-07-31"]
    assert result.blockers[0]["code"] == "conflicting_end_dates"
    assert result.blockers[0]["evidence"]["quote"] == "\n".join(
        source_line.text for source_line in source
    )
    assert events(result) == []


def test_impossible_date_is_domain_blocker_instead_of_normalized_fake_date():
    result = result_for(end="31/02/2027")
    assert "invalid_end_date" in {b["code"] for b in result.blockers}
    assert not any(f["field"] == "end_date" for f in result.facts)
    assert events(result) == []


def test_declared_amendment_cannot_be_hidden_by_context_label_or_abstention():
    source = lines("ADITIVO ao contrato.", "O término passa a 31/08/2027.", role="aditivo")
    result = interpret_lines(source, {"x1": "context", "x2": "termination"})
    assert result.blockers[0]["code"] == "amendment_not_supported"
    assert result.blockers[0]["evidence"]["start_line"] == 1
    assert events(result) == []
    result = interpret_lines(source, {"x1": "context", "x2": "context"}, abstained=True)
    assert result.blockers[0]["code"] == "amendment_not_supported"
    assert any(f["code"] == "model_abstained" for f in result.findings)


def test_explicit_amendment_is_guarded_without_treating_negation_as_declaration():
    for text in (
        "Este instrumento é aditivo ao contrato.",
        "Este documento constitui um aditivo ao contrato.",
    ):
        result = interpret_lines(lines(text), {"x1": "context"})
        assert result.blockers[0]["code"] == "amendment_not_supported"
    negative = interpret_lines(lines("Não há aditivo neste conjunto."), {"x1": "no_event"})
    assert negative.blockers == ()


def test_illustration_and_payment_cannot_be_published_as_end_dates():
    source = lines(
        "O exemplo a seguir não define a vigência deste contrato:",
        "Término do ciclo informado: 30/06/2027.",
        "A vigência efetiva encerra-se em 31/08/2027.",
    )
    good = interpret_lines(
        source,
        {
            "x1": "context",
            "x2": "illustrative",
            "x3": "termination",
        },
    )
    assert events(good) == [{"kind": "termination", "date": "2027-08-31"}]
    bad = interpret_lines(
        source,
        {
            "x1": "context",
            "x2": "termination",
            "x3": "termination",
        },
    )
    assert not any(f["value"] == "2027-06-30" for f in bad.facts)
    assert events(bad) == []
    payment = interpret_lines(lines("Data de pagamento: 30/06/2027."), {"x1": "termination"})
    assert payment.facts == ()
    assert payment.blockers[0]["code"] == "unsupported_scope"


def test_relevant_line_labeled_context_or_unjustified_absence_is_not_empty_success():
    for label in ("context", "no_event", "illustrative"):
        result = interpret_lines(lines("Término do ciclo informado: 30/06/2027."), {"x1": label})
        assert result.blockers
        assert events(result) == []
    no_event = interpret_lines(lines("Não há data de término neste texto."), {"x1": "no_event"})
    assert not no_event.facts and not no_event.blockers and not no_event.abstained
    abstention = interpret_lines(
        lines("Texto que não consigo interpretar."), {"x1": "context"}, abstained=True
    )
    assert abstention.abstained


@pytest.mark.parametrize(
    "labels", [{}, {"x1": "notice", "extra": "context"}, {"x1": "other"}, {"x1": True}]
)
def test_missing_extra_and_invalid_classifications_are_rejected(labels):
    with pytest.raises(ValidationError):
        interpret_lines(lines("Texto."), labels)


def test_metadata_prefix_with_literal_condition_cannot_hide_an_event():
    result = interpret_lines(
        lines("Fornecedor fictício: A vigência termina em 30/06/2027."), {"x1": "context"}
    )
    assert result.blockers[0]["code"] == "unsupported_scope"
    assert events(result) == []


def test_no_documents_or_duplicate_origin_are_not_verified_empty():
    with pytest.raises(ValidationError):
        interpret_lines((), {})
    source = lines("Texto.")
    with pytest.raises(ValidationError):
        interpret_lines(source * 2, {"x1": "context"})


def test_repeated_notice_keeps_one_candidate_and_additional_source_record():
    source = lines(
        "O ciclo termina em 30/06/2027.",
        "Avisar com 30 dias corridos antes do término.",
        "Avisar com 30 dias corridos antes do término.",
    )
    result = interpret_lines(source, {"x1": "termination", "x2": "notice", "x3": "notice"})
    assert len(events(result)) == 2
    assert any(f["code"] == "repeated_notice" for f in result.findings)


def test_conflicting_rules_in_combined_lines_are_blocked():
    source = lines(
        "O ciclo termina em 30/06/2027. Avisar com 30 dias corridos antes do término.",
        "O ciclo termina em 30/06/2027. Avisar com 60 dias corridos antes do término.",
    )
    result = interpret_lines(
        source, {"x1": "termination_and_notice", "x2": "termination_and_notice"}
    )
    assert result.blockers[0]["code"] == "conflicting_notice_days"
    assert events(result) == []
