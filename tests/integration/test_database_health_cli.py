import hashlib
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pytest


def run_check(data_dir, *args):
    return subprocess.run(
        [sys.executable, "-m", "radar_contratos.cli", "check-db", *args],
        env={**os.environ, "RADAR_DATA_DIR": str(data_dir), "PYTHONIOENCODING": "utf-8"},
        text=True,
        encoding="utf-8",
        capture_output=True,
        timeout=20,
    )


def test_cli_success_preserves_file_and_reports_only_technical_status(engine):
    path = Path(engine.url.database)
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    result = run_check(path.parent)
    assert result.returncode == 0, result.stderr
    assert "Esquema básico: OK" in result.stdout
    assert "somente leitura" in result.stdout
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


def test_cli_missing_database_is_nonzero_without_creation(tmp_path):
    folder = tmp_path / "missing"
    result = run_check(folder)
    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert not folder.exists()


def test_cli_bad_version_does_not_print_untrusted_value_or_migrate(engine):
    path = Path(engine.url.database)
    marker = "PRIVATE_VERSION_MARKER"
    with sqlite3.connect(path) as connection:
        connection.execute("UPDATE alembic_version SET version_num=?", (marker,))
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    result = run_check(path.parent)
    assert result.returncode == 1
    assert "Esquema básico: FALHA" in result.stdout
    assert marker not in result.stdout + result.stderr
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


@pytest.mark.parametrize("kind", ["foreign_key", "check"])
def test_cli_data_violations_fail_without_repair_or_private_details(service, engine, kind):
    path = Path(engine.url.database)
    marker = "PRIVATE_FIXTURE_81"
    if kind == "check":
        service.register(title=marker, actor="Operador", request_id=str(uuid4()))
    with sqlite3.connect(path) as connection:
        if kind == "foreign_key":
            connection.execute("PRAGMA foreign_keys=OFF")
            connection.execute(
                "INSERT INTO operations VALUES (?, ?, ?, ?)", ("orphan", "0" * 64, marker, "{}")
            )
        else:
            connection.execute("PRAGMA ignore_check_constraints=ON")
            connection.execute("UPDATE contracts SET record_version=0")
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    result = run_check(path.parent)
    assert result.returncode == 1
    label = "Chaves estrangeiras" if kind == "foreign_key" else "Restrições CHECK do modelo"
    assert f"{label}: FALHA" in result.stdout
    assert marker not in result.stdout + result.stderr
    assert "Traceback" not in result.stderr
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
