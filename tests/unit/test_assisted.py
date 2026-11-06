import hashlib
import json
from pathlib import Path

import pytest

from radar_contratos.domain.assisted import prepare_assisted_analysis
from radar_contratos.domain.documents import NORMALIZATION_VERSION
from radar_contratos.domain.reviews import ReferenceDocument
from radar_contratos.errors import ValidationError
from radar_contratos.infrastructure.experiments.extraction import (
    Proposal,
    load_documents,
    proposed_events,
)

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "tests/fixtures/contracts/development/cases.json"
REPORT = ROOT / "docs/evidencias/ia-local-linhas-v1.json"


@pytest.mark.parametrize("index", range(20))
def test_assisted_boundary_preserves_all_twenty_original_proposals_without_human_corrections(index):
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    case = catalog["cases"][index]
    observation = report["observations"][index]
    documents = tuple(
        ReferenceDocument(
            d.id,
            position,
            d.text,
            hashlib.sha256(d.text.encode()).hexdigest(),
            NORMALIZATION_VERSION,
            d.role,
        )
        for position, d in enumerate(load_documents(case, CATALOG.parent))
    )
    payload = prepare_assisted_analysis(
        documents,
        observation["classifications"],
        observation["model_abstained"],
        known_amendment=False,
    )
    raw = observation["proposal"]
    assert payload["extraction"]["original"]["facts"] == raw["facts"]
    assert payload["candidate_events"] == proposed_events(
        Proposal(
            tuple(raw["facts"]),
            tuple(raw["blockers"]),
            raw["abstained"],
        )
    )
    assert payload["method_version"] != "MANUAL_V1"
    assert payload["rule_version"] == "AVISO_CORRIDOS_V1"


def test_empty_document_set_and_changed_normalization_are_rejected():
    with pytest.raises(ValidationError):
        prepare_assisted_analysis((), {}, False, known_amendment=False)
    with pytest.raises(ValidationError):
        prepare_assisted_analysis(
            (ReferenceDocument("base", 0, "Texto.", "a" * 64, "other"),),
            {"d1_l1": "context"},
            False,
            known_amendment=False,
        )
