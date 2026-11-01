"""Levantamento manual e conferência explícita do case sintético."""

from datetime import date
from uuid import uuid4

import streamlit as st

from radar_contratos.application.documents import DocumentService
from radar_contratos.application.reviews import ReviewService
from radar_contratos.domain.contracts import Contract
from radar_contratos.domain.documents import PreparedDocument
from radar_contratos.domain.reviews import AnalysisSnapshot, EvidenceInput, ManualDraft
from radar_contratos.errors import RadarError

KINDS = {"termination": "Término do ciclo", "non_renewal_notice": "Aviso de não renovação"}
MODES = {
    "events": "Informar marcos",
    "empty": "Sem marcos no recorte",
    "blocked": "Registrar impedimento",
}
UNITS = {
    "calendar_days": "Dias corridos explícitos",
    "undefined": "Unidade não definida",
    "other": "Outra unidade",
}
ANCHORS = {
    "end_date": "Término informado",
    "unknown": "Evento sem data conhecida",
    "other": "Outro evento",
}


def _evidence(
    label: str, documents: tuple[PreparedDocument, ...], key: str, default: dict | None = None
) -> EvidenceInput:
    st.write(label)
    position = st.selectbox(
        f"Documento — {label}",
        options=list(range(len(documents))),
        index=default["document_position"] if default else 0,
        format_func=lambda value: f"Documento {value + 1}",
        key=f"{key}:document",
    )
    lines = documents[position].reference_text.split("\n")
    initial = (
        (default["start_line"], default["end_line"])
        if default and default["document_position"] == position
        else (1, 1)
    )
    if len(lines) > 1:
        start, end = st.slider(
            f"Linhas — {label}",
            min_value=1,
            max_value=len(lines),
            value=initial,
            key=f"{key}:lines:{position}",
        )
    else:
        start, end = 1, 1
        st.caption("Linha 1")
    quote = "\n".join(lines[start - 1 : end])
    st.code(quote, language=None, wrap_lines=True)
    return EvidenceInput(position, start, end, quote)


def _show_analysis(analysis: AnalysisSnapshot) -> None:
    st.caption(
        f"Levantamento {analysis.analysis_version} · "
        f"revisão documental {analysis.document_version} · método manual"
    )
    st.text(f"Registrado por {analysis.actor}")
    if analysis.change_reason:
        st.text(f"Motivo da correção: {analysis.change_reason}")
    values = analysis.payload["input"]
    if values["end_date"]:
        st.write(f"Término informado: {values['end_date']}")
    if values["notice_days"] is not None:
        st.write(
            f"Antecedência: {values['notice_days']} · "
            f"{UNITS.get(values['notice_unit'], values['notice_unit'])}"
        )
    if analysis.payload["blockers"]:
        st.warning("Este levantamento tem impedimentos; a confirmação fica bloqueada.")
        for reason in analysis.payload["blockers"]:
            st.text(reason)
    elif analysis.payload["candidate_events"]:
        st.dataframe(
            [
                {"Candidato": KINDS[item["kind"]], "Data calculada/informada": item["date"]}
                for item in analysis.payload["candidate_events"]
            ],
            hide_index=True,
            width="stretch",
        )
    else:
        st.info(
            "Conferido sem eventos no recorte."
            if analysis.review_id and analysis.is_current
            else "Levantamento sem candidatos no recorte. Consulte sua situação de conferência."
        )
    for field, evidence in analysis.payload["evidence"].items():
        label = {"end_date": "Término", "notice_rule": "Aviso", "blocker": "Impedimento"}[field]
        st.caption(
            f"{label} · documento {evidence['document_position'] + 1} · "
            f"linhas {evidence['start_line']}–{evidence['end_line']}"
        )
        st.code(evidence["quote"], language=None, wrap_lines=True)


