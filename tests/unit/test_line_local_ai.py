"""Protocolo local com respostas simuladas; não requer GPU/runtime na suíte."""

import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from radar_contratos.infrastructure.experiments.extraction import ExperimentDocument
from radar_contratos.infrastructure.experiments.line_local_ai import (
    LineExtractor,
    classification_schema,
    run_evaluation,
    source_lines,
)
from radar_contratos.infrastructure.experiments.local_ai import (
    MODEL,
    LocalInferenceError,
)

DIGEST = "a" * 64
DOCUMENTS = (ExperimentDocument("base", "base", "Término do ciclo informado: 30/06/2027.\n"),)


def transport_for(labels):
    return Mock(
        side_effect=[
            {"version": "0.40.13"},
            {"models": [{"name": MODEL, "digest": DIGEST, "details": {"format": "gguf"}}]},
            {
                "model": MODEL,
                "done": True,
                "done_reason": "stop",
                "prompt_eval_count": 900,
                "eval_count": 30,
                "message": {
                    "role": "assistant",
                    "content": json.dumps({"classifications": labels, "abstained": False}),
                },
            },
        ]
    )


def test_dynamic_schema_requires_all_nonempty_lines_and_is_grounded_in_prompt():
    client = LineExtractor(DIGEST, transport=Mock())
    payload = client._payload(DOCUMENTS)
    schema = classification_schema(source_lines(DOCUMENTS))
    assert payload["format"] == schema
    assert schema["properties"]["classifications"]["required"] == ["d1_l1"]
    user = json.loads(payload["messages"][1]["content"])
    assert user["output_schema"] == schema
    assert user["source_lines"][0]["id"] == "d1_l1"
    assert "facts" not in schema["properties"]
    assert "tools" not in payload


def test_existing_multidocument_case_fits_without_truncating_sources():
    from radar_contratos.infrastructure.experiments.extraction import load_documents

    root = Path(__file__).resolve().parents[1] / "fixtures/contracts/development"
    case = json.loads((root / "cases.json").read_text(encoding="utf-8"))["cases"][3]
    documents = load_documents(case, root)
    payload = LineExtractor(DIGEST)._payload(documents)
    source = json.loads(payload["messages"][1]["content"])["source_lines"]
    assert {line["document_id"] for line in source} == {"base", "amendment"}
    assert all(
        line["text"]
        == next(d for d in documents if d.id == line["document_id"]).text.split("\n")[
            int(line["id"].split("_l")[1]) - 1
        ]
        for line in source
    )


def test_evidence_is_assembled_from_source_and_observation_separates_model_and_code():
    client = LineExtractor(DIGEST, transport=transport_for({"d1_l1": "termination"}))
    client.check_model()
    proposal = client(DOCUMENTS)
    assert proposal.facts[0]["value"] == "2027-06-30"
    assert proposal.facts[0]["evidence"]["quote"] == DOCUMENTS[0].text.rstrip("\n")
    assert client.observations[0]["citation_origin"] == "source_lines_by_code"
    assert client.observations[0]["classifications"] == {"d1_l1": "termination"}


def test_skipped_line_is_failure_instead_of_verified_empty():
    client = LineExtractor(DIGEST, transport=transport_for({}))
    client.check_model()
    with pytest.raises(LocalInferenceError, match="LINE_COVERAGE"):
        client(DOCUMENTS)
    assert client.observations[0]["ok"] is False


def test_duplicate_json_keys_cannot_silently_override_line_classification():
    client = LineExtractor(DIGEST)
    with pytest.raises(LocalInferenceError, match="DUPLICATE_JSON_KEY"):
        client._parse_content(
            '{"classifications":{"d1_l1":"termination","d1_l1":"context"},"abstained":false}',
            DOCUMENTS,
        )


def test_blank_lines_keep_their_original_numbers_without_required_classification():
    documents = (ExperimentDocument("d", "base", "\ufeffunused\n\nFim da vigência: 30/06/2027."),)
    lines = source_lines(documents)
    assert lines[2].number == 3
    assert classification_schema(lines)["properties"]["classifications"]["required"] == [
        "d1_l1",
        "d1_l3",
    ]


def mini_catalog(directory):
    (directory / "doc.txt").write_text(DOCUMENTS[0].text, encoding="utf-8")
    path = directory / "cases.json"
    path.write_text(
        json.dumps(
            {
                "split": "development",
                "cases": [
                    {
                        "id": "case-renamed",
                        "documents": [{"id": "base", "role": "base", "path": "doc.txt"}],
                        "facts": [
                            {
                                "field": "end_date",
                                "value": "2027-06-30",
                                "evidence": {
                                    "document_id": "base",
                                    "start_line": 1,
                                    "end_line": 1,
                                    "quote": DOCUMENTS[0].text.rstrip("\n"),
                                },
                            }
                        ],
                        "blockers": [],
                        "expected": {
                            "candidate_events": [{"kind": "termination", "date": "2027-06-30"}]
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def test_round_preserves_progress_counts_and_component_hashes_without_overwrite(tmp_path):
    catalog = mini_catalog(tmp_path)
    output = tmp_path / "result.json"
    client = LineExtractor(DIGEST, transport=transport_for({"d1_l1": "termination"}))
    report = run_evaluation(catalog, output, client)
    assert report["totals"]["exact_cases"] == 1
    assert report["local_inference_requests"] == 1
    assert report["local_metadata_requests"] == 2
    assert len(report["component_sha256"]) == 4
    partial = json.loads(Path(str(output) + ".partial.json").read_text(encoding="utf-8"))
    assert partial["status"] == "completed" and partial["recorded_attempts"] == 1
    assert partial["observations"][0]["case_id"] == "case-renamed"
    original = output.read_bytes()
    with pytest.raises(ValueError):
        run_evaluation(catalog, output, client)
    assert output.read_bytes() == original


def test_interrupted_round_is_preserved_and_cannot_be_silently_repeated(tmp_path):
    catalog = mini_catalog(tmp_path)
    response = transport_for({"d1_l1": "termination"})
    values = list(response.side_effect)
    response.side_effect = [*values[:2], KeyboardInterrupt()]
    client = LineExtractor(DIGEST, transport=response)
    output = tmp_path / "interrupted.json"
    with pytest.raises(KeyboardInterrupt):
        run_evaluation(catalog, output, client)
    partial = json.loads(Path(str(output) + ".partial.json").read_text(encoding="utf-8"))
    assert partial["status"] == "interrupted_or_failed"
    assert partial["recorded_attempts"] == 1
    assert not output.exists()
    with pytest.raises(ValueError):
        run_evaluation(catalog, output, client)


def test_changed_source_invalidates_round_without_hiding_its_observations(tmp_path, monkeypatch):
    from radar_contratos.infrastructure.experiments import line_local_ai

    hashes = line_local_ai.component_hashes()
    changed = {**hashes, "literal_extraction.py": "f" * 64}
    monkeypatch.setattr(line_local_ai, "component_hashes", Mock(side_effect=[hashes, changed]))
    client = LineExtractor(DIGEST, transport=transport_for({"d1_l1": "termination"}))
    output = tmp_path / "changed.json"
    report = run_evaluation(mini_catalog(tmp_path), output, client)
    assert report["source_changed_during_run"] is True
    assert report["observations"][0]["proposal"]["facts"]
    state = json.loads(Path(str(output) + ".partial.json").read_text(encoding="utf-8"))
    assert state["status"] == "invalidated_source_changed"
