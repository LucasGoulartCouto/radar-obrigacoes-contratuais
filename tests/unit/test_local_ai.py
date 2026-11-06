"""Testes da fronteira local com transporte simulado, sem rede/modelo na CI."""

import copy
import json
from unittest.mock import Mock

import pytest

from radar_contratos.infrastructure.experiments.extraction import ExperimentDocument
from radar_contratos.infrastructure.experiments.local_ai import (
    CONTEXT_TOKENS,
    MAX_REPLY_BYTES,
    MODEL,
    LocalExtractor,
    LocalInferenceError,
    parse_proposal,
    request_local,
    validate_endpoint,
)

DIGEST = "a" * 64
DOCUMENTS = (ExperimentDocument("base", "base", "Término do ciclo informado: 30/06/2027."),)
RESULT = {
    "facts": [
        {
            "field": "end_date",
            "value": "2027-06-30",
            "evidence": {
                "document_id": "base",
                "start_line": 1,
                "end_line": 1,
                "quote": DOCUMENTS[0].text,
            },
        }
    ],
    "blockers": [],
    "abstained": False,
}


def envelope(content=None):
    return {
        "done": True,
        "done_reason": "stop",
        "model": MODEL,
        "message": {"role": "assistant", "content": json.dumps(content or RESULT)},
        "prompt_eval_count": 500,
        "eval_count": 100,
    }


@pytest.mark.parametrize(
    "url",
    [
        "https://127.0.0.1:11435",
        "http://example.com:11435",
        "http://localhost:11435",
        "http://127.0.0.1:11435/api",
        "http://user:pass@127.0.0.1:11435",
        "http://127.0.0.1:11435?model=x",
        "http://127.0.0.1",
        "http://127.0.0.1:11435#x",
    ],
)
def test_endpoint_rejects_nonliteral_loopback_and_extra_parts(url):
    with pytest.raises(ValueError):
        validate_endpoint(url)


def test_local_success_sends_only_documents_schema_and_no_actions():
    transport = Mock(return_value=envelope())
    extractor = LocalExtractor(DIGEST, transport=transport)
    proposal = extractor(DOCUMENTS)
    payload = transport.call_args.args[2]
    assert payload["model"] == MODEL
    assert payload["stream"] is False
    assert "tools" not in payload
    assert len(payload["messages"]) == 2
    assert payload["format"]["additionalProperties"] is False
    user = json.loads(payload["messages"][1]["content"])
    assert set(user[0]) == {"document_id", "role", "lines"}
    assert proposal.facts == tuple(RESULT["facts"])
    assert extractor.observations[0]["ok"] is True
    assert extractor.inference_requests == 1
    assert "confirmed" not in extractor.observations[0]["proposal"]


@pytest.mark.parametrize(
    "change",
    [
        {"done": False},
        {"done_reason": "length"},
        {"model": "different:latest"},
        {"prompt_eval_count": 8000, "eval_count": 500},
        {"prompt_eval_count": None},
        {"eval_count": True},
        {
            "message": {
                "role": "assistant",
                "content": "{}",
                "tool_calls": [{"function": "send_message"}],
            }
        },
    ],
)
def test_truncation_different_model_unverified_context_and_tools_fail(change):
    response = {**envelope(), **change}
    extractor = LocalExtractor(DIGEST, transport=Mock(return_value=response))
    with pytest.raises(LocalInferenceError):
        extractor(DOCUMENTS)
    assert extractor.observations[0]["ok"] is False
    assert "proposal" not in extractor.observations[0]


@pytest.mark.parametrize(
    "value",
    [
        "2027-02-31",
        "20270630",
        "30/06/2027",
        None,
        True,
    ],
)
def test_invalid_or_nonnormalized_dates_fail(value):
    result = copy.deepcopy(RESULT)
    result["facts"][0]["value"] = value
    with pytest.raises(LocalInferenceError, match="INVALID_DATE"):
        parse_proposal(json.dumps(result), DOCUMENTS)


def test_nonliteral_evidence_and_extra_confirmation_are_rejected():
    result = copy.deepcopy(RESULT)
    result["facts"][0]["evidence"]["quote"] = "Término inventado"
    with pytest.raises(LocalInferenceError, match="INVALID_EVIDENCE"):
        parse_proposal(json.dumps(result), DOCUMENTS)
    result = {**RESULT, "confirmed": True}
    with pytest.raises(LocalInferenceError, match="INVALID_SCHEMA"):
        parse_proposal(json.dumps(result), DOCUMENTS)


