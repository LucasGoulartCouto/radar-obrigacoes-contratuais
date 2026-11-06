"""Experimento M7: serviços reais, dados sintéticos e bancos novos em .tools/."""

import argparse
import hashlib
import json
import math
import os
import platform
import sqlite3
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime
from importlib.metadata import version
from pathlib import Path
from time import perf_counter, process_time
from uuid import uuid4

from radar_contratos.application.contracts import ContractService
from radar_contratos.bootstrap import (
    build_agenda_service,
    build_document_service,
    build_review_service,
)
from radar_contratos.config import Settings
from radar_contratos.domain.documents import DocumentInput, DocumentRole
from radar_contratos.domain.reviews import EvidenceInput, ManualDraft
from radar_contratos.errors import StaleRecordError, StorageBusyError, ValidationError
from radar_contratos.infrastructure.persistence.contracts import SqliteContractStore
from radar_contratos.infrastructure.persistence.database import initialize_database, make_engine

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = date(2027, 5, 1)
HEADER = b"Termino: 2027-06-30.\nAviso: 30 dias corridos.\n"
SOURCE = HEADER + b"x" * (8192 - len(HEADER))


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def summary(values):
    ordered = sorted(values)
    if not ordered:
        return {"n": 0, "p50_ms": None, "p95_ms": None, "max_ms": None}
    return {
        "n": len(ordered),
        "p50_ms": round(ordered[math.ceil(len(ordered) * 0.50) - 1], 3),
        "p95_ms": round(ordered[math.ceil(len(ordered) * 0.95) - 1], 3),
        "max_ms": round(ordered[-1], 3),
    }


