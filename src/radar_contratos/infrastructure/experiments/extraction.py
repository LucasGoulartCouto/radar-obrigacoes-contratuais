"""Baseline e avaliação offline. Não acessa banco, rede, UI ou confirmações."""

import argparse
import hashlib
import json
import re
import statistics
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from time import perf_counter_ns

from radar_contratos.domain.dates import calculate_notice_date
from radar_contratos.domain.documents import DocumentInput, DocumentLimits, DocumentRole
from radar_contratos.domain.documents import prepare_documents as prepare_inputs
from radar_contratos.errors import ValidationError

METHOD_VERSION = "REGEX_EXPERIMENT_V1"
END = re.compile(
    r"(?:Término do ciclo informado: |Cláusula [0-9]+: o (?:mesmo )?ciclo informado termina em )"
    r"([0-9]{2}/[0-9]{2}/[0-9]{4})\."
)
NOTICE = re.compile(
    r"Para não renovar, (?:a contratante deverá comunicar sua decisão com |"
    r"o aviso tem antecedência expressa de )([+-]?[0-9]+(?:[,.][0-9]+)?) "
    r"(dia corrido|dias corridos|dias|dia) (?:de antecedência )?"
    r"em relação à data de término\."
)


@dataclass(frozen=True)
class ExperimentDocument:
    id: str
    role: str
    text: str


@dataclass(frozen=True)
class Proposal:
    facts: tuple[dict, ...]
    blockers: tuple[dict, ...] = ()
    abstained: bool = False


def evidence(document: ExperimentDocument, start: int, end: int | None = None) -> dict:
    end = start if end is None else end
    return {
        "document_id": document.id,
        "start_line": start,
        "end_line": end,
        "quote": "\n".join(document.text.split("\n")[start - 1 : end]),
    }


def extract_rules(documents: tuple[ExperimentDocument, ...]) -> Proposal:
    """Reconhece gramáticas explícitas; saída parcial nunca autoriza conferência."""
    facts, blockers = [], []
    for document in documents:
        if document.role == "aditivo":
            number = next(
                (
                    i
                    for i, line in enumerate(document.text.split("\n"), 1)
                    if line.startswith("ADITIVO")
                ),
                1,
            )
            blockers.append(
                {
                    "code": "amendment_not_supported",
                    "evidence": evidence(document, number),
                }
            )
            continue
        for number, line in enumerate(document.text.split("\n"), 1):
            source = evidence(document, number)
            if match := END.fullmatch(line):
                try:
                    value = datetime.strptime(match[1], "%d/%m/%Y").date().isoformat()
                except ValueError:
                    blockers.append({"code": "invalid_end_date", "evidence": source})
                else:
                    facts.append({"field": "end_date", "value": value, "evidence": source})
            elif match := NOTICE.fullmatch(line):
                raw, unit = match.groups()
                if not raw.isdecimal():
                    blockers.append({"code": "invalid_notice_days", "evidence": source})
                    continue
                days = int(raw)
                normalized_unit = "calendar_days" if "corrido" in unit else None
                facts.append(
                    {
                        "field": "notice_rule",
                        "value": {"days": days, "unit": normalized_unit, "anchor": "end_date"},
                        "evidence": source,
                    }
                )
                if normalized_unit is None:
                    blockers.append({"code": "undefined_day_unit", "evidence": source})
    endings = [f for f in facts if f["field"] == "end_date"]
    if len({f["value"] for f in endings}) > 1:
        first, last = endings[0]["evidence"], endings[-1]["evidence"]
        # Para conflitos entre documentos, uma evidência literal de cada afirmação.
        if first["document_id"] == last["document_id"]:
            document = next(d for d in documents if d.id == first["document_id"])
            source = evidence(document, first["start_line"], last["end_line"])
        else:
            source = first
        blockers.append({"code": "conflicting_end_dates", "evidence": source})
    rules = [f for f in facts if f["field"] == "notice_rule"]
    if len({json.dumps(f["value"], sort_keys=True) for f in rules}) > 1:
        blockers.append({"code": "conflicting_notice_days", "evidence": rules[0]["evidence"]})
    return Proposal(tuple(facts), tuple(blockers), abstained=not facts and not blockers)


def literal_evidence_valid(item: dict, documents: tuple[ExperimentDocument, ...]) -> bool:
    if not isinstance(item, dict):
        return False
    document = next((d for d in documents if d.id == item.get("document_id")), None)
    start, end = item.get("start_line"), item.get("end_line")
    if document is None or type(start) is not int or type(end) is not int:
        return False
    lines = document.text.split("\n")
    quote = item.get("quote")
    return (
        1 <= start <= end <= len(lines)
        and isinstance(quote, str)
        and bool(quote.strip())
        and "\n".join(lines[start - 1 : end]) == quote
    )


