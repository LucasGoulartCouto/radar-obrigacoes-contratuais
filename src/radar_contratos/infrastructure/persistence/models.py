"""Mapeamentos do cadastro e do histórico da fundação."""

from sqlalchemy import JSON, CheckConstraint, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ContractRow(Base):
    __tablename__ = "contracts"
    __table_args__ = (CheckConstraint("record_version >= 1", name="ck_contract_version"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    record_version: Mapped[int]
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
