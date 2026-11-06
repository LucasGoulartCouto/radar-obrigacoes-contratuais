"""Revisão offline de uma observação preservada; sem inferência, banco ou confirmação."""

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from radar_contratos.domain.extraction_review import (
    ContextDecision,
    review_retention,
    source_fingerprint,
)
from radar_contratos.errors import RadarError, StaleRecordError, ValidationError
from radar_contratos.infrastructure.experiments import extraction, line_local_ai
from radar_contratos.infrastructure.experiments.extraction import Proposal, proposed_events


def load_observation(report_path: Path, catalog_path: Path, case_id: str) -> dict:
    report_bytes, catalog_bytes = report_path.read_bytes(), catalog_path.read_bytes()
    report = json.loads(report_bytes)
    catalog = json.loads(catalog_bytes)
    if (
        report.get("method_version") != line_local_ai.METHOD_VERSION
        or report.get("prompt_version") != line_local_ai.PROMPT_VERSION
        or report.get("interpretation_version") != line_local_ai.INTERPRETATION_VERSION
        or report.get("component_sha256") != line_local_ai.component_hashes()
        or report.get("source_changed_during_run") is not False
        or report.get("catalog_sha256") != hashlib.sha256(catalog_bytes).hexdigest()
        or catalog.get("split") != "development"
    ):
        raise ValidationError("O relatório não corresponde à fonte ativa preservada.")
    expected_paths = {
        document["path"] for case in catalog["cases"] for document in case["documents"]
    }
    if set(report["document_sha256"]) != expected_paths:
        raise ValidationError("O relatório não identifica todo o conjunto documental.")
    for relative, digest in report["document_sha256"].items():
        path = (catalog_path.parent / relative).resolve()
        if not path.is_relative_to(catalog_path.parent.resolve()):
            raise ValidationError("Documento fora do conjunto de desenvolvimento.")
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValidationError("Os documentos mudaram desde a rodada preservada.")
    cases = [case for case in catalog["cases"] if case["id"] == case_id]
    observations = [item for item in report["observations"] if item["case_id"] == case_id]
    if len(cases) != 1 or len(observations) != 1 or observations[0].get("ok") is not True:
        raise ValidationError("O caso não possui uma única observação concluída.")
    case, observation = cases[0], observations[0]
    # Não usar fatos/gabaritos como entrada da revisão: reconstruir pela origem + labels.
    documents = extraction.load_documents(case, catalog_path.parent)
    lines = line_local_ai.source_lines(documents)
    return {
        "lines": lines,
        "labels": observation["classifications"],
        "abstained": observation["model_abstained"],
        "report_sha256": hashlib.sha256(report_bytes).hexdigest(),
        "case_id": case_id,
    }


def make_receipt(source: dict, plan: dict) -> dict:
    if set(plan) != {
        "case_id",
        "expected_source",
        "expected_report",
        "actor",
        "acknowledged",
        "known_amendment",
        "decisions",
    }:
        raise ValidationError("O plano de revisão possui campos ausentes ou desconhecidos.")
    if plan["case_id"] != source["case_id"] or plan["expected_report"] != source["report_sha256"]:
        raise StaleRecordError("O plano não corresponde à observação aberta.")
    if not isinstance(plan["decisions"], list):
        raise ValidationError("Informe a lista de decisões de contexto.")
    try:
        decisions = tuple(ContextDecision(**item) for item in plan["decisions"])
    except TypeError as exc:
        raise ValidationError("Cada decisão exige alias, disposition, quote e reason.") from exc
    receipt = review_retention(
        source["lines"],
        source["labels"],
        decisions=decisions,
        expected_source=plan["expected_source"],
        actor=plan["actor"],
        acknowledged=plan["acknowledged"],
        known_amendment=plan["known_amendment"],
        abstained=source["abstained"],
    )
    before, after = receipt["original"], receipt["reviewed"]
    receipt.update(
        {
            "case_id": plan["case_id"],
            "report_sha256": source["report_sha256"],
            "created_at_utc": datetime.now(UTC).isoformat(),
            "original_candidates": proposed_events(
                Proposal(tuple(before["facts"]), tuple(before["blockers"]), before["abstained"])
            ),
            "reviewed_candidates": proposed_events(
                Proposal(tuple(after["facts"]), tuple(after["blockers"]), after["abstained"])
            ),
            "integrated_with_application": False,
            "new_inference_requests": 0,
        }
    )
    return receipt


def write_receipt(path: Path, receipt: dict) -> None:
    # Serializar antes de reservar. Interrupção após a abertura preserva arquivo incompleto;
    # execução seguinte não sobrescreve esse arquivo nem o toma como revisão concluída.
    encoded = json.dumps(receipt, ensure_ascii=False, indent=2) + "\n"
    with path.open("x", encoding="utf-8", newline="\n") as file:
        file.write(encoded)


def main() -> None:
    parser = argparse.ArgumentParser(description="Revisar retenções de contexto offline")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if bool(args.plan) != bool(args.output):
        parser.error("Use --plan e --output juntos, ou omita ambos para inspecionar a origem.")
    try:
        source = load_observation(args.report, args.catalog, args.case_id)
        if args.plan:
            plan = json.loads(args.plan.read_text(encoding="utf-8"))
            if not isinstance(plan, dict) or plan.get("case_id") != args.case_id:
                raise ValidationError("O plano não pertence ao caso aberto.")
            receipt = make_receipt(source, plan)
            write_receipt(args.output, receipt)
            print(
                json.dumps({"confirmed": False, "blocked": bool(receipt["reviewed"]["blockers"])})
            )
        else:
            # known_amendment é declaração explícita no plano, nunca inferida do relatório.
            print(
                json.dumps(
                    {
                        "case_id": args.case_id,
                        "report_sha256": source["report_sha256"],
                        "source_without_known_amendment": source_fingerprint(
                            source["lines"],
                            source["labels"],
                            abstained=source["abstained"],
                            known_amendment=False,
                        ),
                        "source_with_known_amendment": source_fingerprint(
                            source["lines"],
                            source["labels"],
                            abstained=source["abstained"],
                            known_amendment=True,
                        ),
                    }
                )
            )
    except OSError, ValueError, KeyError, TypeError, RadarError:
        parser.exit(1, "Revisão não concluída; confira origem, plano e destino novo.\n")


if __name__ == "__main__":
    main()
