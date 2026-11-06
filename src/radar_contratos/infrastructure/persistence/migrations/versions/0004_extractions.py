"""Tentativas persistidas sem modificar os levantamentos e confirmações anteriores."""

import sqlalchemy as sa
from alembic import op

revision = "0004_extractions"
down_revision = "0003_reviews"
branch_labels = depends_on = None


def upgrade() -> None:
    op.add_column(
        "contracts",
        sa.Column(
            "known_textual_amendment",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "manual_analyses",
        sa.Column(
            "method_version",
            sa.String(40),
            nullable=False,
            server_default="MANUAL_V1",
        ),
    )
    op.create_table(
        "extraction_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("contract_id", sa.String(36), sa.ForeignKey("contracts.id"), nullable=False),
        sa.Column(
            "revision_id", sa.String(36), sa.ForeignKey("document_revisions.id"), nullable=False
        ),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("analysis_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("input_sha256", sa.String(64), nullable=False),
        sa.Column("method", sa.JSON(), nullable=False),
        sa.Column("output", sa.JSON(), nullable=True),
        sa.Column("blocked", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("error_code", sa.String(40), nullable=False),
        sa.Column("actor", sa.String(80), nullable=False),
        sa.Column("created_at_utc", sa.String(40), nullable=False),
        sa.Column("started_at_utc", sa.String(40), nullable=True),
        sa.Column("finished_at_utc", sa.String(40), nullable=True),
        sa.Column("duration_ms", sa.Float(), nullable=True),
        sa.UniqueConstraint("contract_id", "number", name="uq_extraction_number"),
        sa.CheckConstraint("number >= 1 AND analysis_version >= 0", name="ck_extraction_versions"),
        sa.CheckConstraint(
            "status IN ('pending','running','completed','failed','interrupted')",
            name="ck_extraction_status",
        ),
    )
    op.create_index("ix_extraction_runs_contract_id", "extraction_runs", ["contract_id"])
    op.create_index("ix_extraction_runs_revision_id", "extraction_runs", ["revision_id"])


def downgrade() -> None:
    op.drop_table("extraction_runs")
    op.drop_column("manual_analyses", "method_version")
    op.drop_column("contracts", "known_textual_amendment")
