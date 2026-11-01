"""Configuração explícita do armazenamento local."""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    data_dir: Path

    @classmethod
    def from_environment(cls) -> Settings:
        return cls(Path(os.environ.get("RADAR_DATA_DIR", "var")).expanduser().resolve())

    @property
    def database_path(self) -> Path:
        return self.data_dir / "radar.sqlite3"