@pytest.mark.parametrize("days", [-1, 1.5, True, "30"])
def test_invalid_notice_days_are_not_coerced(days):
    result = copy.deepcopy(RESULT)
    result["facts"][0].update(
        {
            "field": "notice_rule",
            "value": {"days": days, "unit": "calendar_days", "anchor": "end_date"},
        }
    )
    with pytest.raises(LocalInferenceError, match="INVALID_NOTICE"):
        parse_proposal(json.dumps(result), DOCUMENTS)


def test_empty_and_abstention_are_distinct_and_neither_confirms():
    empty = parse_proposal('{"facts":[],"blockers":[],"abstained":false}', DOCUMENTS)
    abstained = parse_proposal('{"facts":[],"blockers":[],"abstained":true}', DOCUMENTS)
    assert empty.facts == abstained.facts == ()
    assert empty.abstained is False and abstained.abstained is True
    with pytest.raises(LocalInferenceError, match="INVALID_SCHEMA"):
        parse_proposal(json.dumps({**RESULT, "abstained": True}), DOCUMENTS)


def test_oversized_prompt_fails_without_sending_or_losing_observation():
    transport = Mock()
    extractor = LocalExtractor(DIGEST, transport=transport)
    with pytest.raises(LocalInferenceError, match="INPUT_EXCEEDS"):
        extractor((ExperimentDocument("d", "base", "x" * CONTEXT_TOKENS),))
    transport.assert_not_called()
    assert extractor.inference_requests == 0
    assert extractor.observations[0]["error_code"] == "LOCAL_INPUT_EXCEEDS_CONTEXT_BUDGET"


def test_model_digest_format_and_runtime_version_are_checked():
    transport = Mock(
        side_effect=[
            {"version": "0.40.13"},
            {"models": [{"name": MODEL, "digest": DIGEST, "details": {"format": "gguf"}}]},
        ]
    )
    extractor = LocalExtractor(DIGEST, transport=transport)
    extractor.check_model()
    assert extractor.runtime_version == "0.40.13"
    assert extractor.metadata_requests == 2
    for changed in (
        {"digest": "b" * 64},
        {"details": {"format": "remote"}},
        {"remote_host": "ollama.com"},
    ):
        model = {"name": MODEL, "digest": DIGEST, "details": {"format": "gguf"}, **changed}
        extractor = LocalExtractor(
            DIGEST,
            transport=Mock(
                side_effect=[
                    {"version": "0.40.13"},
                    {"models": [model]},
                ]
            ),
        )
        with pytest.raises(LocalInferenceError, match="MODEL_NOT_PINNED"):
            extractor.check_model()


def test_timeout_does_not_turn_into_empty_or_store_document_message():
    extractor = LocalExtractor(DIGEST, transport=Mock(side_effect=TimeoutError("texto sensível")))
    with pytest.raises(TimeoutError):
        extractor(DOCUMENTS)
    assert extractor.observations[0]["ok"] is False
    assert "texto sensível" not in json.dumps(extractor.observations)


def test_http_rejects_redirects_without_reading_or_following_target(monkeypatch):
    connection = Mock()
    connection.getresponse.return_value.status = 302
    factory = Mock(return_value=connection)
    monkeypatch.setattr("http.client.HTTPConnection", factory)
    with pytest.raises(LocalInferenceError, match="LOCAL_HTTP_302"):
        request_local("http://127.0.0.1:11435", "/api/chat", {"x": 1}, 1)
    assert factory.call_args.args == ("127.0.0.1", 11435)
    connection.getresponse.return_value.read.assert_not_called()
    connection.close.assert_called_once()


@pytest.mark.parametrize(
    "raw,code",
    [
        (b"[]", "LOCAL_INVALID_ENVELOPE"),
        (b"invalid-json", "LOCAL_TRANSPORT_FAILURE"),
        (b"x" * (MAX_REPLY_BYTES + 1), "LOCAL_RESPONSE_TOO_LARGE"),
    ],
)
def test_http_bounds_and_invalid_response_are_rejected(monkeypatch, raw, code):
    connection = Mock()
    response = connection.getresponse.return_value
    response.status = 200
    response.read.return_value = raw
    monkeypatch.setattr("http.client.HTTPConnection", Mock(return_value=connection))
    with pytest.raises(LocalInferenceError, match=code):
        request_local("http://127.0.0.1:11435", "/api/chat", {"x": 1}, 1)
    response.read.assert_called_once_with(MAX_REPLY_BYTES + 1)
    connection.close.assert_called_once()
