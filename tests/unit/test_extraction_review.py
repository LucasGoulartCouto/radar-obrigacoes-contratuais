"""Decisões de contexto simuladas, separadas da capacidade da extração automática."""

import json
from dataclasses import replace
from pathlib import Path

import pytest

from radar_contratos.domain.extraction_review import (
    ContextDecision,
    review_retention,
    source_fingerprint,
)
from radar_contratos.domain.literal_extraction import LiteralLine, interpret_lines
from radar_contratos.errors import StaleRecordError, ValidationError
from radar_contratos.infrastructure.experiments.extraction import Proposal, proposed_events
from radar_contratos.infrastructure.experiments.retention_review import (
    load_observation,
    make_receipt,
)

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs/evidencias/ia-local-linhas-v1.json"
CATALOG = ROOT / "tests/fixtures/contracts/development/cases.json"


def source(case_id="DEV-008"):
    return load_observation(REPORT, CATALOG, case_id)


def decision_for(observation, alias, disposition):
    return ContextDecision(
        alias,
        disposition,
        next(item.text for item in observation["lines"] if item.alias == alias),
        "Conferência simulada do contexto completo: este trecho não define condição efetiva.",
    )


def review(observation, decisions=(), **changes):
    arguments = {
        "decisions": decisions,
        "expected_source": source_fingerprint(
            observation["lines"],
            observation["labels"],
            abstained=observation["abstained"],
            known_amendment=False,
        ),
        "actor": "Marina - simulação pelo agente",
        "acknowledged": True,
        "known_amendment": False,
        "abstained": observation["abstained"],
    }
    arguments.update(changes)
    return review_retention(observation["lines"], observation["labels"], **arguments)


def candidates(receipt):
    result = receipt["reviewed"]
    return proposed_events(Proposal(tuple(result["facts"]), tuple(result["blockers"])))


@pytest.mark.parametrize(
    "case_id,alias,disposition,dates",
    [
        ("DEV-008", "d1_l7", "untrusted_instruction", ["2027-06-30", "2027-05-31"]),
        ("DEV-020", "d1_l6", "illustrative", ["2027-08-31"]),
    ],
)
def test_review_releases_only_existing_facts_and_preserves_raw_retention(
    case_id,
    alias,
    disposition,
    dates,
):
    observation = source(case_id)
    raw = interpret_lines(observation["lines"], observation["labels"])
    receipt = review(observation, (decision_for(observation, alias, disposition),))
    assert raw.blockers and receipt["original"]["blockers"]
    assert receipt["reviewed"]["blockers"] == []
    assert receipt["reviewed"]["facts"] == list(raw.facts)
    assert [event["date"] for event in candidates(receipt)] == dates
    assert receipt["confirmed"] is False
    assert receipt["decisions"][0]["original_label"] == observation["labels"][alias]
    assert observation["labels"][alias] in {"unsupported", "termination"}


def test_acknowledgment_alone_does_not_resolve_retention():
    receipt = review(source())
    assert receipt["reviewed"]["blockers"]
    assert candidates(receipt) == []


@pytest.mark.parametrize("acknowledged", [False, None, 1, "true"])
def test_explicit_review_declaration_is_required(acknowledged):
    with pytest.raises(ValidationError):
        review(source(), acknowledged=acknowledged)


@pytest.mark.parametrize("field,value", [("actor", ""), ("actor", "x\ny"), ("actor", "x" * 81)])
def test_reviewer_is_required(field, value):
    with pytest.raises(ValidationError):
        review(source(), **{field: value})


@pytest.mark.parametrize("change", ["text", "role", "labels", "history", "version"])
def test_any_change_in_reviewed_base_invalidates_the_decision(change, monkeypatch):
    observation = source()
    fingerprint = source_fingerprint(
        observation["lines"],
        observation["labels"],
        known_amendment=False,
    )
    options = {}
    if change == "text":
        observation["lines"] = (
            replace(observation["lines"][0], text="Cabeçalho alterado."),
            *observation["lines"][1:],
        )
    elif change == "role":
        observation["lines"] = tuple(replace(line, role="aditivo") for line in observation["lines"])
    elif change == "labels":
        observation["labels"]["d1_l7"] = "context"
    elif change == "history":
        options["known_amendment"] = True
    else:
        monkeypatch.setattr("radar_contratos.domain.extraction_review.REVIEW_VERSION", "NEXT")
    with pytest.raises(StaleRecordError):
        review(observation, expected_source=fingerprint, **options)


