"""Configuração explícita do armazenamento local."""

import os
from dataclasses import dataclass
from pathlib import Path

from radar_contratos.domain.documents import DocumentLimits
from radar_contratos.errors import ValidationError


@dataclass(frozen=True, slots=True)
class Settings:
    data_dir: Path
    document_limits: DocumentLimits = DocumentLimits()
    local_model_digest: str | None = None

    @classmethod
    def from_environment(cls) -> Settings:
        try:
            limits = DocumentLimits(
                max_document_bytes=int(os.environ.get("RADAR_MAX_DOCUMENT_BYTES", "262144")),
                max_revision_bytes=int(os.environ.get("RADAR_MAX_REVISION_BYTES", "1048576")),
                max_documents=int(os.environ.get("RADAR_MAX_DOCUMENTS", "5")),
            )
        except ValueError as exc:
            raise ValidationError("Os limites documentais devem ser inteiros positivos.") from exc
        return cls(
            Path(os.environ.get("RADAR_DATA_DIR", "var")).expanduser().resolve(),
            limits,
            os.environ.get("RADAR_LOCAL_MODEL_DIGEST") or None,
        )

    @property
    def database_path(self) -> Path:
        return self.data_dir / "radar.sqlite3"
