"""Entrada textual e identidade de conjuntos documentais do case sintético."""

import hashlib
import json
import unicodedata
from dataclasses import dataclass
from enum import StrEnum

from radar_contratos.errors import ValidationError

NORMALIZATION_VERSION = "TEXT_REFERENCE_V1"


class DocumentRole(StrEnum):
    BASE = "base"
    AMENDMENT = "aditivo"
    REPLACEMENT = "substituição"
    UNKNOWN = "desconhecido"


@dataclass(frozen=True, slots=True)
class DocumentLimits:
    max_document_bytes: int = 262_144
    max_revision_bytes: int = 1_048_576
    max_documents: int = 5

    def __post_init__(self) -> None:
        values = (self.max_document_bytes, self.max_revision_bytes, self.max_documents)
        if any(type(value) is not int or value < 1 for value in values):
            raise ValidationError("Os limites documentais devem ser inteiros positivos.")
        if self.max_document_bytes > self.max_revision_bytes:
            raise ValidationError("O limite por documento não pode exceder o limite do conjunto.")


@dataclass(frozen=True, slots=True)
class DocumentInput:
    filename: str
    content: bytes
    role: DocumentRole


@dataclass(frozen=True, slots=True)
class PreparedDocument:
    filename: str
    role: DocumentRole
    original_bytes: bytes
    raw_sha256: str
    reference_text: str
    reference_sha256: str
    normalization_version: str = NORMALIZATION_VERSION


@dataclass(frozen=True, slots=True)
class DocumentRevision:
    id: str
    contract_id: str
    number: int
    source_request_id: str
    document_count: int
    total_bytes: int
    actor: str
    created_at_utc: str


@dataclass(frozen=True, slots=True)
class SubmissionReceipt:
    request_id: str
    revision_id: str
    revision_number: int
    created_revision: bool
    actor: str
    received_at_utc: str


def prepare_documents(
    inputs: tuple[DocumentInput, ...], limits: DocumentLimits
) -> tuple[PreparedDocument, ...]:
    if len(inputs) > limits.max_documents:
        raise ValidationError(f"O conjunto aceita até {limits.max_documents} documentos.")
    if any(
        not isinstance(item, DocumentInput) or type(item.content) is not bytes for item in inputs
    ):
        raise ValidationError("Envie arquivos de texto em bytes, sem conversão prévia.")
    if sum(len(item.content) for item in inputs) > limits.max_revision_bytes:
        raise ValidationError(f"O conjunto excede {limits.max_revision_bytes} bytes.")
    prepared = []
    identities = set()
    for item in inputs:
        name = item.filename
        if (
            not isinstance(name, str)
            or not 1 <= len(name) <= 200
            or name != name.strip()
            or any(char in name for char in "/\\:")
            or any(unicodedata.category(char) == "Cc" for char in name)
            or not name.lower().endswith(".txt")
        ):
            raise ValidationError(
                "Use um nome de arquivo .txt, sem caminhos ou caracteres de controle."
            )
        if len(item.content) > limits.max_document_bytes:
            raise ValidationError(f"Um documento excede {limits.max_document_bytes} bytes.")
        try:
            role = DocumentRole(item.role)
        except (ValueError, TypeError) as exc:
            raise ValidationError("Informe o papel de cada documento.") from exc
        try:
            text = item.content.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
        except UnicodeDecodeError as exc:
            raise ValidationError("O documento não é texto UTF-8 válido.") from exc
        if not text.strip() or text.lstrip().startswith("%PDF-"):
            raise ValidationError("Envie texto UTF-8 não vazio; PDF não é suportado.")
        if any(unicodedata.category(char) == "Cc" and char not in "\n\t" for char in text):
            raise ValidationError("O texto contém controles incompatíveis com este formato.")
        reference_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
        identity = (role, reference_sha)
        if identity in identities:
            raise ValidationError("O conjunto repete o mesmo texto e papel. Remova a repetição.")
        identities.add(identity)
        prepared.append(
            PreparedDocument(
                filename=name,
                role=role,
                original_bytes=item.content,
                raw_sha256=hashlib.sha256(item.content).hexdigest(),
                reference_text=text,
                reference_sha256=reference_sha,
            )
        )
    return tuple(prepared)


def revision_fingerprint(documents: tuple[PreparedDocument, ...]) -> str:
    members = sorted((document.role, document.reference_sha256) for document in documents)
    payload = json.dumps([NORMALIZATION_VERSION, members], ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
