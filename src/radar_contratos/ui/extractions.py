"""Analisar, revisar contexto e selecionar são ações explícitas e independentes."""

from uuid import uuid4

import streamlit as st

from radar_contratos.application.extractions import ExtractionService
from radar_contratos.domain.agenda import EVENT_LABELS
from radar_contratos.domain.assisted import literal_lines, prepare_assisted_analysis
from radar_contratos.domain.extraction_review import ContextDecision, source_fingerprint
from radar_contratos.errors import RadarError
from radar_contratos.ui.labels import BLOCKER_LABELS

STATES = {
    "pending": "Aguardando execução",
    "running": "Em processamento",
    "completed": "Concluída, sem confirmação",
    "failed": "Falhou",
    "interrupted": "Interrompida",
}


def render_extractions(service: ExtractionService, contract) -> None:
    st.subheader("Análise assistida dos documentos")
    st.caption(
        "IA local de desenvolvimento. Analisar e escolher um resultado não confirma eventos."
    )
    if service.classifier is None:
        st.info(
            "A IA local não está configurada neste ambiente. O levantamento manual está disponível."
        )
    actor = st.text_input(
        "Responsável pela análise assistida (simulação)",
        value="Rafael (simulação)",
        key=f"extraction_actor:{contract.id}",
    )
    synthetic = st.checkbox(
        "Esta análise usa somente os documentos sintéticos do case.",
        key=f"extraction_synthetic:{contract.id}",
    )
    key = (
        f"extraction_request:{contract.id}:{contract.document_version}:{contract.analysis_version}"
    )
    st.session_state.setdefault(key, str(uuid4()))
    if st.button(
        "Analisar documentos (não confirma)",
        disabled=service.classifier is None or contract.document_version == 0,
    ):
        try:
            receipt = service.request(
                contract_id=contract.id,
                expected_document_version=contract.document_version,
                expected_analysis_version=contract.analysis_version,
                actor=actor,
                operation_id=st.session_state[key],
                synthetic=synthetic,
            )
            with st.spinner("Analisando os documentos no computador..."):
                service.execute(contract.id, receipt["run_id"])
        except RadarError as exc:
            st.error(str(exc))
        else:
            st.session_state[f"extraction_history:{contract.id}"] = receipt["run_id"]
            st.session_state.pop(key, None)
            st.rerun()
    runs = service.list_runs(contract.id)
    if not runs:
        return
    with st.expander("Tentativas de análise e recuperação", expanded=True):
        by_id = {item["run_id"]: item for item in runs}
        selected = st.selectbox(
            "Tentativa para consultar",
            options=list(by_id),
            format_func=lambda value: (
                f"Tentativa {by_id[value]['number']} · "
                f"revisão {by_id[value]['document_version']} · "
                f"{STATES[by_id[value]['status']]}"
            ),
            key=f"extraction_history:{contract.id}",
        )
        run = by_id[selected]
        st.text(f"Solicitada por {run['actor']} · {run['created_at_utc']} (UTC)")
        if run["status"] in {"pending", "running"}:
            st.warning(
                "Tentativa incompleta. Se a execução foi interrompida, encerre-a antes de refazer. "
                "Encerrar o registro não cancela uma análise que ainda esteja em execução."
            )
            ack = st.checkbox(
                "Quero encerrar esta tentativa incompleta para poder refazer.",
                key=f"interrupt_ack:{selected}",
            )
            if st.button("Encerrar tentativa incompleta", key=f"interrupt:{selected}"):
                try:
                    service.interrupt(
                        contract.id,
                        selected,
                        actor=actor,
                        operation_id=str(uuid4()),
                        acknowledged=ack,
                    )
                except RadarError as exc:
                    st.error(str(exc))
                else:
                    st.session_state.pop(key, None)
                    st.rerun()
            return
        if run["status"] in {"failed", "interrupted"}:
            st.error(
                "A tentativa não produziu uma análise concluída. Use Analisar documentos "
                "para uma nova tentativa; o histórico será preservado."
            )
            return
        context = service.context(contract.id, selected)
        lines = literal_lines(context["documents"])
        output = run["output"]
        preview = prepare_assisted_analysis(
            context["documents"],
            output["classifications"],
            output["abstained"],
            known_amendment=context["known_amendment"],
        )
        with st.expander("Texto completo e classificações da tentativa"):
            for document in context["documents"]:
                st.text(f"Documento {document.position + 1}")
                st.code(
                    "\n".join(
                        f"{n}: {line}"
                        for n, line in enumerate(document.reference_text.split("\n"), 1)
                    ),
                    language=None,
                    wrap_lines=True,
                )
            st.json(output["classifications"])
        if run["document_version"] != contract.document_version:
            st.warning(
                "Tentativa de revisão anterior. O resultado fica no histórico "
                "e não pode ser selecionado."
            )
            return
        st.caption("Resultado original da tentativa, antes de qualquer revisão de contexto.")
        if preview["blockers"]:
            st.warning(
                "Há impedimentos nesta análise. "
                "Eles não podem ser resolvidos apenas confirmando a tela."
            )
            for blocker in preview["blockers"]:
                st.text(BLOCKER_LABELS.get(blocker, blocker))
        else:
            if preview["candidate_events"]:
                st.dataframe(
                    [
                        {"Candidato": EVENT_LABELS[item["kind"]], "Data": item["date"]}
                        for item in preview["candidate_events"]
                    ],
                    hide_index=True,
                )
            else:
                st.info("Sem candidatos no recorte; exige conferência explícita do vazio.")
        decisions = []
        for finding in preview["extraction"]["original"]["findings"]:
            disposition = {
                "model_reports_unsupported": "untrusted_instruction",
                "clause_inside_illustration": "illustrative",
            }.get(finding["reason"])
            if disposition is None or finding.get("line") is None:
                continue
            line = next(item for item in lines if item.alias == finding["line"])
            if disposition == "untrusted_instruction" and not line.text.startswith(
                "INSTRUÇÃO AO ASSISTENTE:"
            ):
                continue
            st.code(line.text, language=None, wrap_lines=True)
            decision_label = (
                "Conferi que este pedido ao assistente não define condição contratual."
                if disposition == "untrusted_instruction"
                else "Conferi que este trecho pertence ao exemplo, sem definir a condição efetiva."
            )
            if st.checkbox(
                decision_label,
                key=f"context_choice:{selected}:{line.alias}",
            ):
                reason = st.text_input(
                    "Justificativa da revisão de contexto",
                    key=f"context_reason:{selected}:{line.alias}",
                    max_chars=500,
                )
                decisions.append(ContextDecision(line.alias, disposition, line.text, reason))
        acknowledged = (
            st.checkbox(
                "Conferi o texto completo e o contexto das retenções selecionadas.",
                key=f"context_ack:{selected}",
            )
            if decisions
            else False
        )
        reason = (
            st.text_input(
                "Motivo para substituir o levantamento atual",
                max_chars=500,
                key=f"selection_reason:{selected}:{contract.analysis_version}",
            )
            if contract.analysis_version
            else ""
        )
        if st.button(
            "Usar resultado para conferência (não confirma)", key=f"select_run:{selected}"
        ):
            try:
                service.select_result(
                    contract_id=contract.id,
                    run_id=selected,
                    expected_document_version=contract.document_version,
                    expected_analysis_version=contract.analysis_version,
                    actor=actor,
                    operation_id=str(uuid4()),
                    change_reason=reason,
                    decisions=tuple(decisions),
                    expected_source=source_fingerprint(
                        lines,
                        output["classifications"],
                        abstained=output["abstained"],
                        known_amendment=context["known_amendment"],
                    ),
                    acknowledged=acknowledged,
                )
            except RadarError as exc:
                st.error(str(exc))
            else:
                st.session_state.pop(f"review_snapshot:{contract.id}", None)
                st.rerun()
