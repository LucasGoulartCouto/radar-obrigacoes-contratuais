"""O experimento mede serviços isolados sem usar configuração/banco do operador."""

import importlib.util
from pathlib import Path

import pytest


def load_harness():
    path = Path(__file__).resolve().parents[2] / "scripts" / "medir_base_local.py"
    spec = importlib.util.spec_from_file_location("m7_harness", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_small_load_preserves_invariants_and_ignores_operator_database(tmp_path, monkeypatch):
    protected = tmp_path / "operator" / "radar.sqlite3"
    protected.parent.mkdir()
    protected.write_bytes(b"sentinela: nao abrir nem migrar")
    monkeypatch.setenv("RADAR_DATA_DIR", str(protected.parent))
    report = load_harness().measure(tmp_path / "load.sqlite3", 8, 2, 1, [1, 4])
    assert protected.read_bytes() == b"sentinela: nao abrir nem migrar"
    assert report["contracts"] == 8
    assert all(report["invariants"].values())
    assert report["integrity_check"] == "ok"
    assert report["successful_unique_confirmations"] == 2
    assert len(report["mixed"]["operations"]) == 8
    assert all(item["status"] == "ok" for item in report["mixed"]["operations"])
    assert [item["latency"]["n"] for item in report["reads"]] == [2, 2]


@pytest.mark.parametrize("args", [["--sizes", "0"], ["--workers", "9"], ["--rounds", "0"]])
def test_invalid_load_is_rejected_before_creating_databases(tmp_path, monkeypatch, args):
    harness = load_harness()
    monkeypatch.setattr(harness, "ROOT", tmp_path)
    monkeypatch.setattr("sys.argv", ["medir_base_local.py", *args])
    with pytest.raises(SystemExit) as error:
        harness.main()
    assert error.value.code == 2
    assert list(tmp_path.iterdir()) == []
