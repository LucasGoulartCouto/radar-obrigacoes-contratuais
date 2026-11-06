import json
from unittest.mock import Mock

import pytest

from radar_contratos.domain.documents import NORMALIZATION_VERSION
from radar_contratos.domain.reviews import ReferenceDocument
from radar_contratos.infrastructure.experiments.local_ai import MODEL, LocalInferenceError
from radar_contratos.infrastructure.local_classifier import OllamaLineClassifier

DOCUMENTS = (
    ReferenceDocument(
        "base", 0, "Término do ciclo informado: 30/06/2027.", "a" * 64, NORMALIZATION_VERSION
    ),
)
DIGEST = "a" * 64


def responses():
    return [
        {"version": "0.40.13"},
        {"models": [{"name": MODEL, "digest": DIGEST, "details": {"format": "gguf"}}]},
        {
            "model": MODEL,
            "done": True,
            "done_reason": "stop",
            "prompt_eval_count": 600,
            "eval_count": 30,
            "message": {
                "role": "assistant",
                "content": json.dumps(
                    {
                        "classifications": {"d1_l1": "termination"},
                        "abstained": False,
                    }
                ),
            },
        },
    ]


def test_classifier_validates_without_network_and_returns_classifications_without_actions(
    monkeypatch,
):
    transport = Mock(side_effect=responses())
    monkeypatch.setattr("radar_contratos.infrastructure.local_classifier.request_local", transport)
    classifier = OllamaLineClassifier(DIGEST)
    classifier.validate_input(DOCUMENTS)
    assert transport.call_count == 0
    result = classifier.classify(DOCUMENTS)
    assert result["classifications"] == {"d1_l1": "termination"}
    assert "facts" not in result and "candidate_events" not in result
    assert classifier.descriptor()["automatic_retries"] == 0
    assert transport.call_count == 3
    for call in transport.call_args_list:
        assert 0 < call.args[3] <= 120
    assert "tools" not in transport.call_args_list[-1].args[2]


def test_total_request_budget_does_not_restart_for_each_metadata_request(monkeypatch):
    transport = Mock(return_value=responses()[0])
    monkeypatch.setattr("radar_contratos.infrastructure.local_classifier.request_local", transport)
    monkeypatch.setattr(
        "radar_contratos.infrastructure.local_classifier.monotonic", Mock(side_effect=[0, 1, 121])
    )
    with pytest.raises(LocalInferenceError, match="LOCAL_TIMEOUT"):
        OllamaLineClassifier(DIGEST).classify(DOCUMENTS)
    assert transport.call_count == 1


def test_changed_model_digest_prevents_inference(monkeypatch):
    values = responses()
    values[1]["models"][0]["digest"] = "b" * 64
    transport = Mock(side_effect=values)
    monkeypatch.setattr("radar_contratos.infrastructure.local_classifier.request_local", transport)
    with pytest.raises(LocalInferenceError):
        OllamaLineClassifier(DIGEST).classify(DOCUMENTS)
    assert transport.call_count == 2