def _fact_key(fact: dict) -> str:
    # Correspondência estrita ao gabarito, incluindo suporte anotado.
    return json.dumps(fact, sort_keys=True, ensure_ascii=False)


def _counts(predicted: Counter, expected: Counter) -> dict:
    tp = sum((predicted & expected).values())
    return {"tp": tp, "fp": sum(predicted.values()) - tp, "fn": sum(expected.values()) - tp}


def proposed_events(proposal: Proposal) -> list[dict]:
    if proposal.blockers or proposal.abstained:
        return []
    endings = {f["value"] for f in proposal.facts if f["field"] == "end_date"}
    rules = [f["value"] for f in proposal.facts if f["field"] == "notice_rule"]
    if len(endings) != 1 or len(rules) > 1:
        return []
    end = date.fromisoformat(next(iter(endings)))
    events = [{"kind": "termination", "date": end.isoformat()}]
    if rules:
        rule = rules[0]
        if rule["unit"] != "calendar_days" or rule["anchor"] != "end_date":
            return []
        events.append(
            {
                "kind": "non_renewal_notice",
                "date": calculate_notice_date(end, rule["days"]).isoformat(),
            }
        )
    return events


def score_proposal(
    proposal: Proposal, case: dict, documents: tuple[ExperimentDocument, ...]
) -> dict:
    if not isinstance(proposal, Proposal) or (
        proposal.abstained and (proposal.facts or proposal.blockers)
    ):
        raise ValueError("Saída experimental inconsistente.")
    valid = [f for f in proposal.facts if literal_evidence_valid(f.get("evidence"), documents)]
    fact_counts = _counts(
        Counter(_fact_key(f) for f in valid), Counter(_fact_key(f) for f in case["facts"])
    )
    # Evidência inválida é erro, mesmo quando o valor coincide com o esperado.
    fact_counts["fp"] += len(proposal.facts) - len(valid)
    expected_blockers = {_fact_key(b) for b in case["blockers"]}
    supported_blockers = [
        b
        for b in proposal.blockers
        if literal_evidence_valid(b.get("evidence"), documents)
        and _fact_key(b) in expected_blockers
    ]
    actual_codes = {b["code"] for b in supported_blockers}
    unsupported_codes = {b["code"] for b in proposal.blockers if b not in supported_blockers}
    expected_codes = {b["code"] for b in case["blockers"]}
    candidates = proposed_events(proposal) if len(valid) == len(proposal.facts) else []
    expected_events = [
        {"kind": e["kind"], "date": e["date"]} for e in case["expected"]["candidate_events"]
    ]
    event_counts = _counts(
        Counter(json.dumps(e, sort_keys=True) for e in candidates),
        Counter(json.dumps(e, sort_keys=True) for e in expected_events),
    )
    missing = sorted(expected_codes - actual_codes)
    invalid_evidence = sum(
        not literal_evidence_valid(item.get("evidence"), documents)
        for item in (*proposal.facts, *proposal.blockers)
    )
    return {
        "id": case["id"],
        "abstained": proposal.abstained,
        "facts": fact_counts,
        "events": event_counts,
        "blockers_missing": missing,
        "blockers_extra": sorted((actual_codes - expected_codes) | unsupported_codes),
        "invalid_evidence": invalid_evidence,
        "exact_case": (
            fact_counts["fp"] == fact_counts["fn"] == event_counts["fp"] == event_counts["fn"] == 0
            and actual_codes == expected_codes
            and not unsupported_codes
            and not proposal.abstained
            and invalid_evidence == 0
        ),
        # Resultado vazio do método é abstenção; nunca prova ausência de eventos.
        "expected_empty": not case["facts"] and not case["blockers"],
    }


def load_documents(case: dict, directory: Path) -> tuple[ExperimentDocument, ...]:
    paths = [(directory / d["path"]).resolve() for d in case["documents"]]
    if any(not p.is_relative_to(directory.resolve()) for p in paths):
        raise ValueError("Documento fora do diretório do conjunto.")
    prepared = prepare_inputs(
        tuple(
            DocumentInput(path.name, path.read_bytes(), DocumentRole(d["role"]))
            for path, d in zip(paths, case["documents"], strict=True)
        ),
        DocumentLimits(),
    )
    return tuple(
        ExperimentDocument(d["id"], d["role"], p.reference_text)
        for d, p in zip(case["documents"], prepared, strict=True)
    )


