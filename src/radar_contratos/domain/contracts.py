"""Cadastro básico; não representa análise ou confirmação de uma obrigação."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Contract:
    id: str
    title: str
    record_version: int
    created_at_utc: str
    updated_at_utc: str
    document_version: int = 0
    analysis_version: int = 0