def test_known_amendment_survives_context_decision():
    observation = source()
    receipt = review(
        observation,
        (decision_for(observation, "d1_l7", "untrusted_instruction"),),
        known_amendment=True,
        expected_source=source_fingerprint(
            observation["lines"],
            observation["labels"],
            known_amendment=True,
        ),
    )
    assert receipt["reviewed"]["blockers"] == [
        {"code": "known_amendment_history", "evidence": None}
    ]
    assert candidates(receipt) == []


@pytest.mark.parametrize("fault", ["quote", "alias", "reason", "disposition", "duplicate"])
def test_invalid_or_unsupported_context_decision_is_rejected(fault):
    observation = source()
    decision = decision_for(observation, "d1_l7", "untrusted_instruction")
    changes = {"quote": "outra citação", "alias": "missing", "reason": "", "disposition": "ignore"}
    decisions = (
        (decision, decision)
        if fault == "duplicate"
        else (replace(decision, **{fault: changes[fault]}),)
    )
    with pytest.raises(ValidationError):
        review(observation, decisions)


@pytest.mark.parametrize(
    "extra",
    [" Término: 30/06/2027.", " O aviso é de 30 dias.", " Há aditivo.", " Vigência efetiva."],
)
def test_instruction_prefix_cannot_hide_mixed_contractual_content(extra):
    observation = source()
    observation["lines"] = tuple(
        replace(line, text=line.text + extra) if line.alias == "d1_l7" else line
        for line in observation["lines"]
    )
    with pytest.raises(ValidationError):
        review(observation, (decision_for(observation, "d1_l7", "untrusted_instruction"),))


def test_partial_resolution_keeps_the_unresolved_line_as_blocker_evidence():
    observation = source()
    number = len(observation["lines"]) + 1
    observation["lines"] += (LiteralLine("extra", "base", number, "Condição ambígua.", "base"),)
    observation["labels"]["extra"] = "unsupported"
    receipt = review(observation, (decision_for(observation, "d1_l7", "untrusted_instruction"),))
    assert receipt["reviewed"]["blockers"][0]["evidence"]["start_line"] == number
    assert candidates(receipt) == []


def test_illustration_marker_in_another_document_does_not_authorize_resolution():
    observation = source("DEV-020")
    observation["lines"] = tuple(
        replace(line, text="Contexto sem marcador.") if line.alias == "d1_l5" else line
        for line in observation["lines"]
    )
    observation["lines"] += (
        LiteralLine("other", "other-document", 1, "O exemplo não define a vigência:", "base"),
    )
    observation["labels"]["other"] = "illustrative"
    with pytest.raises(ValidationError):
        review(observation, (decision_for(observation, "d1_l6", "illustrative"),))


def test_abstention_cannot_be_resolved_as_context():
    observation = source()
    observation["abstained"] = True
    with pytest.raises(ValidationError):
        review(observation)


def test_all_twenty_saved_observations_preserve_blockers_without_decisions():
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    for observation in report["observations"]:
        receipt = review(source(observation["case_id"]))
        assert receipt["reviewed"]["facts"] == observation["proposal"]["facts"]
        assert {b["code"] for b in receipt["reviewed"]["blockers"]} == {
            b["code"] for b in observation["proposal"]["blockers"]
        }


@pytest.mark.parametrize(
    "case_id", ["DEV-002", "DEV-003", "DEV-004", "DEV-011", "DEV-012", "DEV-015", "DEV-017"]
)
def test_domain_blockers_cannot_be_dismissed_by_context_review(case_id):
    observation = source(case_id)
    raw = interpret_lines(observation["lines"], observation["labels"])
    evidence = raw.blockers[0]["evidence"]
    alias = next(
        line.alias
        for line in observation["lines"]
        if line.document_id == evidence["document_id"] and line.number == evidence["start_line"]
    )
    with pytest.raises(ValidationError):
        review(observation, (decision_for(observation, alias, "untrusted_instruction"),))
    assert candidates(review(observation)) == []


def test_receipt_plan_is_bound_to_case_and_report():
    observation = source()
    plan = {
        "case_id": "DEV-020",
        "expected_report": observation["report_sha256"],
        "expected_source": "0" * 64,
        "actor": "Marina",
        "acknowledged": True,
        "known_amendment": False,
        "decisions": [],
    }
    with pytest.raises(StaleRecordError):
        make_receipt(observation, plan)
    plan["case_id"], plan["expected_report"] = "DEV-008", "0" * 64
    with pytest.raises(StaleRecordError):
        make_receipt(observation, plan)


def test_missing_or_unordered_source_lines_are_rejected_without_partial_review():
    observation = source()
    observation["lines"] = observation["lines"][1:]
    with pytest.raises(ValidationError):
        review(observation)
