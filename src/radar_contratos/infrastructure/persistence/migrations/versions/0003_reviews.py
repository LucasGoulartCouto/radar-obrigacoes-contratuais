"""Levantamentos manuais, conferências e eventos ligados à base revisada."""

import sqlalchemy as sa
from alembic import op

revision = "0003_reviews"
down_revision = "0002_documents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "contracts",
        sa.Column(
            "analysis_version",
            sa.Integer(),
            sa.CheckConstraint("analysis_version >= 0", name="ck_contract_analysis_version"),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.create_table(
        "manual_analyses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("contract_id", sa.String(36), sa.ForeignKey("contracts.id"), nullable=False),
        sa.Column(
            "revision_id", sa.String(36), sa.ForeignKey("document_revisions.id"), nullable=False
        ),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("rule_version", sa.String(40), nullable=False),
        sa.Column("blocked", sa.Boolean(), nullable=False),
        sa.Column("candidate_count", sa.Integer(), nullable=False),
        sa.Column("change_reason", sa.String(500), nullable=False),
        sa.Column("actor", sa.String(80), nullable=False),
        sa.Column("created_at_utc", sa.String(40), nullable=False),
        sa.UniqueConstraint("contract_id", "number", name="uq_analysis_number"),
        sa.CheckConstraint("number >= 1", name="ck_analysis_number"),
        sa.CheckConstraint("candidate_count BETWEEN 0 AND 2", name="ck_analysis_candidate_count"),
    )
    op.create_index("ix_manual_analyses_contract_id", "manual_analyses", ["contract_id"])
    op.create_index("ix_manual_analyses_revision_id", "manual_analyses", ["revision_id"])
    op.create_table(
        "human_reviews",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "analysis_id",
            sa.String(36),
            sa.ForeignKey("manual_analyses.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("actor", sa.String(80), nullable=False),
        sa.Column("reviewed_at_utc", sa.String(40), nullable=False),
    )
    op.create_table(
        "confirmed_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("review_id", sa.String(36), sa.ForeignKey("human_reviews.id"), nullable=False),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("event_date", sa.String(10), nullable=False),
        sa.UniqueConstraint("review_id", "kind", name="uq_review_event_kind"),
        sa.CheckConstraint("kind IN ('termination', 'non_renewal_notice')", name="ck_event_kind"),
    )
    op.create_index("ix_confirmed_events_review_id", "confirmed_events", ["review_id"])


def downgrade() -> None:
    op.drop_table("confirmed_events")
    op.drop_table("human_reviews")
    op.drop_table("manual_analyses")
    op.drop_column("contracts", "analysis_version")
