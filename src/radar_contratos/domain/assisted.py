"""Propostas assistidas: origem literal, cálculo e revisão; sem confirmar eventos."""

import json
from dataclasses import asdict
from datetime import date

from radar_contratos.domain.dates import calculate_notice_date
from radar_contratos.domain.documents import NORMALIZATION_VERSION
from radar_contratos.domain.extraction_review import ContextDecision, review_retention
from radar_contratos.domain.literal_extraction import LiteralLine, interpret_lines
from radar_contratos.domain.reviews import (
    RULE_VERSION,
    EvidenceInput,
    ManualDraft,
    ReferenceDocument,
    draft_payload,
    locate_evidence,
)
from radar_contratos.errors import ValidationError

METHOD_VERSION = "ASSISTED_LOCAL_LINES_V1"


def literal_lines(documents: tuple[ReferenceDocument, ...]) -> tuple[LiteralLine, ...]:
    if not documents or any(d.normalization_version != NORMALIZATION_VERSION for d in documents):
        raise ValidationError(
            "Receba documentos com texto de referência suportado antes de analisar."
        )
    return tuple(
        LiteralLine(f"d{index}_l{number}", document.id, number, text, document.role)
        for index, document in enumerate(documents, 1)
        for number, text in enumerate(document.reference_text.split("\n"), 1)
    )


def prepare_assisted_analysis(
    documents: tuple[ReferenceDocument, ...],
    labels: dict[str, str],
    abstained: bool,
    *,
    known_amendment: bool,
    decisions: tuple[ContextDecision, ...] = (),
    expected_source: str = "",
    actor: str = "",
    acknowledged: bool = False,
) -> dict:
    lines = literal_lines(documents)
    raw = interpret_lines(lines, labels, abstained=abstained)
    receipt = None
    blockers = [item["code"] for item in raw.blockers]
    if decisions:
        receipt = review_retention(
            lines,
            labels,
            decisions=decisions,
            expected_source=expected_source,
            actor=actor,
            acknowledged=acknowledged,
            known_amendment=known_amendment,
            abstained=abstained,
        )
        blockers = [item["code"] for item in receipt["reviewed"]["blockers"]]
    elif known_amendment:
        blockers.append("known_amendment_history")
    if raw.abstained:
        blockers.append("incomplete_analysis")
    evidence = {}
    for index, item in enumerate((*raw.facts, *raw.blockers)):
        source = item["evidence"]
        document = next(d for d in documents if d.id == source["document_id"])
        located = locate_evidence(
            EvidenceInput(
                document.position, source["start_line"], source["end_line"], source["quote"]
            ),
            documents,
        )
        key = item.get("field", "blocker")
        evidence[key if key not in evidence else f"source_{index}"] = located
    endings = [item for item in raw.facts if item["field"] == "end_date"]
    notices = [item for item in raw.facts if item["field"] == "notice_rule"]
    end = date.fromisoformat(endings[0]["value"]) if endings else None
    days = notices[0]["value"]["days"] if notices else None
    candidates = []
    if not blockers and end is not None:
        candidates.append({"kind": "termination", "date": end.isoformat()})
        if days is not None:
            candidates.append(
                {
                    "kind": "non_renewal_notice",
                    "date": calculate_notice_date(end, days).isoformat(),
                }
            )
    inputs = draft_payload(
        ManualDraft(
            mode="blocked" if blockers else "events" if candidates else "empty",
            end_date=end,
            notice_days=days,
        )
    )
    payload = {
        "input": inputs,
        "evidence": evidence,
        "candidate_events": candidates,
        "blockers": list(dict.fromkeys(blockers)),
        "method_version": METHOD_VERSION,
        "rule_version": RULE_VERSION,
        "extraction": {
            "classifications": dict(labels),
            "abstained": abstained,
            "original": asdict(raw),
            "context_review": receipt,
            "review_input": {
                "decisions": [asdict(item) for item in decisions],
                "expected_source": expected_source,
                "actor": actor if decisions else "",
                "acknowledged": acknowledged if decisions else False,
            },
        },
    }
    return json.loads(json.dumps(payload, ensure_ascii=False))


def restore_context(payload: dict) -> dict:
    data = payload["extraction"]["review_input"]
    return {
        **data,
        "decisions": tuple(ContextDecision(**item) for item in data["decisions"]),
    }