def evaluate(
    catalog_path: Path,
    extractor: Callable = extract_rules,
    *,
    method_version: str = METHOD_VERSION,
) -> dict:
    raw = catalog_path.read_bytes()
    catalog = json.loads(raw)
    if catalog["split"] != "development":
        raise ValueError("Este comando usa somente desenvolvimento; não abre avaliação reservada.")
    identifiers = [c["id"] for c in catalog["cases"]]
    if not identifiers or len(identifiers) != len(set(identifiers)):
        raise ValueError("O conjunto deve conter casos com IDs únicos.")
    rows, durations, input_hashes = [], [], {}
    for case in catalog["cases"]:
        documents = load_documents(case, catalog_path.parent)
        for d in case["documents"]:
            input_hashes[d["path"]] = hashlib.sha256(
                (catalog_path.parent / d["path"]).read_bytes()
            ).hexdigest()
        start = perf_counter_ns()
        try:
            # Somente documentos chegam ao extrator; ID/gabarito/expectativas ficam no avaliador.
            proposal = extractor(documents)
            row = score_proposal(proposal, case, documents)
        except (
            ValidationError,
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
            OverflowError,
            TimeoutError,
        ) as exc:
            row = {"id": case["id"], "failed": True, "error_type": type(exc).__name__}
        elapsed = (perf_counter_ns() - start) / 1_000_000
        durations.append(elapsed)
        rows.append(row)
    successful = [r for r in rows if not r.get("failed")]
    totals = {
        "cases": len(rows),
        "failed_cases": len(rows) - len(successful),
        "abstained_cases": sum(r["abstained"] for r in successful),
        "exact_cases": sum(r["exact_case"] for r in successful),
        "cases_missing_blockers": sum(bool(r["blockers_missing"]) for r in successful),
        "expected_blocked_cases": sum(bool(c["blockers"]) for c in catalog["cases"]),
        "failed_blocked_cases": sum(
            bool(c["blockers"])
            for c in catalog["cases"]
            if any(r["id"] == c["id"] and r.get("failed") for r in rows)
        ),
        "cases_extra_blockers": sum(bool(r["blockers_extra"]) for r in successful),
        "invalid_evidence": sum(r["invalid_evidence"] for r in successful),
    }
    for kind in ("facts", "events"):
        counts = {key: sum(r[kind][key] for r in successful) for key in ("tp", "fp", "fn")}
        # Falhas não desaparecem dos denominadores de omissão.
        failed_ids = {r["id"] for r in rows if r.get("failed")}
        counts["fn"] += sum(
            len(c["facts"] if kind == "facts" else c["expected"]["candidate_events"])
            for c in catalog["cases"]
            if c["id"] in failed_ids
        )
        counts["precision"] = (
            counts["tp"] / (counts["tp"] + counts["fp"]) if counts["tp"] + counts["fp"] else None
        )
        counts["recall"] = (
            counts["tp"] / (counts["tp"] + counts["fn"]) if counts["tp"] + counts["fn"] else None
        )
        totals[kind] = counts
    return {
        "schema_version": 1,
        "method_version": method_version,
        "method_sha256": (
            hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
            if extractor is extract_rules
            else None
        ),
        "evaluator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "catalog_sha256": hashlib.sha256(raw).hexdigest(),
        "document_sha256": input_hashes,
        "split": catalog["split"],
        "independent_evaluation": False,
        "integrated_with_application": False,
        "api_calls": 0 if extractor is extract_rules else None,
        "api_cost": 0 if extractor is extract_rules else None,
        "totals": totals,
        "timing_ms": {
            "scope": "extração + pontuação; sem leitura de arquivos, confirmação ou esforço humano",
            "median": statistics.median(durations),
            "max": max(durations),
        },
        "cases": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Experimento offline de extração do Radar")
    parser.add_argument(
        "--catalog",
        type=Path,
        default=Path("tests/fixtures/contracts/development/cases.json"),
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = evaluate(args.catalog)
        # Não sobrescrever evidência anterior por acidente; diretório deve existir.
        with args.output.open("x", encoding="utf-8", newline="\n") as output:
            json.dump(report, output, ensure_ascii=False, indent=2)
            output.write("\n")
    except (OSError, ValueError, KeyError, ValidationError) as exc:
        # Não imprimir mensagem arbitrária que possa conter texto documental.
        parser.exit(
            1, f"Experimento não concluído ({type(exc).__name__}). Confira entradas/destino.\n"
        )
    print(json.dumps(report["totals"], ensure_ascii=False))
    if report["totals"]["failed_cases"]:
        parser.exit(1, "Há falhas técnicas; consulte o relatório, sem tratá-las como vazio.\n")


if __name__ == "__main__":
    main()
