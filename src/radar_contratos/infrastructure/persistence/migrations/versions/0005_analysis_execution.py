"""Referência de execução como metadado, preservando payloads e confirmações."""

from alembic import op

revision = "0005_analysis_execution"
down_revision = "0004_extractions"
branch_labels = depends_on = None


def upgrade() -> None:
    # SQLite admite REFERENCES na coluna nullable sem reconstruir a tabela referenciada.
    op.execute(
        "ALTER TABLE manual_analyses ADD COLUMN execution_id VARCHAR(36) "
        "REFERENCES extraction_runs(id)"
    )
    op.execute("""
        UPDATE manual_analyses
        SET execution_id = (
            SELECT extraction_runs.id FROM extraction_runs
            WHERE extraction_runs.id = json_extract(manual_analyses.payload, '$.execution_id')
              AND extraction_runs.contract_id = manual_analyses.contract_id
              AND extraction_runs.revision_id = manual_analyses.revision_id
        )
        WHERE method_version = 'ASSISTED_LOCAL_LINES_V1'
    """)


def downgrade() -> None:
    op.drop_column("manual_analyses", "execution_id")
