"""Validação compartilhada de metadados e identificação de operações."""

import hashlib
import json
from uuid import UUID

from radar_contratos.errors import ValidationError


def text(value: str, *, label: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"{label}: informe um texto.")
    value = value.strip()
    if not value or len(value) > maximum or any(ord(char) < 32 for char in value):
        raise ValidationError(
            f"{label}: informe entre 1 e {maximum} caracteres, sem quebras de linha."
        )
    return value


def request_id(value: str) -> str:
    try:
        return str(UUID(value))
    except (ValueError, AttributeError, TypeError) as exc:
        raise ValidationError("A identificação da operação é inválida. Atualize a tela.") from exc


def fingerprint(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
