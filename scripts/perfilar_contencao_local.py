"""Compara a base aprovada com o candidato em snapshots sintéticos, sem IA."""

import argparse
import cProfile
import hashlib
import importlib.util
import json
import platform
import pstats
import sqlite3
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime
from importlib.metadata import version
from pathlib import Path
from threading import Lock
from time import perf_counter
from uuid import uuid4

from sqlalchemy import event

from radar_contratos.application.agenda import AgendaService
from radar_contratos.application.reviews import ReviewService
from radar_contratos.infrastructure.persistence.agenda import SqliteAgendaStore
from radar_contratos.infrastructure.persistence.database import (
    backup_database,
    initialize_database,
    make_engine,
)
from radar_contratos.infrastructure.persistence.reviews import SqliteReviewStore

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "cb4bd1f3e7d96e776c75153989513afcfa443ec7"


def load_m7():
    spec = importlib.util.spec_from_file_location("m7", ROOT / "scripts/medir_base_local.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def baseline_store(filename, name):
    """Somente código do commit fixo já aprovado; demais dependências são as do lock."""
    relative = f"src/radar_contratos/infrastructure/persistence/{filename}.py"
    source = subprocess.check_output(["git", "show", f"{BASELINE}:{relative}"], cwd=ROOT)
    namespace = {"__name__": f"baseline_{filename}", "__file__": relative}
    exec(compile(source, relative, "exec"), namespace)
    return namespace[name], hashlib.sha256(source).hexdigest()


def trial(source, target, pending, contracts, stores, m7):
    backup_database(source, target)
    engine = make_engine(target)
    records, statements, lock = [], [], Lock()
    reviews, agenda = ReviewService(stores[0](engine)), AgendaService(stores[1](engine))
    enabled = False

    @event.listens_for(engine, "before_cursor_execute")
    def before(_conn, _cursor, _statement, _parameters, context, _many):
        context.profile_started = perf_counter()

    @event.listens_for(engine, "after_cursor_execute")
    def after(_conn, _cursor, statement, parameters, context, _many):
        if not enabled:
            return
        category = statement.split()[0].lower()
        if "UPDATE contracts SET analysis_version=contracts.analysis_version" in statement:
            category = "reserve_writer"
        elif "AS known_amendment" in statement:
            category = "portfolio_execute"
            with lock:
                if not statements:
                    statements.append((statement, parameters))
        with lock:
            records.append((category, (perf_counter() - context.profile_started) * 1000))

    original_commit = engine.dialect.do_commit

    def commit(connection):
        started = perf_counter()
        try:
            return original_commit(connection)
        finally:
            if enabled:
                with lock:
                    records.append(("commit", (perf_counter() - started) * 1000))

    engine.dialect.do_commit = commit

    def read():
        view = agenda.read(date(2027, 5, 1))
        m7.require(len(view.portfolio.contracts) == contracts, "Carteira incompleta")
        m7.require(sum(n for _, n in view.coverage) == contracts, "Cobertura incompleta")
        m7.require(len({x.event.id for x in view.items}) == len(view.items), "Evento duplicado")
        m7.require(len(view.items) % 2 == 0, "Confirmacao parcial")

    def operation(task):
        kind, action = task
        started = perf_counter()
        action()
        return kind, (perf_counter() - started) * 1000

    tasks = []
    for case in pending:
        request_id = str(uuid4())

        def action(case=case, request_id=request_id):
            m7.confirm(reviews, case, request_id)

        tasks.extend([("confirm", action), ("read", read), ("confirm", action), ("read", read)])
    try:
        enabled = True
        started = perf_counter()
        with ThreadPoolExecutor(max_workers=8) as pool:
            observed = list(pool.map(operation, tasks))
        wall = perf_counter() - started
        enabled = False
        report = {
            "wall_seconds": wall,
            "operations": {
                kind: m7.summary([ms for k, ms in observed if k == kind])
                for kind in ("confirm", "read")
            },
            "sql": {
                category: {
                    **m7.summary([ms for c, ms in records if c == category]),
                    "total_ms": sum(ms for c, ms in records if c == category),
                }
                for category in sorted({c for c, _ in records})
            },
        }
        if statements:
            with engine.connect() as connection:
                report["query_plan"] = [
                    list(row)
                    for row in connection.exec_driver_sql(
                        "EXPLAIN QUERY PLAN " + statements[0][0], statements[0][1]
                    ).all()
                ]
        profiler = cProfile.Profile()
        profiler.enable()
        for _ in range(10):
            read()
        profiler.disable()
        report["read_profile_top"] = [
            {
                "file": Path(f).name,
                "function": name,
                "calls": nc,
                "own_seconds": tt,
                "cumulative_seconds": ct,
            }
            for (f, _line, name), (_cc, nc, tt, ct, _callers) in sorted(
                pstats.Stats(profiler).stats.items(), key=lambda x: x[1][2], reverse=True
            )[:12]
        ]
        m7.require(
            all(len(reviews.current_events(c)) == 2 for c, _ in pending),
            "Duplicacao/perda de eventos",
        )
        with engine.connect() as connection:
            report["journal_mode"] = connection.exec_driver_sql("PRAGMA journal_mode").scalar()
            report["synchronous"] = connection.exec_driver_sql("PRAGMA synchronous").scalar()
            m7.require(
                not connection.exec_driver_sql("PRAGMA foreign_key_check").all(),
                "Chave estrangeira violada",
            )
            m7.require(
                connection.exec_driver_sql("PRAGMA integrity_check").scalar() == "ok",
                "Banco inconsistente",
            )
        report["invariants"] = {
            "coverage": True,
            "confirmed_once": True,
            "foreign_keys": True,
            "integrity": True,
        }
        return report
    finally:
        engine.dispose()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contracts", type=int, default=3000)
    parser.add_argument("--rounds", type=int, default=3)
    args = parser.parse_args()
    if not (8 <= args.contracts <= 10000 and args.contracts % 4 == 0 and 1 <= args.rounds <= 5):
        parser.error("Use 8..10000 contratos multiplos de 4 e 1..5 rodadas")
    # Falhar antes de criar bancos se o clone raso não contiver o baseline fixo.
    old_reviews, review_hash = baseline_store("reviews", "SqliteReviewStore")
    old_agenda, agenda_hash = baseline_store("agenda", "SqliteAgendaStore")
    m7 = load_m7()
    out = ROOT / ".tools" / f"contencao-{uuid4().hex}"
    out.mkdir(parents=True, exist_ok=False)
    source = out / "seed.sqlite3"
    engine = make_engine(source)
    try:
        initialize_database(engine)
        _, _, pending, _, _, _ = m7.seed(engine, args.contracts)
    finally:
        engine.dispose()
    store_types = {
        "baseline": (old_reviews, old_agenda),
        "candidate": (SqliteReviewStore, SqliteAgendaStore),
    }
    report = {
        "started_utc": datetime.now(UTC).isoformat(),
        "baseline_commit": BASELINE,
        "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "python": platform.python_version(),
        "sqlite": sqlite3.sqlite_version,
        "platform": platform.platform(),
        "packages": {p: version(p) for p in ("sqlalchemy", "alembic", "streamlit")},
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "baseline_files_sha256": {"reviews": review_hash, "agenda": agenda_hash},
        "candidate_files_sha256": {
            name: hashlib.sha256(
                (ROOT / f"src/radar_contratos/infrastructure/persistence/{name}.py").read_bytes()
            ).hexdigest()
            for name in ("reviews", "agenda")
        },
        "parameters": vars(args),
        "workers": 8,
        "unique_confirmations": min(24, len(pending)),
        "scope": "services + invariant checks; no UI/network/IA; closed loop; no retry",
        "runs": [],
    }
    for index in range(args.rounds):
        order = ("baseline", "candidate") if index % 2 == 0 else ("candidate", "baseline")
        for label in order:
            print(f"rodada {index + 1}: {label}", flush=True)
            result = trial(
                source,
                out / f"{index}-{label}.sqlite3",
                pending[:24],
                args.contracts,
                store_types[label],
                m7,
            )
            report["runs"].append({"round": index + 1, "variant": label, **result})
            (out / "resultados.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(out / "resultados.json", flush=True)


if __name__ == "__main__":
    main()
