"""Preparação e backup do armazenamento local."""

import argparse
import logging
from datetime import UTC, datetime
from pathlib import Path

from radar_contratos.config import Settings
from radar_contratos.errors import RadarError
from radar_contratos.infrastructure.persistence.database import (
    backup_database,
    initialize_database,
    make_engine,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Preparação local do Radar")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init-db", help="Criar ou atualizar o esquema sem apagar dados")
    backup = commands.add_parser("backup", help="Criar uma cópia consistente do banco")
    backup.add_argument("--output", type=Path, help="Arquivo de destino que ainda não existe")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    try:
        settings = Settings.from_environment()
        if args.command == "init-db":
            engine = make_engine(settings.database_path)
            try:
                initialize_database(engine)
            finally:
                engine.dispose()
            print("Banco preparado. Os dados existentes foram preservados.")
        elif args.command == "backup":
            stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
            destination = args.output or settings.data_dir / "backups" / f"radar-{stamp}.sqlite3"
            output = backup_database(settings.database_path, destination)
            print(f"Backup criado: {output}")
    except (RadarError, OSError, TimeoutError) as exc:
        parser.exit(1, f"Não foi possível concluir: {exc}\n")
