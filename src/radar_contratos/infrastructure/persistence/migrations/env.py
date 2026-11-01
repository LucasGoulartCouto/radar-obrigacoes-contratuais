"""Migrações executadas pela conexão configurada pelo aplicativo."""

from alembic import context

from radar_contratos.infrastructure.persistence.models import Base

connection = context.config.attributes.get("connection")
if connection is None:
    raise RuntimeError("Execute as migrações pelo comando 'radar init-db'.")

context.configure(connection=connection, target_metadata=Base.metadata, render_as_batch=True)
with context.begin_transaction():
    context.run_migrations()
