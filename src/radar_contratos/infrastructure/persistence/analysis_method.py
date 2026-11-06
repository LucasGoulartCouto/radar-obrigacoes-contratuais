"""Validade do método nas projeções, sem carregar textos ou o payload da análise."""

from radar_contratos.domain import assisted, reviews
from radar_contratos.infrastructure.persistence.models import AnalysisRow, ExtractionRunRow


def selected_execution_join(run=ExtractionRunRow):
    return (
        (run.id == AnalysisRow.execution_id)
        & (run.contract_id == AnalysisRow.contract_id)
        & (run.revision_id == AnalysisRow.revision_id)
    )


def method_is_current(version, status, descriptor, *, kernel):
    if version == reviews.METHOD_VERSION:
        return True
    return (
        version == assisted.METHOD_VERSION
        and status == "completed"
        and isinstance(descriptor, dict)
        and descriptor.get("kernel") == kernel
    )
