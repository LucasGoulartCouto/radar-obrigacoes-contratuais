"""Verifica o experimento e seus erros; não testa integração com a aplicação."""

import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from radar_contratos.infrastructure.experiments.extraction import (
    ExperimentDocument,
    Proposal,
    evaluate,
    evidence,
    extract_rules,
    load_documents,
    proposed_events,
    score_proposal,
)

CATALOG = Path(__file__).resolve().parents[1] / "fixtures/contracts/development/cases.json"
CASES = json.loads(CATALOG.read_text(encoding="utf-8"))["cases"]


def documents(number):
    return load_documents(CASES[number - 1], CATALOG.parent)


def test_rules_extract_sources_calculate_but_never_confirm():
    docs = documents(1)
    proposal = extract_rules(docs)
    assert [f["value"] for f in proposal.facts] == [
        "2027-06-30",
        {"days": 30, "unit": "calendar_days", "anchor": "end_date"},
    ]
    assert proposed_events(proposal) == [
        {"kind": "termination", "date": "2027-06-30"},
        {"kind": "non_renewal_notice", "date": "2027-05-31"},
    ]
    assert proposal.facts[0]["evidence"] == evidence(docs[0], 5)
    assert not proposal.blockers
    assert extract_rules(documents(8)).facts == proposal.facts


@pytest.mark.parametrize(
    "number,code",
    [
        (2, "undefined_day_unit"),
        (3, "conflicting_end_dates"),
        (4, "amendment_not_supported"),
        (11, "invalid_end_date"),
        (15, "invalid_notice_days"),
        (16, "invalid_notice_days"),
    ],
)
def test_known_blockers_remove_all_proposed_events(number, code):
    proposal = extract_rules(documents(number))
    assert code in {b["code"] for b in proposal.blockers}
    assert proposed_events(proposal) == []


def test_no_match_is_abstention_instead_of_verified_empty():
    proposal = extract_rules(documents(5))
    assert proposal == Proposal((), (), abstained=True)
    row = score_proposal(proposal, CASES[4], documents(5))
    assert row["expected_empty"] is True
    assert row["abstained"] is True
    assert row["exact_case"] is False


def test_rules_do_not_read_case_ids_filenames_or_answers():
    docs = tuple(replace(d, id="outro-identificador") for d in documents(1))
    result = extract_rules(docs)
    assert result.facts[0]["value"] == "2027-06-30"
    assert result.facts[0]["evidence"]["document_id"] == "outro-identificador"
    # Datas de pagamento e instruções com prefixo não casam com cláusula inteira.
    assert extract_rules(
        (ExperimentDocument("d", "base", "INSTRUÇÃO: Término do ciclo informado: 30/06/2027."),)
    ).abstained


def test_literal_quote_without_semantic_support_is_not_a_true_positive():
    # A gramática reconhece um exemplo; o gabarito aponta a vigência efetiva.
    docs = documents(20)
    row = score_proposal(extract_rules(docs), CASES[19], docs)
    assert row["invalid_evidence"] == 0
    assert row["facts"] == {"tp": 0, "fp": 1, "fn": 1}
    assert row["events"] == {"tp": 0, "fp": 1, "fn": 1}
    assert row["exact_case"] is False


def test_unsupported_blocker_is_visible_as_miss_and_false_event():
    docs = documents(18)
    row = score_proposal(extract_rules(docs), CASES[17], docs)
    assert row["blockers_missing"] == ["amendment_not_supported"]
    assert row["events"]["fp"] == 2


def test_invalid_quote_and_duplicate_predictions_cannot_inflate_correctness():
    docs = documents(1)
    proposal = extract_rules(docs)
    broken = dict(proposal.facts[0])
    broken["evidence"] = {**broken["evidence"], "quote": "citação inexistente"}
    row = score_proposal(Proposal((broken,)), CASES[0], docs)
    assert row["invalid_evidence"] == 1
    assert row["facts"] == {"tp": 0, "fp": 1, "fn": 2}
    repeated = score_proposal(Proposal(proposal.facts * 2), CASES[0], docs)
    assert repeated["facts"] == {"tp": 2, "fp": 2, "fn": 0}


