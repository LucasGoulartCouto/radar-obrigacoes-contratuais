"""Confere o gabarito de desenvolvimento, sem simular um extrator ou o fluxo futuro."""

import json
import re
from datetime import date
from pathlib import Path

import pytest

from radar_contratos.domain.dates import calculate_notice_date, classify_date

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "contracts" / "development"
CATALOG = json.loads((FIXTURES / "cases.json").read_text(encoding="utf-8"))
CASES = CATALOG["cases"]


def test_development_catalog_has_unique_cases_and_documents():
    assert CATALOG["schema_version"] == 1
    assert CATALOG["split"] == "development"
    assert CATALOG["decision_status"] in {"proposed", "accepted"}
    assert CATALOG["rule_version"] == "AVISO_CORRIDOS_V1"
    assert CATALOG["guardrails"] == {
        "synthetic_only": True,
        "automatic_confirmation": False,
        "external_actions": False,
    }
    ids = [case["id"] for case in CASES]
    assert len(ids) == len(set(ids))
    assert ids
    spec = (FIXTURES.parents[3] / "docs" / "specs" / "001-primeiro-fluxo.md").read_text(
        encoding="utf-8"
    )
    scenario_ids = set(re.findall(r"\| (C\d{2}) \|", spec))
    declared_paths = []
    for case in CASES:
        assert re.fullmatch(r"DEV-\d{3}", case["id"])
        assert case["spec_scenarios"]
        assert set(case["spec_scenarios"]) <= scenario_ids
        declared_paths.extend(document["path"] for document in case["documents"])
    assert len(declared_paths) == len(set(declared_paths))
    actual_paths = {path.relative_to(FIXTURES).as_posix() for path in FIXTURES.rglob("*.txt")}
    assert set(declared_paths) == actual_paths


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_development_oracle_matches_sources_and_existing_date_rules(case):
    documents = {}
    assert case["documents"]
    assert case["title"] and case["rationale"]
    for document in case["documents"]:
        assert document["id"] not in documents
        assert document["role"] in {"base", "aditivo", "substituição", "desconhecido"}
        path = (FIXTURES / document["path"]).resolve()
        assert path.is_relative_to((FIXTURES / "documents").resolve())
        raw = path.read_bytes()
        text = raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
        assert text.startswith("DOCUMENTO SINTÉTICO — SEM VALIDADE — CASE PRISMA\n")
        documents[document["id"]] = text.split("\n")

    annotations = [*case["facts"], *case["blockers"]]
    evidence_items = [annotation["evidence"] for annotation in annotations]
    if "untrusted_instruction" in case:
        evidence_items.append(case["untrusted_instruction"])
    for evidence in evidence_items:
        lines = documents[evidence["document_id"]]
        start, end = evidence["start_line"], evidence["end_line"]
        assert type(start) is int and type(end) is int
        assert 1 <= start <= end <= len(lines)
        assert evidence["quote"]
        assert "\n".join(lines[start - 1 : end]) == evidence["quote"]

    facts = {}
    for fact in case["facts"]:
        facts.setdefault(fact["field"], []).append(fact["value"])
        if fact["field"].endswith("date"):
            date.fromisoformat(fact["value"])
        if fact["field"] == "notice_rule":
            rule = fact["value"]
            assert type(rule["days"]) is int and rule["days"] >= 0
            assert rule["unit"] in {None, "calendar_days"}
            assert rule["anchor"] == "end_date"

    expected = case["expected"]
    assert expected["agenda_before_review"] == []
    assert type(expected["confirmation_allowed"]) is bool
    events = expected["candidate_events"]
    if case["blockers"]:
        assert expected["coverage_before_review"] == "Bloqueado"
        assert expected["confirmation_allowed"] is False
        assert expected["coverage_after_review"] is None
        assert events == []
        return

    assert expected["coverage_before_review"] == "Revisão pendente"
    assert expected["confirmation_allowed"] is True
    assert expected["coverage_after_review"] == (
        "Conferido com eventos" if events else "Conferido sem eventos no recorte"
    )
    if not events:
        assert case["facts"] == []
        return

    assert len(facts["end_date"]) == len(facts["notice_rule"]) == 1
    end_date = date.fromisoformat(facts["end_date"][0])
    notice_rule = facts["notice_rule"][0]
    assert notice_rule["unit"] == "calendar_days"
    by_kind = {event["kind"]: event for event in events}
    assert len(by_kind) == len(events) == 2
    assert set(by_kind) == {"termination", "non_renewal_notice"}
    assert date.fromisoformat(by_kind["termination"]["date"]) == end_date
    assert date.fromisoformat(by_kind["non_renewal_notice"]["date"]) == calculate_notice_date(
        end_date, notice_rule["days"]
    )
    reference = date.fromisoformat(CATALOG["reference_date"])
    for event in events:
        actual_status = classify_date(date.fromisoformat(event["date"]), reference)
        assert event["temporal_status"] == actual_status
