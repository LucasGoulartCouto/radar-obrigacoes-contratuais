"""Interpretação literal experimental; não comprova suporte semântico nem confirma."""

import re
from dataclasses import dataclass
from datetime import datetime

from radar_contratos.errors import ValidationError

INTERPRETATION_VERSION = "LITERAL_CLAUSES_V1"
KINDS = frozenset(
    {
        "context",
        "termination",
        "notice",
        "termination_and_notice",
        "amendment",
        "illustrative",
        "no_event",
        "unsupported",
    }
)
DATE = re.compile(r"(?<![0-9])([0-9]{2}/[0-9]{2}/[0-9]{4})(?![0-9])")
DURATION = re.compile(
    r"(?<![\w+.,-])(?P<amount>[+-]?[0-9]+(?:[,.][0-9]+)?"
    r"(?:\s*\([^()\n]+\))?)\s+(?P<unit>dias?\s+corridos?|dias?\s+úteis|dias?|meses?|anos?)\b",
    re.IGNORECASE,
)
SIGNAL = re.compile(r"término|termina|vigência|renova|antecedência|aditivo|aviso", re.IGNORECASE)
NEGATIVE = re.compile(r"^(?:não há|não existe|não é exigido|nenhum[ao]?\b)", re.IGNORECASE)
METADATA = re.compile(
    r"^(?:DOCUMENTO SINTÉTICO|Serviço fictício:|Contratante fictícia:|Fornecedor fictício:)",
    re.IGNORECASE,
)
ANCHORS = ("em relação à data de término", "antes do término")
AFFIRMATIVE_AMENDMENT = re.compile(
    r"^(?:aditivo\s+ao|este\s+(?:instrumento|documento)\s+(?:é|constitui)\s+(?:um\s+)?aditivo)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class LiteralLine:
    alias: str
    document_id: str
    number: int
    text: str
    role: str


@dataclass(frozen=True, slots=True)
class LiteralResult:
    facts: tuple[dict, ...]
    blockers: tuple[dict, ...]
    abstained: bool
    findings: tuple[dict, ...]


def line_evidence(line: LiteralLine) -> dict:
    return {
        "document_id": line.document_id,
        "start_line": line.number,
        "end_line": line.number,
        "quote": line.text,
    }


def _span(first: LiteralLine, last: LiteralLine, lines: tuple[LiteralLine, ...]) -> dict:
    selected = {
        source_line.number: source_line.text
        for source_line in lines
        if source_line.document_id == first.document_id
    }
    return {
        "document_id": first.document_id,
        "start_line": first.number,
        "end_line": last.number,
        "quote": "\n".join(selected[n] for n in range(first.number, last.number + 1)),
    }


def _written_number(text: str) -> int | None:
    units = ["zero", "um", "dois", "três", "quatro", "cinco", "seis", "sete", "oito", "nove"]
    teens = [
        "dez",
        "onze",
        "doze",
        "treze",
        "quatorze",
        "quinze",
        "dezesseis",
        "dezessete",
        "dezoito",
        "dezenove",
    ]
    words = {word: i for i, word in enumerate(units + teens)}
    for tens, word in enumerate(
        ["vinte", "trinta", "quarenta", "cinquenta", "sessenta", "setenta", "oitenta", "noventa"],
        2,
    ):
        words[word] = tens * 10
        words.update({f"{word} e {unit}": tens * 10 + n for n, unit in enumerate(units) if n})
    words["cem"] = 100
    return words.get(text.strip().casefold())


def interpret_lines(
    lines: tuple[LiteralLine, ...],
    labels: dict[str, str],
    *,
    abstained: bool = False,
) -> LiteralResult:
    if (
        any(
            not isinstance(line, LiteralLine)
            or type(line.number) is not int
            or line.number < 1
            or not isinstance(line.text, str)
            or not isinstance(line.alias, str)
            or not line.alias
            or not isinstance(line.document_id, str)
            or not line.document_id
            or not isinstance(line.role, str)
            or line.role not in {"base", "aditivo", "substituição", "desconhecido"}
            for line in lines
        )
        or len({source_line.alias for source_line in lines}) != len(lines)
        or len({(source_line.document_id, source_line.number) for source_line in lines})
        != len(lines)
    ):
        raise ValidationError("A origem das linhas é inválida ou repetida.")
    expected = {line.alias for line in lines if line.text.strip()}
    if not expected:
        raise ValidationError("Sem documentos legíveis não existe análise vazia concluída.")
    if (
        not isinstance(labels, dict)
        or set(labels) != expected
        or type(abstained) is not bool
        or any(not isinstance(v, str) or v not in KINDS for v in labels.values())
    ):
        raise ValidationError("A classificação deve cobrir exatamente todas as linhas não vazias.")
    facts, blockers, findings = [], [], []

    def block(code, line, reason):
        if code not in {b["code"] for b in blockers}:
            blockers.append({"code": code, "evidence": line_evidence(line)})
        findings.append({"code": code, "line": line.alias, "reason": reason})

    # Papel declarado é metadado: não delegar ao modelo sua remoção.
    for line in lines:
        if line.role == "aditivo" and line.text.strip():
            source = next(
                (
                    source_line
                    for source_line in lines
                    if source_line.document_id == line.document_id
                    and re.search(r"\baditivo\b", source_line.text, re.IGNORECASE)
                ),
                line,
            )
            block("amendment_not_supported", source, "declared_amendment")
            break
    for line in lines:
        if AFFIRMATIVE_AMENDMENT.search(line.text):
            block("amendment_not_supported", line, "explicit_textual_amendment")
    if abstained:
        if blockers:
            findings.append({"code": "model_abstained", "reason": "known_blocker_has_priority"})
        return LiteralResult((), tuple(blockers), not bool(blockers), tuple(findings))
    for line in lines:
        if not line.text.strip():
            continue
        kind = labels[line.alias]
        lower = line.text.casefold()
        prior = next(
            (
                source_line
                for source_line in reversed(lines)
                if source_line.document_id == line.document_id
                and source_line.number < line.number
                and source_line.text.strip()
            ),
            None,
        )
        illustrative_context = (
            ("exemplo" in lower and "não define" in lower)
            or prior is not None
            and "exemplo" in prior.text.casefold()
            and "não define" in prior.text.casefold()
        )
        has_signal = bool(SIGNAL.search(line.text) or DATE.search(line.text))
        metadata = bool(METADATA.search(line.text))
        metadata = metadata and not (DATE.search(line.text) or DURATION.search(line.text))
        negative = bool(NEGATIVE.search(line.text)) and not DATE.search(line.text)
        # Negação explícita é só uma classificação de ausência; ainda exige conferência.
        if kind == "no_event":
            if not negative:
                block("unsupported_scope", line, "absence_without_explicit_negation")
            continue
        if kind == "illustrative":
            if not illustrative_context and has_signal:
                block("unsupported_scope", line, "unverified_illustration")
            continue
        if kind == "unsupported":
            block("unsupported_scope", line, "model_reports_unsupported")
            continue
        if illustrative_context and kind in {"termination", "notice", "termination_and_notice"}:
            block("unsupported_scope", line, "clause_inside_illustration")
            continue
        if kind == "context":
            # Datas de pagamento são explicitamente fora do recorte, sem inferir término.
            outside = (
                lower.startswith("data de pagamento")
                or "exemplo" in lower
                and "não define" in lower
                and not DATE.search(line.text)
            )
            if (
                has_signal
                and not metadata
                and not outside
                and not AFFIRMATIVE_AMENDMENT.search(line.text)
            ):
                block("unsupported_scope", line, "relevant_line_classified_as_context")
            continue
        if kind == "amendment":
            if "aditivo" not in lower and line.role != "aditivo":
                block("unsupported_scope", line, "amendment_without_support")
                continue
            block("amendment_not_supported", line, "amendment_line")
        if kind in {"termination", "termination_and_notice", "amendment"}:
            matches = list(DATE.finditer(line.text))
            if not matches and kind != "amendment":
                block("unsupported_scope", line, "termination_without_literal_date")
            if matches and not re.search(
                r"término|termina|vigência|encerr|finda|fim do ciclo", line.text, re.IGNORECASE
            ):
                block("unsupported_scope", line, "date_without_end_scope")
                matches = []
            for match in matches:
                try:
                    value = datetime.strptime(match[1], "%d/%m/%Y").date().isoformat()
                except ValueError:
                    block("invalid_end_date", line, "invalid_literal_date")
                else:
                    field = (
                        "amendment_end_date"
                        if kind == "amendment" or line.role == "aditivo"
                        else "end_date"
                    )
                    facts.append({"field": field, "value": value, "evidence": line_evidence(line)})
        if kind not in {"notice", "termination_and_notice"}:
            continue
        matches = list(DURATION.finditer(line.text))
        if not matches:
            block("unsupported_scope", line, "notice_without_literal_duration")
            continue
        for match in matches:
            amount, unit = match["amount"], " ".join(match["unit"].casefold().split())
            if "(" in amount:
                digits, written = amount.split("(", 1)
                written_value = _written_number(written.rstrip(")"))
                if written_value is None:
                    block("unsupported_scope", line, "written_number_not_supported")
                    continue
                if not digits.strip().isdecimal() or int(digits) != written_value:
                    block("conflicting_notice_days", line, "written_number_conflicts")
                    continue
                amount = digits.strip()
            if not amount.lstrip("+").isdecimal():
                block("invalid_notice_days", line, "negative_or_fractional_duration")
                continue
            if unit not in {"dia", "dias", "dia corrido", "dias corridos"}:
                block("unsupported_day_unit", line, "unit_not_calendar_days")
                continue
            if not any(anchor in lower for anchor in ANCHORS):
                block("unsupported_anchor", line, "anchor_not_explicitly_supported")
                continue
            normalized_unit = "calendar_days" if "corrido" in unit else None
            facts.append(
                {
                    "field": "notice_rule",
                    "value": {"days": int(amount), "unit": normalized_unit, "anchor": "end_date"},
                    "evidence": line_evidence(line),
                }
            )
            if normalized_unit is None:
                block("undefined_day_unit", line, "calendar_unit_not_explicit")
    endings = [f for f in facts if f["field"] == "end_date"]
    if len({f["value"] for f in endings}) > 1:
        sources = [
            source_line
            for source_line in lines
            if any(
                f["evidence"]["document_id"] == source_line.document_id
                and f["evidence"]["start_line"] == source_line.number
                for f in endings
            )
        ]
        first, last = sources[0], sources[-1]
        block("conflicting_end_dates", first, "distinct_literal_end_dates")
        if first.document_id == last.document_id:
            next(b for b in blockers if b["code"] == "conflicting_end_dates")["evidence"] = _span(
                first, last, lines
            )
    rules = [f for f in facts if f["field"] == "notice_rule"]
    if rules and not endings:
        source = next(
            source_line
            for source_line in lines
            if source_line.alias in labels
            and labels[source_line.alias] in {"notice", "termination_and_notice"}
        )
        block("unsupported_anchor", source, "notice_without_explicit_end_date")
    if len({(f["value"]["days"], f["value"]["unit"]) for f in rules}) > 1:
        source = next(
            source_line
            for source_line in lines
            if source_line.alias in labels
            and labels[source_line.alias] in {"notice", "termination_and_notice"}
        )
        block("conflicting_notice_days", source, "distinct_literal_notice_rules")
    # Repetição idêntica não cria dois avisos nem apaga as fontes da observação.
    canonical_rules, selected = set(), []
    for fact in facts:
        if fact["field"] == "notice_rule":
            key = (fact["value"]["days"], fact["value"]["unit"])
            if key in canonical_rules:
                findings.append(
                    {
                        "code": "repeated_notice",
                        "evidence": fact["evidence"],
                        "reason": "same_rule_additional_source",
                    }
                )
                continue
            canonical_rules.add(key)
        selected.append(fact)
    return LiteralResult(tuple(selected), tuple(blockers), False, tuple(findings))
