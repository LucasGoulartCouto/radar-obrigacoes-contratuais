"""Revisão restrita de retenções; não muda a extração original nem confirma eventos."""

import hashlib
import json
import re
from dataclasses import asdict, dataclass

from radar_contratos.domain.literal_extraction import (
    INTERPRETATION_VERSION,
    LiteralLine,
    interpret_lines,
    line_evidence,
)
from radar_contratos.domain.reviews import RULE_VERSION
from radar_contratos.errors import StaleRecordError, ValidationError

REVIEW_VERSION = "RETAINED_CONTEXT_REVIEW_V1"
# O recorte só admite instrução ao assistente sem conteúdo contratual misturado.
CONTRACT_CONTENT = re.compile(
    r"[0-9]|términ|termin|vigência|renova|antecedência|aditivo|cláusula|contrat",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class ContextDecision:
    alias: str
    disposition: str
    quote: str
    reason: str


def _digest(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _source_payload(lines, labels, abstained, known_amendment) -> dict:
    if type(known_amendment) is not bool:
        raise ValidationError("Informe explicitamente o estado de aditivo conhecido.")
    if (
        not isinstance(lines, tuple)
        or not lines
        or any(
            not isinstance(line, LiteralLine)
            or not isinstance(line.document_id, str)
            or not isinstance(line.role, str)
            for line in lines
        )
    ):
        raise ValidationError("Informe as linhas completas da origem.")
    for document_id in {line.document_id for line in lines}:
        selected = [line for line in lines if line.document_id == document_id]
        if [line.number for line in selected] != list(range(1, len(selected) + 1)) or len(
            {line.role for line in selected}
        ) != 1:
            raise ValidationError(
                "A revisão exige todas as linhas na ordem original e papel único."
            )
    # Revalidar cobertura/valores na origem, nunca confiar numa proposta fornecida.
    interpret_lines(lines, labels, abstained=abstained)
    return {
        "lines": [asdict(line) for line in lines],
        "classifications": dict(labels),
        "model_abstained": abstained,
        "known_amendment": known_amendment,
        "interpretation_version": INTERPRETATION_VERSION,
        "review_version": REVIEW_VERSION,
        "rule_version": RULE_VERSION,
    }


def source_fingerprint(
    lines: tuple[LiteralLine, ...],
    labels: dict[str, str],
    *,
    abstained: bool = False,
    known_amendment: bool,
) -> str:
    return _digest(_source_payload(lines, labels, abstained, known_amendment))


def _supported_decision(decision, line, lines, findings) -> bool:
    reasons = {f["reason"] for f in findings if f.get("line") == line.alias}
    if decision.disposition == "untrusted_instruction":
        return (
            reasons == {"model_reports_unsupported"}
            and line.text.casefold().startswith("instrução ao assistente:")
            and not CONTRACT_CONTENT.search(line.text)
        )
    if decision.disposition == "illustrative":
        prior = next(
            (
                item
                for item in reversed(lines)
                if item.document_id == line.document_id
                and item.number < line.number
                and item.text.strip()
            ),
            None,
        )
        return (
            reasons == {"clause_inside_illustration"}
            and prior is not None
            and "exemplo" in prior.text.casefold()
            and "não define" in prior.text.casefold()
            and prior.text.rstrip().endswith(":")
        )
    return False


def review_retention(
    lines: tuple[LiteralLine, ...],
    labels: dict[str, str],
    *,
    decisions: tuple[ContextDecision, ...],
    expected_source: str,
    actor: str,
    acknowledged: bool,
    known_amendment: bool,
    abstained: bool = False,
) -> dict:
    source = _source_payload(lines, labels, abstained, known_amendment)
    source_hash = _digest(source)
    if expected_source != source_hash:
        raise StaleRecordError("A origem ou o método mudou. Reabra a retenção antes de revisar.")
    if acknowledged is not True:
        raise ValidationError(
            "Declare a conferência do texto completo e do contexto das retenções."
        )
    if (
        not isinstance(actor, str)
        or not actor.strip()
        or len(actor.strip()) > 80
        or any(ord(char) < 32 for char in actor)
    ):
        raise ValidationError("Identifique o responsável simulado em até 80 caracteres.")
    if not isinstance(decisions, tuple) or any(
        not isinstance(item, ContextDecision)
        or not isinstance(item.alias, str)
        or not isinstance(item.disposition, str)
        or not isinstance(item.reason, str)
        or not item.reason.strip()
        or len(item.reason.strip()) > 500
        or any(ord(char) < 32 for char in item.reason)
        for item in decisions
    ):
        raise ValidationError("Cada decisão exige linha, tratamento e justificativa explícita.")
    if len({item.alias for item in decisions}) != len(decisions):
        raise ValidationError("Uma linha não pode receber decisões repetidas.")
    raw = interpret_lines(lines, labels, abstained=abstained)
    if abstained:
        raise ValidationError("Abstenção exige nova análise; não pode ser resolvida como contexto.")
    resolved, records = set(), []
    for decision in decisions:
        line = next((item for item in lines if item.alias == decision.alias), None)
        if (
            line is None
            or line.role != "base"
            or decision.quote != line.text
            or not _supported_decision(decision, line, lines, raw.findings)
        ):
            raise ValidationError("A decisão não resolve uma retenção de contexto suportada.")
        resolved.add(line.alias)
        records.append(
            {
                "alias": line.alias,
                "original_label": labels[line.alias],
                "disposition": decision.disposition,
                "reason": decision.reason.strip(),
                "evidence": line_evidence(line),
            }
        )
    unresolved = [
        finding
        for finding in raw.findings
        if finding["code"] == "unsupported_scope" and finding.get("line") not in resolved
    ]
    blockers = [blocker for blocker in raw.blockers if blocker["code"] != "unsupported_scope"]
    pending_aliases = {finding["line"] for finding in unresolved}
    blockers.extend(
        {"code": "unsupported_scope", "evidence": line_evidence(line)}
        for line in lines
        if line.alias in pending_aliases
    )
    if known_amendment:
        blockers.append({"code": "known_amendment_history", "evidence": None})
    return {
        "source_sha256": source_hash,
        "source": source,
        "actor": actor.strip(),
        "acknowledged": True,
        "original": asdict(raw),
        "decisions": records,
        "reviewed": {
            "facts": list(raw.facts),
            "blockers": blockers,
            "abstained": raw.abstained,
        },
        "confirmed": False,
        "review_scope": "simulação de revisão de contexto; não é aprovação de Lucas",
    }
