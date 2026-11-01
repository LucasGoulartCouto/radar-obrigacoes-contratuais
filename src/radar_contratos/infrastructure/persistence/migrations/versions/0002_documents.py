"""Revisões documentais e bytes recebidos, preservando o cadastro existente."""

import sqlalchemy as sa
from alembic import op

revision = "0002_documents"
down_revision = "0001_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "contracts",
        sa.Column(
            "document_version",
            sa.Integer(),
            sa.CheckConstraint("document_version >= 0", name="ck_contract_document_version"),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.create_table(
        "document_revisions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("contract_id", sa.String(36), sa.ForeignKey("contracts.id"), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column(
            "source_request_id",
            sa.String(36),
            sa.ForeignKey("operations.request_id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("document_count", sa.Integer(), nullable=False),
        sa.Column("total_bytes", sa.Integer(), nullable=False),
        sa.Column("actor", sa.String(80), nullable=False),
        sa.Column("created_at_utc", sa.String(40), nullable=False),
        sa.UniqueConstraint("contract_id", "number", name="uq_document_revision_number"),
        sa.CheckConstraint("number >= 1", name="ck_document_revision_number"),
        sa.CheckConstraint("document_count >= 0 AND total_bytes >= 0", name="ck_revision_sizes"),
    )
    op.create_index("ix_document_revisions_contract_id", "document_revisions", ["contract_id"])
    op.create_table(
        "document_uploads",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "revision_id", sa.String(36), sa.ForeignKey("document_revisions.id"), nullable=False
        ),
        sa.Column(
            "request_id", sa.String(36), sa.ForeignKey("operations.request_id"), nullable=False
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(200), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("original_bytes", sa.LargeBinary(), nullable=False),
        sa.Column("raw_sha256", sa.String(64), nullable=False),
        sa.Column("reference_text", sa.Text(), nullable=False),
        sa.Column("reference_sha256", sa.String(64), nullable=False),
        sa.Column("normalization_version", sa.String(40), nullable=False),
        sa.UniqueConstraint("request_id", "position", name="uq_upload_position"),
        sa.CheckConstraint("position >= 0", name="ck_upload_position"),
        sa.CheckConstraint(
            "role IN ('base', 'aditivo', 'substituição', 'desconhecido')", name="ck_document_role"
        ),
    )
    op.create_index("ix_document_uploads_revision_id", "document_uploads", ["revision_id"])
    op.create_index("ix_document_uploads_request_id", "document_uploads", ["request_id"])


def downgrade() -> None:
    op.drop_table("document_uploads")
    op.drop_table("document_revisions")
    op.drop_column("contracts", "document_version")
