import json
from dataclasses import replace
from datetime import date, datetime
from pathlib import Path

import pytest

from radar_contratos.domain.reviews import (
    EvidenceInput,
    ManualDraft,
    ReferenceDocument,
    locate_evidence,
    prepare_manual_analysis,
)
from radar_contratos.errors import ValidationError

ROOT = Path(__file__).parents[1] / "fixtures/contracts/development"
CATALOG = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))


def reference(text="Término: 30/06/2027.\nAviso: 30 dias corridos antes do término."):
    return ReferenceDocument("documento", 0, text, "a" * 64, "TEXT_REFERENCE_V1")


def evidence(document, start, end=None):
    end = start if end is None else end
    return EvidenceInput(
        document.position,
        start,
        end,
        "\n".join(document.reference_text.split("\n")[start - 1 : end]),
    )


def valid_draft(document=None):
    document = document or reference()
    return ManualDraft(
        end_date=date(2027, 6, 30),
        end_evidence=evidence(document, 1),
        notice_days=30,
        notice_evidence=evidence(document, 2),
    )


@pytest.mark.parametrize("case", CATALOG["cases"], ids=lambda item: item["id"])
def test_annotated_cases_match_manual_rules_without_claiming_extraction(case):
    documents = tuple(
        ReferenceDocument(
            item["id"],
            index,
            (ROOT / item["path"])
            .read_bytes()
            .decode("utf-8-sig")
            .replace("\r\n", "\n")
            .replace("\r", "\n"),
            "a" * 64,
            "TEXT_REFERENCE_V1",
        )
        for index, item in enumerate(case["documents"])
    )
    by_id = {item.id: item for item in documents}

    def annotation(value):
        return EvidenceInput(
            by_id[value["document_id"]].position,
            value["start_line"],
            value["end_line"],
            value["quote"],
        )

    fields = {item["field"]: item for item in case["facts"]}
    if case["id"] in {"DEV-003", "DEV-004"}:
        blocker = case["blockers"][0]
        draft = ManualDraft(
            mode="blocked",
            blocker_reason=blocker["code"],
            blocker_evidence=annotation(blocker["evidence"]),
        )
    elif not fields:
        draft = ManualDraft(mode="empty")
    else:
        end, notice = fields["end_date"], fields["notice_rule"]
        draft = ManualDraft(
            end_date=date.fromisoformat(end["value"]),
            end_evidence=annotation(end["evidence"]),
            notice_days=notice["value"]["days"],
            notice_evidence=annotation(notice["evidence"]),
            notice_unit=notice["value"]["unit"] or "undefined",
        )
    result = prepare_manual_analysis(draft, documents, known_amendment=case["id"] == "DEV-004")
    assert bool(result["blockers"]) == bool(case["blockers"])
    assert result["candidate_events"] == [
        {"kind": item["kind"], "date": item["date"]}
        for item in case["expected"]["candidate_events"]
    ]
    assert "confirmed" not in result


@pytest.mark.parametrize(
    "change",
    [
        {"quote": "citação inventada"},
        {"document_position": -1},
        {"start_line": 0},
        {"end_line": 100},
        {"start_line": True},
        {"end_line": 0},
    ],
)
def test_invalid_evidence_is_rejected(change):
    document = reference()
    with pytest.raises(ValidationError):
        locate_evidence(replace(evidence(document, 1), **change), (document,))


@pytest.mark.parametrize(
    "change",
    [
        {"notice_days": -1},
        {"notice_days": 1.5},
        {"notice_days": True},
        {"end_date": datetime(2027, 6, 30)},
        {"end_evidence": None},
        {"notice_evidence": None},
        {"notice_unit": "inventada"},
    ],
)
def test_invalid_manual_fields_cannot_produce_candidates(change):
    with pytest.raises(ValidationError):
        prepare_manual_analysis(replace(valid_draft(), **change), (reference(),))


def test_evidence_location_does_not_prove_semantic_support():
    document = reference("Trecho literal sem uma data de término.\nOutro trecho.")
    result = prepare_manual_analysis(valid_draft(document), (document,))
    assert result["candidate_events"][0]["date"] == "2027-06-30"
    # A confirmação humana, e não a localização literal, deve avaliar esse desacordo.
    assert result["evidence"]["end_date"]["quote"] == document.reference_text.split("\n")[0]


def test_empty_mode_cannot_hide_supplied_events():
    with pytest.raises(ValidationError):
        prepare_manual_analysis(replace(valid_draft(), mode="empty"), (reference(),))


def test_unknown_anchor_blocks_instead_of_inventing_a_date():
    result = prepare_manual_analysis(
        replace(valid_draft(), notice_anchor="unknown"), (reference(),)
    )
    assert result["blockers"]
    assert result["candidate_events"] == []
