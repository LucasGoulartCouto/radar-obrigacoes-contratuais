"""Execução explícita: reserva persistida, inferência fora da escrita e seleção separada."""

from dataclasses import asdict
from time import perf_counter
from typing import Protocol

from radar_contratos.application.inputs import fingerprint, request_id, text
from radar_contratos.application.reviews import _versions
from radar_contratos.domain.assisted import prepare_assisted_analysis
from radar_contratos.domain.extraction_review import ContextDecision
from radar_contratos.domain.reviews import ReferenceDocument
from radar_contratos.errors import ValidationError


class Classifier(Protocol):
    def descriptor(self) -> dict: ...
    def validate_input(self, documents: tuple[ReferenceDocument, ...]) -> None: ...
    def classify(self, documents: tuple[ReferenceDocument, ...]) -> dict: ...


class ExtractionStore(Protocol):
    def context(self, contract_id: str, run_id: str | None = None) -> dict: ...
    def request(self, **arguments) -> dict: ...
    def claim(self, contract_id: str, run_id: str) -> bool: ...
    def finish(self, contract_id: str, run_id: str, **arguments) -> dict: ...
    def interrupt(self, **arguments) -> dict: ...
    def select_result(self, **arguments) -> dict: ...
    def list_runs(self, contract_id: str) -> list[dict]: ...


class ExtractionService:
    def __init__(self, store: ExtractionStore, classifier: Classifier | None, kernel: dict):
        self.store, self.classifier, self.kernel = store, classifier, kernel

    def request(
        self,
        *,
        contract_id: str,
        expected_document_version: int,
        expected_analysis_version: int,
        actor: str,
        operation_id: str,
        synthetic: bool,
    ) -> dict:
        if synthetic is not True:
            raise ValidationError("Confirme o uso exclusivo dos documentos sintéticos do case.")
        if self.classifier is None:
            raise ValidationError(
                "A IA local de desenvolvimento não está configurada neste ambiente."
            )
        _versions(expected_document_version, expected_analysis_version)
        contract_id, operation_id = request_id(contract_id), request_id(operation_id)
        actor = text(actor, label="Responsável pela análise", maximum=80)
        context = self.store.context(contract_id)
        self.classifier.validate_input(context["documents"])
        method = self.classifier.descriptor()
        arguments = {
            "contract_id": contract_id,
            "expected_document_version": expected_document_version,
            "expected_analysis_version": expected_analysis_version,
            "actor": actor,
            "method": method,
            "input_sha256": fingerprint(
                {
                    "documents": [asdict(document) for document in context["documents"]],
                }
            ),
        }
        return self.store.request(
            **arguments, request_id=operation_id, fingerprint=fingerprint(arguments)
        )

    def execute(self, contract_id: str, run_id: str) -> dict:
        contract_id, run_id = request_id(contract_id), request_id(run_id)
        if self.classifier is None:
            raise ValidationError(
                "A IA local de desenvolvimento não está configurada neste ambiente."
            )
        if not self.store.claim(contract_id, run_id):
            return self.store.context(contract_id, run_id)["run"]
        started = perf_counter()
        try:
            context = self.store.context(contract_id, run_id)
            if context["run"]["method"] != self.classifier.descriptor() or context["run"][
                "input_sha256"
            ] != fingerprint(
                {
                    "documents": [asdict(document) for document in context["documents"]],
                }
            ):
                raise ValidationError("O método mudou desde a reserva da tentativa.")
            output = self.classifier.classify(context["documents"])
            prepare_assisted_analysis(
                context["documents"],
                output["classifications"],
                output["abstained"],
                known_amendment=context["known_amendment"],
            )
        except KeyboardInterrupt, SystemExit:
            self.store.finish(
                contract_id,
                run_id,
                status="interrupted",
                output=None,
                duration_ms=(perf_counter() - started) * 1000,
            )
            raise
        except Exception:
            # Nunca persistir mensagem de exceção/resposta, que pode conter texto documental.
            return self.store.finish(
                contract_id,
                run_id,
                status="failed",
                output=None,
                duration_ms=(perf_counter() - started) * 1000,
            )
        return self.store.finish(
            contract_id,
            run_id,
            status="completed",
            output=output,
            duration_ms=(perf_counter() - started) * 1000,
        )

    def select_result(
        self,
        *,
        contract_id: str,
        run_id: str,
        expected_document_version: int,
        expected_analysis_version: int,
        actor: str,
        operation_id: str,
        change_reason: str = "",
        decisions: tuple[ContextDecision, ...] = (),
        expected_source: str = "",
        acknowledged: bool = False,
    ) -> dict:
        _versions(expected_document_version, expected_analysis_version)
        actor = text(actor, label="Responsável pela seleção", maximum=80)
        if (
            not isinstance(change_reason, str)
            or not isinstance(decisions, tuple)
            or any(not isinstance(item, ContextDecision) for item in decisions)
        ):
            raise ValidationError("Informe justificativa e decisões de contexto válidas.")
        if change_reason:
            change_reason = text(change_reason, label="Motivo da alteração", maximum=500)
        arguments = {
            "contract_id": request_id(contract_id),
            "run_id": request_id(run_id),
            "expected_document_version": expected_document_version,
            "expected_analysis_version": expected_analysis_version,
            "actor": actor,
            "change_reason": change_reason,
            "decisions": decisions,
            "expected_source": expected_source,
            "acknowledged": acknowledged,
            "kernel": self.kernel,
        }
        payload = {**arguments, "decisions": [asdict(item) for item in decisions]}
        return self.store.select_result(
            **arguments, request_id=request_id(operation_id), fingerprint=fingerprint(payload)
        )

    def interrupt(
        self, contract_id: str, run_id: str, *, actor: str, operation_id: str, acknowledged: bool
    ) -> dict:
        if acknowledged is not True:
            raise ValidationError(
                "Declare que deseja encerrar a tentativa incompleta antes de refazer."
            )
        arguments = {
            "contract_id": request_id(contract_id),
            "run_id": request_id(run_id),
            "actor": text(actor, label="Responsável pela recuperação", maximum=80),
        }
        return self.store.interrupt(
            **arguments, request_id=request_id(operation_id), fingerprint=fingerprint(arguments)
        )

    def context(self, contract_id: str, run_id: str) -> dict:
        return self.store.context(request_id(contract_id), request_id(run_id))

    def list_runs(self, contract_id: str) -> list[dict]:
        return self.store.list_runs(request_id(contract_id))