def peak_memory_bytes():
    """Pico do processo inteiro; não atribuir o valor a uma única consulta."""
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes

        class MemoryCounters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
                (name, ctypes.c_size_t)
                for name in (
                    "PeakWorkingSetSize",
                    "WorkingSetSize",
                    "QuotaPeakPagedPoolUsage",
                    "QuotaPagedPoolUsage",
                    "QuotaPeakNonPagedPoolUsage",
                    "QuotaNonPagedPoolUsage",
                    "PagefileUsage",
                    "PeakPagefileUsage",
                )
            ]

        counters = MemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        psapi.GetProcessMemoryInfo.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(MemoryCounters),
            wintypes.DWORD,
        ]
        if not psapi.GetProcessMemoryInfo(
            kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        return counters.PeakWorkingSetSize
    import resource

    scale = 1 if sys.platform == "darwin" else 1024
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * scale


def confirm(reviews, case, request_id):
    contract_id, analysis = case
    return reviews.confirm(
        contract_id=contract_id,
        analysis_id=analysis["analysis_id"],
        expected_document_version=1,
        expected_analysis_version=1,
        expected_rule_version="AVISO_CORRIDOS_V1",
        actor="M7 simulacao",
        request_id=request_id,
        acknowledged=True,
    )


def seed(engine, count):
    contracts = ContractService(SqliteContractStore(engine))
    documents = build_document_service(Settings(Path("unused")), engine)
    reviews = build_review_service(engine)
    pending, blocked, confirmed = [], [], []
    stage_times = {key: [] for key in ("register", "document", "manual_analysis", "confirm")}

    def timed(stage, action):
        started = perf_counter()
        result = action()
        stage_times[stage].append((perf_counter() - started) * 1000)
        return result

    for index in range(count):
        contract = timed(
            "register",
            lambda index=index: contracts.register(
                title=f"M7 sintetico {index:06d}", actor="M7 simulacao", request_id=str(uuid4())
            ),
        )
        mode = index % 4
        if mode == 0:
            continue
        timed(
            "document",
            lambda contract=contract: documents.submit(
                contract_id=contract.id,
                documents=(DocumentInput("m7.txt", SOURCE, DocumentRole.BASE),),
                expected_version=0,
                actor="M7 simulacao",
                request_id=str(uuid4()),
                synthetic=True,
            ),
        )
        draft = ManualDraft(
            end_date=date(2027, 6, 30),
            end_evidence=EvidenceInput(0, 1, 1, HEADER.decode().splitlines()[0]),
            notice_days=30,
            notice_evidence=EvidenceInput(0, 2, 2, HEADER.decode().splitlines()[1]),
            notice_unit="undefined" if mode == 2 else "calendar_days",
        )
        analysis = timed(
            "manual_analysis",
            lambda contract=contract, draft=draft: reviews.register(
                contract_id=contract.id,
                expected_document_version=1,
                expected_analysis_version=0,
                draft=draft,
                actor="M7 simulacao",
                request_id=str(uuid4()),
                synthetic=True,
            ),
        )
        case = (contract.id, analysis)
        if mode == 1:
            pending.append(case)
        elif mode == 2:
            blocked.append(case)
        else:
            timed("confirm", lambda case=case: confirm(reviews, case, str(uuid4())))
            confirmed.append(case)
        if (index + 1) % 500 == 0:
            print(f"seed: {index + 1}/{count}", flush=True)
    return documents, reviews, pending, blocked, confirmed, stage_times


def measure(path, count, samples, rounds, concurrency):
    engine = make_engine(path)
    try:
        initialize_database(engine)
        started, cpu = perf_counter(), process_time()
        documents, reviews, pending, blocked, confirmed, times = seed(engine, count)
        result = {
            "contracts": count,
            "seed_seconds": round(perf_counter() - started, 3),
            "seed_cpu_seconds": round(process_time() - cpu, 3),
            "seed_stages": {key: summary(value) for key, value in times.items()},
        }
        agenda = build_agenda_service(engine)
        initial_events = len(confirmed) * 2

        def read(exact=True):
            view = agenda.read(REFERENCE)
            require(len(view.portfolio.contracts) == count, "Carteira incompleta")
            require(sum(n for _, n in view.coverage) == count, "Cobertura incompleta")
            require(
                len({item.event.id for item in view.items}) == len(view.items), "Eventos duplicados"
            )
            require(len(view.items) % 2 == 0, "Confirmacao parcial")
            if exact:
                require(len(view.items) == initial_events, "Agenda inicial incorreta")

        cold = perf_counter()
        read()
        result["first_read_ms"] = round((perf_counter() - cold) * 1000, 3)
        result["reads"] = []

        def operation(item):
            kind, action = item
            before = perf_counter()
            status = "ok"
            try:
                action()
            except StorageBusyError:
                status = "busy"
            return {"kind": kind, "status": status, "ms": (perf_counter() - before) * 1000}

        for workers in concurrency:
            observations, batches = [], []
            for _ in range(rounds):
                before, cpu = perf_counter(), process_time()
                with ThreadPoolExecutor(max_workers=workers) as pool:
                    observations.extend(pool.map(operation, [("read", read)] * samples))
                batches.append(
                    {
                        "wall_seconds": round(perf_counter() - before, 3),
                        "cpu_seconds": round(process_time() - cpu, 3),
                    }
                )
            result["reads"].append(
                {
                    "workers": workers,
                    "batches": batches,
                    "latency": summary([x["ms"] for x in observations]),
                    "busy": sum(x["status"] == "busy" for x in observations),
                }
            )

        # Duas chamadas por recibo, misturadas com leituras. Sem repeticao automatica.
        selected = pending[: min(24, len(pending))]
        tasks = []
        for case in selected:
            request_id = str(uuid4())

            def action(case=case, rid=request_id):
                return confirm(reviews, case, rid)

            tasks.extend(
                [
                    ("confirm", action),
                    ("read", lambda: read(False)),
                    ("confirm", action),
                    ("read", lambda: read(False)),
                ]
            )
        before, cpu = perf_counter(), process_time()
        with ThreadPoolExecutor(max_workers=max(concurrency)) as pool:
            observed = list(pool.map(operation, tasks))
        result["mixed"] = {
            "workers": max(concurrency),
            "wall_seconds": round(perf_counter() - before, 3),
            "cpu_seconds": round(process_time() - cpu, 3),
            "operations": observed,
        }
        # Estado final deriva de recibos de negocio, nao de uma estimativa por latencia.
        successful_cases = sum(bool(reviews.current_events(case[0])) for case in selected)
        expected_successes = sum(
            any(observed[index * 4 + offset]["status"] == "ok" for offset in (0, 2))
            for index in range(len(selected))
        )
        require(successful_cases == expected_successes, "Estado difere dos recibos")
        view = agenda.read(REFERENCE)
        require(
            len(view.items) == initial_events + successful_cases * 2,
            "Duplicacao/perda apos concorrencia",
        )
        require(sum(n for _, n in view.coverage) == count, "Cobertura final incompleta")
        require(
            all(len(reviews.list_history(case[0])) == 1 for case in selected), "Historico duplicado"
        )
        try:
            confirm(reviews, blocked[0], str(uuid4()))
        except ValidationError:
            pass
        else:
            raise RuntimeError("Ambiguidade foi confirmada")
        case = confirmed[0]
        documents.submit(
            contract_id=case[0],
            documents=(DocumentInput("m7.txt", SOURCE + b"\nRevisao.", DocumentRole.BASE),),
            expected_version=1,
            actor="M7 simulacao",
            request_id=str(uuid4()),
            synthetic=True,
        )
        try:
            confirm(reviews, case, str(uuid4()))
        except StaleRecordError:
            pass
        else:
            raise RuntimeError("Base antiga foi confirmada")
        require(not reviews.current_events(case[0]), "Evento desatualizado vigente")
        require(len(reviews.list_history(case[0])) == 1, "Historico anterior perdido")
        with engine.connect() as connection:
            require(
                not connection.exec_driver_sql("PRAGMA foreign_key_check").all(),
                "Chave estrangeira violada",
            )
            result["integrity_check"] = connection.exec_driver_sql(
                "PRAGMA integrity_check"
            ).scalar()
            require(result["integrity_check"] == "ok", "Banco inconsistente")
            result["journal_mode"] = connection.exec_driver_sql("PRAGMA journal_mode").scalar()
            result["synchronous"] = connection.exec_driver_sql("PRAGMA synchronous").scalar()
            result["schema"] = connection.exec_driver_sql(
                "SELECT version_num FROM alembic_version"
            ).scalar()
        result["invariants"] = {
            "coverage_complete": True,
            "atomic_no_duplicate_events": True,
            "stale_rejected": True,
            "blocked_rejected": True,
            "history_preserved": True,
            "foreign_keys": True,
        }
        result["successful_unique_confirmations"] = successful_cases
        result["database_bytes"] = path.stat().st_size
        result["process_peak_memory_bytes"] = peak_memory_bytes()
        return result
    finally:
        engine.dispose()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", type=int, nargs="+", default=[100, 1000, 3000])
    parser.add_argument("--samples", type=int, default=40, help="Por rodada e concorrencia")
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--workers", type=int, nargs="+", default=[1, 4, 8])
    args = parser.parse_args()
    if (
        any(n < 8 or n > 10000 or n % 4 for n in args.sizes)
        or not 1 <= args.samples <= 500
        or not 1 <= args.rounds <= 10
        or any(n < 1 or n > 8 for n in args.workers)
    ):
        parser.error(
            "Use tamanhos multiplos de 4 (8..10000), amostras 1..500, rodadas 1..10, workers 1..8"
        )
    scratch = ROOT / ".tools" / f"m7-{uuid4().hex}"
    scratch.mkdir(parents=True, exist_ok=False)
    source_hash = hashlib.sha256()
    for path in sorted((ROOT / "src").rglob("*.py")):
        source_hash.update(path.relative_to(ROOT).as_posix().encode())
        source_hash.update(path.read_bytes())
    output = {
        "started_utc": datetime.now(UTC).isoformat(),
        "git_head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_sha256": source_hash.hexdigest(),
        "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "logical_cpus": os.cpu_count(),
        "sqlite": sqlite3.sqlite_version,
        "packages": {p: version(p) for p in ("sqlalchemy", "alembic", "streamlit")},
        "parameters": vars(args),
        "document_bytes": len(SOURCE),
        "synthetic_source_sha256": hashlib.sha256(SOURCE).hexdigest(),
        "cache": "first read after seed, then warm; OS cache not flushed",
        "scope": "services only; no UI/network/IA; closed-loop threads; no retries",
        "runs": [],
    }
    for count in args.sizes:
        print(f"M7: {count} contratos", flush=True)
        output["runs"].append(
            measure(scratch / f"{count}.sqlite3", count, args.samples, args.rounds, args.workers)
        )
        # Checkpoint por tamanho; pasta unica, nunca sobrescreve banco anterior.
        (scratch / "resultados.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(scratch / "resultados.json", flush=True)


if __name__ == "__main__":
    main()