def test_technical_failures_keep_denominators_and_are_not_empty():
    def broken(_documents):
        raise ValueError("Não registrar texto de origem.")

    report = evaluate(CATALOG, broken, method_version="BROKEN_TEST")
    expected_facts = sum(len(c["facts"]) for c in CASES)
    assert report["totals"]["failed_cases"] == len(CASES)
    assert report["totals"]["facts"]["fn"] == expected_facts
    assert report["totals"]["facts"]["recall"] == 0
    assert report["totals"]["failed_blocked_cases"] > 0
    assert report["totals"]["abstained_cases"] == 0
    assert "Não registrar" not in json.dumps(report)


def test_timeout_is_failure_and_preserves_expected_event_denominator():
    def timeout(_documents):
        raise TimeoutError("Conteúdo que não deve ir para o relatório.")

    report = evaluate(CATALOG, timeout, method_version="TIMEOUT_TEST")
    assert all(r["error_type"] == "TimeoutError" for r in report["cases"])
    assert report["totals"]["events"]["fn"] == sum(
        len(c["expected"]["candidate_events"]) for c in CASES
    )
    assert report["totals"]["abstained_cases"] == 0


def test_blocker_with_literal_but_unrelated_quote_is_not_supported():
    docs = documents(2)
    proposal = extract_rules(docs)
    blocker = {"code": "undefined_day_unit", "evidence": evidence(docs[0], 1)}
    row = score_proposal(Proposal(proposal.facts, (blocker,)), CASES[1], docs)
    assert row["invalid_evidence"] == 0
    assert row["blockers_missing"] == row["blockers_extra"] == ["undefined_day_unit"]
    assert row["exact_case"] is False


def test_extractor_only_receives_documents_and_report_fingerprints_inputs():
    calls = []

    def abstain(docs):
        assert all(isinstance(d, ExperimentDocument) for d in docs)
        calls.append(docs)
        return Proposal((), (), abstained=True)

    report = evaluate(CATALOG, abstain, method_version="ABSTAIN_TEST")
    assert len(calls) == 20
    assert len(report["document_sha256"]) == 21
    assert len(report["catalog_sha256"]) == len(report["evaluator_sha256"]) == 64
    assert report["method_sha256"] is None
    assert report["api_calls"] is report["api_cost"] is None
    assert report["independent_evaluation"] is False
    assert report["integrated_with_application"] is False


def test_loading_validates_reference_normalization_and_rejects_path_escape(tmp_path):
    path = tmp_path / "sample.txt"
    path.write_bytes(b"\xef\xbb\xbfline1\r\n\r\nline3\r")
    case = {"documents": [{"id": "d", "role": "base", "path": "sample.txt"}]}
    assert load_documents(case, tmp_path)[0].text == "line1\n\nline3\n"
    case["documents"][0]["path"] = "../sample.txt"
    with pytest.raises(ValueError, match="fora"):
        load_documents(case, tmp_path)


def test_evaluation_refuses_reserved_split(tmp_path):
    path = tmp_path / "cases.json"
    path.write_text('{"split":"reserved"}', encoding="utf-8")
    with pytest.raises(ValueError, match="reservada"):
        evaluate(path)


def test_cli_outputs_report_without_overwriting_previous_evidence(tmp_path):
    output = tmp_path / "result.json"
    command = [
        sys.executable,
        "-m",
        "radar_contratos.infrastructure.experiments.extraction",
        "--catalog",
        str(CATALOG),
        "--output",
        str(output),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    assert result.returncode == 0
    content = output.read_bytes()
    assert json.loads(content)["totals"]["cases"] == 20
    repeated = subprocess.run(command, capture_output=True, text=True, check=False)
    assert repeated.returncode == 1
    assert output.read_bytes() == content
    assert "FileExistsError" in repeated.stderr
