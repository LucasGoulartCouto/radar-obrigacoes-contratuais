"""Cadastro, recibos de operação e histórico atômico."""

import sqlalchemy as sa
from alembic import op

revision = "0001_foundation"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "contracts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("record_version", sa.Integer(), nullable=False),
        sa.Column("created_at_utc", sa.String(40), nullable=False),
        sa.Column("updated_at_utc", sa.String(40), nullable=False),
        sa.CheckConstraint("record_version >= 1", name="ck_contract_version"),
    )
    op.create_table(
        "operations",
        sa.Column("request_id", sa.String(36), primary_key=True),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("contract_id", sa.String(36), sa.ForeignKey("contracts.id"), nullable=False),
        sa.Column("response", sa.JSON(), nullable=False),
    )
    op.create_index("ix_operations_contract_id", "operations", ["contract_id"])
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "request_id",
            sa.String(36),
            sa.ForeignKey("operations.request_id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("contract_id", sa.String(36), sa.ForeignKey("contracts.id"), nullable=False),
        sa.Column("action", sa.String(40), nullable=False),
        sa.Column("actor", sa.String(80), nullable=False),
        sa.Column("at_utc", sa.String(40), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
    )
    op.create_index("ix_audit_events_contract_id", "audit_events", ["contract_id"])


def downgrade() -> None:
    op.drop_table("audit_events")
    op.drop_table("operations")
    op.drop_table("contracts")
