"""Adaptador local de desenvolvimento; reutiliza o protocolo V1 sem promover o modelo."""

from time import monotonic

from radar_contratos.domain.assisted import METHOD_VERSION
from radar_contratos.domain.literal_extraction import INTERPRETATION_VERSION
from radar_contratos.domain.reviews import RULE_VERSION, ReferenceDocument
from radar_contratos.infrastructure.experiments.extraction import ExperimentDocument
from radar_contratos.infrastructure.experiments.line_local_ai import (
    PROMPT_VERSION,
    LineExtractor,
    component_hashes,
)
from radar_contratos.infrastructure.experiments.local_ai import (
    BASE_URL,
    MODEL,
    LocalInferenceError,
    request_local,
)


def method_kernel() -> dict:
    return {
        "method": METHOD_VERSION,
        "prompt": PROMPT_VERSION,
        "interpretation": INTERPRETATION_VERSION,
        "rule": RULE_VERSION,
        "components": component_hashes(),
    }


def _documents(documents):
    return tuple(ExperimentDocument(d.id, d.role, d.reference_text) for d in documents)


class OllamaLineClassifier:
    def __init__(self, digest: str, *, model: str = MODEL, base_url: str = BASE_URL):
        self.digest, self.model, self.base_url = digest, model, base_url
        LineExtractor(digest, model=model, base_url=base_url)  # validar configuração sem rede

    def descriptor(self) -> dict:
        return {
            "kernel": method_kernel(),
            "model": self.model,
            "digest": self.digest,
            "base_url": self.base_url,
            "budget_seconds": 120,
            "automatic_retries": 0,
        }

    def validate_input(self, documents: tuple[ReferenceDocument, ...]) -> None:
        LineExtractor(self.digest, model=self.model, base_url=self.base_url)._payload(
            _documents(documents)
        )

    def classify(self, documents: tuple[ReferenceDocument, ...]) -> dict:
        deadline = monotonic() + 120

        def transport(base_url, path, payload, _timeout):
            remaining = deadline - monotonic()
            if remaining <= 0:
                raise LocalInferenceError("LOCAL_TIMEOUT")
            return request_local(base_url, path, payload, remaining)

        client = LineExtractor(
            self.digest, model=self.model, base_url=self.base_url, transport=transport
        )
        client.check_model()
        client(_documents(documents))
        observation = client.observations[-1]
        return {
            "classifications": observation["classifications"],
            "abstained": observation["model_abstained"],
            "runtime_version": client.runtime_version,
            "prompt_tokens": observation.get("prompt_tokens"),
            "output_tokens": observation.get("output_tokens"),
        }
