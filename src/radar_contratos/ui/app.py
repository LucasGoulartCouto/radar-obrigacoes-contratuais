"""Agenda, cobertura e manutenção dos contratos fictícios."""

from uuid import uuid4

import streamlit as st

from radar_contratos.bootstrap import (
    build_agenda_service,
    build_document_service,
    build_extraction_service,
    build_review_service,
    build_service,
)
from radar_contratos.config import Settings
from radar_contratos.errors import RadarError
from radar_contratos.ui.agenda import render_agenda
from radar_contratos.ui.documents import render_documents
from radar_contratos.ui.extractions import render_extractions
from radar_contratos.ui.reviews import render_reviews


def render() -> None:
    st.set_page_config(page_title="Radar de Obrigações Contratuais", page_icon="◉", layout="wide")
    st.title("Radar de Obrigações Contratuais")
    st.caption("Agência Prisma · Ambiente de estudo com dados sintéticos")
    st.write("Consulte os prazos conferidos e acompanhe as pendências dos contratos fictícios.")

    try:
        settings = Settings.from_environment()
        service, engine = build_service(settings)
        documents = build_document_service(settings, engine)
        reviews = build_review_service(engine)
        agenda = build_agenda_service(engine)
        extractions = build_extraction_service(settings, engine)
    except RadarError as exc:
        st.error(str(exc))
        st.stop()

    try:
        st.session_state.setdefault("register_request_id", str(uuid4()))
        with st.form("register_contract", clear_on_submit=True):
            st.subheader("Cadastrar contrato fictício")
            title = st.text_input("Nome do contrato", max_chars=200)
            actor = st.text_input("Responsável pelo registro (simulação)", value="Operador local")
            synthetic = st.checkbox("Este cadastro faz parte do case fictício da Agência Prisma.")
            submitted = st.form_submit_button("Cadastrar contrato")
        if submitted:
            if not synthetic:
                st.warning("Use apenas cadastros fictícios neste ambiente de estudo.")
            else:
                try:
                    service.register(
                        title=title,
                        actor=actor,
                        request_id=st.session_state["register_request_id"],
                    )
                except RadarError as exc:
                    st.error(str(exc))
                else:
                    st.session_state["register_request_id"] = str(uuid4())
                    st.success(
                        "Contrato cadastrado. Você já pode adicionar os documentos sintéticos."
                    )

        try:
            render_agenda(agenda, reviews)
        except RadarError as exc:
            st.error(str(exc))
        contracts = service.list_contracts()
        st.subheader("Documentos e conferência por contrato")
        if not contracts:
            st.info("Cadastre o primeiro contrato fictício para começar.")
        else:
            by_id = {contract.id: contract for contract in contracts}
            selected_id = st.selectbox(
                "Contrato para editar o nome",
                options=list(by_id),
                format_func=lambda identifier: by_id[identifier].title,
            )
            selected = by_id[selected_id]
            snapshot_key = f"edit_snapshot:{selected_id}"
            st.session_state.setdefault(snapshot_key, selected.record_version)
            with st.form(f"rename:{selected_id}"):
                new_title = st.text_input("Novo nome do contrato", value=selected.title)
                rename_submitted = st.form_submit_button("Salvar nome")
            if rename_submitted:
                try:
                    service.rename(
                        contract_id=selected_id,
                        title=new_title,
                        expected_version=st.session_state[snapshot_key],
                        actor="Operador local",
                        request_id=str(uuid4()),
                    )
                except RadarError as exc:
                    st.error(str(exc))
                    st.session_state.pop(snapshot_key, None)
                else:
                    st.session_state.pop(snapshot_key, None)
                    st.rerun()
            render_documents(documents, selected)
            render_extractions(extractions, selected)
            render_reviews(reviews, documents, selected)
        st.caption(
            "Análise assistida local, levantamento manual, conferência e agenda. "
            "Toda sugestão exige conferência explícita; nenhuma mensagem de negócio é enviada."
        )
    finally:
        engine.dispose()


render()
