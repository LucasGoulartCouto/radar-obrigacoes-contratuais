"""Fronteira de arquivos e CLI offline; não exercita banco, runtime ou revisão humana real."""

import hashlib
import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import pytest

from radar_contratos.domain.extraction_review import ContextDecision, source_fingerprint
from radar_contratos.errors import ValidationError
from radar_contratos.infrastructure.experiments.retention_review import (
    load_observation,
    write_receipt,
)

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs/evidencias/ia-local-linhas-v1.json"
CATALOG = ROOT / "tests/fixtures/contracts/development/cases.json"


def run_cli(*arguments):
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "radar_contratos.infrastructure.experiments.retention_review",
            "--report",
            str(REPORT),
            "--catalog",
            str(CATALOG),
            "--case-id",
            "DEV-008",
            *arguments,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=15,
    )


def test_cli_inspection_review_and_repetition_do_not_overwrite_or_confirm(tmp_path):
    inspection = run_cli()
    assert inspection.returncode == 0
    inspected = json.loads(inspection.stdout)
    source = load_observation(REPORT, CATALOG, "DEV-008")
    plan = {
        "case_id": "DEV-008",
        "expected_report": inspected["report_sha256"],
        "expected_source": inspected["source_without_known_amendment"],
        "actor": "Marina - simulação pelo agente",
        "acknowledged": True,
        "known_amendment": False,
        "decisions": [
            asdict(
                ContextDecision(
                    "d1_l7",
                    "untrusted_instruction",
                    source["lines"][6].text,
                    "Pedido ao assistente sem autoridade; conferência simulada do contexto.",
                )
            )
        ],
    }
    plan_path, output = tmp_path / "plan.json", tmp_path / "receipt.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    arguments = ["--plan", str(plan_path), "--output", str(output)]
    result = run_cli(*arguments)
    assert result.returncode == 0
    assert json.loads(result.stdout) == {"confirmed": False, "blocked": False}
    receipt = json.loads(output.read_text(encoding="utf-8"))
    assert receipt["original_candidates"] == []
    assert len(receipt["reviewed_candidates"]) == 2
    assert receipt["new_inference_requests"] == 0
    assert receipt["integrated_with_application"] is False
    assert receipt["source_sha256"] == source_fingerprint(
        source["lines"],
        source["labels"],
        known_amendment=False,
    )
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    assert run_cli(*arguments).returncode == 1
    assert hashlib.sha256(output.read_bytes()).hexdigest() == digest
    # Um parcial já existente é preservado, não usado como recibo concluído.
    partial = tmp_path / "interrupted.json"
    partial.write_bytes(b'{"source":')
    assert run_cli("--plan", str(plan_path), "--output", str(partial)).returncode == 1
    assert partial.read_bytes() == b'{"source":'


def test_invalid_plan_and_missing_output_are_rejected_without_writing(tmp_path):
    plan, output = tmp_path / "bad.json", tmp_path / "receipt.json"
    plan.write_text('{"case_id":"DEV-020"}', encoding="utf-8")
    assert run_cli("--plan", str(plan), "--output", str(output)).returncode == 1
    assert not output.exists()
    assert run_cli("--plan", str(plan)).returncode == 2


@pytest.mark.parametrize("fault", ["catalog", "component", "documents", "partial", "duplicate"])
def test_observation_loader_rejects_mismatched_or_incomplete_evidence(tmp_path, fault):
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    if fault == "catalog":
        report["catalog_sha256"] = "0" * 64
    elif fault == "component":
        report["component_sha256"]["literal_extraction.py"] = "0" * 64
    elif fault == "documents":
        report["document_sha256"] = {}
    elif fault == "partial":
        report["observations"][7]["ok"] = False
    else:
        report["observations"].append(report["observations"][7])
    path = tmp_path / "report.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ValidationError):
        load_observation(path, CATALOG, "DEV-008")


def test_receipt_serialization_failure_does_not_create_result(tmp_path):
    output = tmp_path / "receipt.json"
    with pytest.raises(TypeError):
        write_receipt(output, {"invalid": object()})
    assert not output.exists()