def _history(service: ReviewService, contract_id: str) -> None:
    history = service.list_history(contract_id)
    if not history:
        return
    with st.expander("Histórico de levantamentos e conferências"):
        by_id = {item.id: item for item in history}
        selected = st.selectbox(
            "Levantamento para consultar",
            options=list(by_id),
            format_func=lambda identifier: (
                f"Levantamento {by_id[identifier].number} · "
                f"revisão {by_id[identifier].document_version} · "
                + ("base atual" if by_id[identifier].is_current else "base anterior/desatualizada")
            ),
            key=f"review_history:{contract_id}",
        )
        historical = service.get_analysis(contract_id, selected)
        if historical:
            if not historical.is_current:
                st.warning("Registro histórico; seus eventos não representam a base atual.")
            _show_analysis(historical)
            if historical.review_id:
                st.text(f"Conferência histórica por {historical.reviewer}")


def render_reviews(service: ReviewService, documents: DocumentService, contract: Contract) -> None:
    st.subheader("Candidatos e conferência")
    st.caption("Levantamento manual com dados sintéticos. Salvar candidatos não confirma eventos.")
    revisions = documents.list_revisions(contract.id)
    current_revision = revisions[0] if revisions else None
    if current_revision is None or current_revision.document_count == 0:
        st.info("Receba documentos para iniciar o levantamento manual.")
        _history(service, contract.id)
        return
    source = documents.get_documents(
        contract.id, current_revision.id, current_revision.source_request_id
    )
    snapshot_key = f"review_snapshot:{contract.id}"
    generation_key = f"review_generation:{contract.id}"
    base = (contract.document_version, contract.analysis_version)
    st.session_state.setdefault(snapshot_key, base)
    st.session_state.setdefault(generation_key, 0)
    flash = f"review_flash:{contract.id}"
    if flash in st.session_state:
        st.success(st.session_state.pop(flash))
    if st.button("Atualizar conferência", key=f"review_refresh:{contract.id}"):
        st.session_state[snapshot_key] = base
        st.session_state[generation_key] += 1
        st.rerun()
    if st.session_state[snapshot_key] != base:
        st.error("A base ou o levantamento mudou. Use Atualizar conferência antes de continuar.")
        return
    analysis = service.get_analysis(contract.id)
    if analysis is not None:
        _show_analysis(analysis)
        if not analysis.is_current:
            st.warning("A regra mudou. Registre outro levantamento antes de confirmar.")
        elif analysis.review_id:
            st.success("Conferência registrada para esta base.")
            st.text(f"Conferido por {analysis.reviewer}")
        elif not analysis.payload["blockers"]:
            actor = st.text_input(
                "Responsável pela conferência (simulação)",
                value="Marina (simulação)",
                key=f"review_actor:{analysis.id}",
            )
            acknowledged = st.checkbox(
                "Conferi os campos, as evidências e a cobertura desta revisão.",
                key=f"review_ack:{analysis.id}",
            )
            empty_acknowledged = False
            if not analysis.payload["candidate_events"]:
                empty_acknowledged = st.checkbox(
                    "Conferi explicitamente que não há eventos deste recorte no texto completo.",
                    key=f"review_empty:{analysis.id}",
                )
            request_key = f"review_request:{analysis.id}"
            st.session_state.setdefault(request_key, str(uuid4()))
            if st.button("Confirmar conferência", key=f"review_confirm:{analysis.id}"):
                try:
                    service.confirm(
                        contract_id=contract.id,
                        analysis_id=analysis.id,
                        expected_document_version=analysis.document_version,
                        expected_analysis_version=analysis.analysis_version,
                        expected_rule_version=analysis.payload["rule_version"],
                        actor=actor,
                        request_id=st.session_state[request_key],
                        acknowledged=acknowledged,
                        empty_acknowledged=empty_acknowledged,
                    )
                except RadarError as exc:
                    st.error(str(exc))
                else:
                    st.session_state[flash] = (
                        "Conferência registrada. Consulte os eventos da base atual."
                    )
                    st.rerun()
    events = service.current_events(contract.id)
    st.write("Eventos conferidos da base atual")
    if events:
        st.dataframe(
            [{"Evento": KINDS[item["kind"]], "Data": item["date"]} for item in events],
            hide_index=True,
            width="stretch",
        )
    else:
        st.info("Nenhum evento confirmado válido para a base atual.")

    key = f"manual:{contract.id}:{st.session_state[generation_key]}:{contract.analysis_version}"
    previous = analysis.payload["input"] if analysis and analysis.is_current else None
    with st.expander("Registrar ou corrigir levantamento manual", expanded=analysis is None):
        mode = st.radio(
            "Resultado do levantamento",
            options=list(MODES),
            index=list(MODES).index(previous["mode"]) if previous else 0,
            format_func=lambda value: MODES[value],
            key=f"{key}:mode",
        )
        end_date = end_evidence = notice_days = notice_evidence = blocker_evidence = None
        notice_unit, notice_anchor, blocker_reason = "calendar_days", "end_date", ""
        if mode == "events":
            previous_date = (
                date.fromisoformat(previous["end_date"])
                if previous and previous["end_date"]
                else None
            )
            end_date = st.date_input(
                "Término explícito do ciclo",
                value=previous_date,
                format="DD/MM/YYYY",
                key=f"{key}:end",
            )
            end_evidence = _evidence(
                "Trecho do término",
                source,
                f"{key}:end_evidence",
                previous["end_evidence"] if previous else None,
            )
            has_notice = st.checkbox(
                "Há aviso de não renovação vinculado ao ciclo informado.",
                value=previous is not None and previous["notice_days"] is not None,
                key=f"{key}:has_notice",
            )
            if has_notice:
                notice_days = st.number_input(
                    "Antecedência informada",
                    min_value=0,
                    value=previous["notice_days"]
                    if previous and previous["notice_days"] is not None
                    else 0,
                    step=1,
                    key=f"{key}:days",
                )
                notice_unit = st.selectbox(
                    "Unidade do prazo",
                    options=list(UNITS),
                    index=list(UNITS).index(previous["notice_unit"]) if previous else 0,
                    format_func=lambda value: UNITS[value],
                    key=f"{key}:unit",
                )
                notice_anchor = st.selectbox(
                    "Referência do aviso",
                    options=list(ANCHORS),
                    index=list(ANCHORS).index(previous["notice_anchor"]) if previous else 0,
                    format_func=lambda value: ANCHORS[value],
                    key=f"{key}:anchor",
                )
                notice_evidence = _evidence(
                    "Trecho do aviso",
                    source,
                    f"{key}:notice_evidence",
                    previous["notice_evidence"] if previous else None,
                )
        elif mode == "blocked":
            blocker_reason = st.text_input(
                "Motivo do impedimento",
                max_chars=500,
                value=previous["blocker_reason"] if previous else "",
                key=f"{key}:reason",
            )
            blocker_evidence = _evidence(
                "Trecho do impedimento",
                source,
                f"{key}:blocker_evidence",
                previous["blocker_evidence"] if previous else None,
            )
        else:
            st.info(
                "O resultado vazio fica pendente até uma conferência explícita do texto completo."
            )
        actor = st.text_input(
            "Responsável pelo levantamento (simulação)",
            value="Rafael (simulação)",
            key=f"{key}:actor",
        )
        synthetic = st.checkbox(
            "Este levantamento usa apenas os documentos sintéticos do case.", key=f"{key}:synthetic"
        )
        request_key = f"{key}:request"
        change_reason = (
            st.text_input(
                "Motivo da correção (obrigatório se mudar o levantamento atual)",
                max_chars=500,
                key=f"{key}:change_reason",
            )
            if analysis
            else ""
        )
        st.session_state.setdefault(request_key, str(uuid4()))
        if st.button("Salvar levantamento (não confirma)", key=f"{key}:save"):
            try:
                service.register(
                    contract_id=contract.id,
                    expected_document_version=base[0],
                    expected_analysis_version=base[1],
                    actor=actor,
                    request_id=st.session_state[request_key],
                    synthetic=synthetic,
                    change_reason=change_reason,
                    draft=ManualDraft(
                        mode,
                        end_date,
                        end_evidence,
                        notice_days,
                        notice_evidence,
                        notice_unit,
                        notice_anchor,
                        blocker_reason,
                        blocker_evidence,
                    ),
                )
            except RadarError as exc:
                st.error(str(exc))
            else:
                st.session_state.pop(snapshot_key, None)
                st.session_state[generation_key] += 1
                st.session_state[flash] = "Levantamento salvo. A conferência é uma ação separada."
                st.rerun()

    _history(service, contract.id)
