"""Mapeamentos do cadastro e do histórico da fundação."""

from sqlalchemy import (
    JSON,
    CheckConstraint,
    ForeignKey,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ContractRow(Base):
    __tablename__ = "contracts"
    __table_args__ = (
        CheckConstraint("record_version >= 1", name="ck_contract_version"),
        CheckConstraint("document_version >= 0", name="ck_contract_document_version"),
        CheckConstraint("analysis_version >= 0", name="ck_contract_analysis_version"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    record_version: Mapped[int]
    document_version: Mapped[int] = mapped_column(default=0, server_default="0")
    analysis_version: Mapped[int] = mapped_column(default=0, server_default="0")
    created_at_utc: Mapped[str] = mapped_column(String(40))
    updated_at_utc: Mapped[str] = mapped_column(String(40))


class OperationRow(Base):
    __tablename__ = "operations"

    request_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    fingerprint: Mapped[str] = mapped_column(String(64))
    contract_id: Mapped[str] = mapped_column(ForeignKey("contracts.id"), index=True)
    response: Mapped[dict] = mapped_column(JSON)


class AuditRow(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    request_id: Mapped[str] = mapped_column(ForeignKey("operations.request_id"), unique=True)
    contract_id: Mapped[str] = mapped_column(ForeignKey("contracts.id"), index=True)
    action: Mapped[str] = mapped_column(String(40))
    actor: Mapped[str] = mapped_column(String(80))
    at_utc: Mapped[str] = mapped_column(String(40))
    details: Mapped[dict] = mapped_column(JSON)


class DocumentRevisionRow(Base):
    __tablename__ = "document_revisions"
    __table_args__ = (
        UniqueConstraint("contract_id", "number", name="uq_document_revision_number"),
        CheckConstraint("number >= 1", name="ck_document_revision_number"),
        CheckConstraint("document_count >= 0 AND total_bytes >= 0", name="ck_revision_sizes"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    contract_id: Mapped[str] = mapped_column(ForeignKey("contracts.id"), index=True)
    number: Mapped[int]
    fingerprint: Mapped[str] = mapped_column(String(64))
    source_request_id: Mapped[str] = mapped_column(ForeignKey("operations.request_id"), unique=True)
    document_count: Mapped[int]
    total_bytes: Mapped[int]
    actor: Mapped[str] = mapped_column(String(80))
    created_at_utc: Mapped[str] = mapped_column(String(40))


class DocumentUploadRow(Base):
    __tablename__ = "document_uploads"
    __table_args__ = (
        UniqueConstraint("request_id", "position", name="uq_upload_position"),
        CheckConstraint("position >= 0", name="ck_upload_position"),
        CheckConstraint(
            "role IN ('base', 'aditivo', 'substituição', 'desconhecido')", name="ck_document_role"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    revision_id: Mapped[str] = mapped_column(ForeignKey("document_revisions.id"), index=True)
    request_id: Mapped[str] = mapped_column(ForeignKey("operations.request_id"), index=True)
    position: Mapped[int]
    filename: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(20))
    original_bytes: Mapped[bytes] = mapped_column(LargeBinary)
    raw_sha256: Mapped[str] = mapped_column(String(64))
    reference_text: Mapped[str] = mapped_column(Text)
    reference_sha256: Mapped[str] = mapped_column(String(64))
    normalization_version: Mapped[str] = mapped_column(String(40))


class AnalysisRow(Base):
    __tablename__ = "manual_analyses"
    __table_args__ = (
        UniqueConstraint("contract_id", "number", name="uq_analysis_number"),
        CheckConstraint("number >= 1", name="ck_analysis_number"),
        CheckConstraint("candidate_count BETWEEN 0 AND 2", name="ck_analysis_candidate_count"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    contract_id: Mapped[str] = mapped_column(ForeignKey("contracts.id"), index=True)
    revision_id: Mapped[str] = mapped_column(ForeignKey("document_revisions.id"), index=True)
    number: Mapped[int]
    fingerprint: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSON)
    rule_version: Mapped[str] = mapped_column(String(40))
    blocked: Mapped[bool]
    candidate_count: Mapped[int]
    change_reason: Mapped[str] = mapped_column(String(500))
    actor: Mapped[str] = mapped_column(String(80))
    created_at_utc: Mapped[str] = mapped_column(String(40))


class ReviewRow(Base):
    __tablename__ = "human_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("manual_analyses.id"), unique=True)
    actor: Mapped[str] = mapped_column(String(80))
    reviewed_at_utc: Mapped[str] = mapped_column(String(40))


class ConfirmedEventRow(Base):
    __tablename__ = "confirmed_events"
    __table_args__ = (
        UniqueConstraint("review_id", "kind", name="uq_review_event_kind"),
        CheckConstraint("kind IN ('termination', 'non_renewal_notice')", name="ck_event_kind"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    review_id: Mapped[str] = mapped_column(ForeignKey("human_reviews.id"), index=True)
    kind: Mapped[str] = mapped_column(String(30))
    event_date: Mapped[str] = mapped_column(String(10))
