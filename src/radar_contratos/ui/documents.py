"""Entrada e consulta documental, com estado de negócio consultado no serviço."""

from math import ceil
from uuid import uuid4

import streamlit as st

from radar_contratos.application.documents import DocumentService
from radar_contratos.domain.contracts import Contract
from radar_contratos.domain.documents import DocumentInput, DocumentRole
from radar_contratos.errors import RadarError, StaleRecordError, ValidationError

ROLE_LABELS = {
    DocumentRole.BASE: "Documento base",
    DocumentRole.AMENDMENT: "Aditivo",
    DocumentRole.REPLACEMENT: "Substituição",
    DocumentRole.UNKNOWN: "Papel desconhecido",
}


def render_documents(service: DocumentService, contract: Contract) -> None:
    st.subheader("Documentos do contrato")
    flash_key = f"documents_flash:{contract.id}"
    if flash_key in st.session_state:
        st.success(st.session_state.pop(flash_key))
    revisions = service.list_revisions(contract.id)
    current = revisions[0] if revisions else None
    originals = (
        service.get_documents(contract.id, current.id, current.source_request_id) if current else ()
    )
    if service.current_states().get(contract.id) == "Bloqueado: aditivo declarado":
        st.warning(
            "Há aditivo declarado no histórico: a confirmação fica bloqueada neste recorte. "
            "Retirar ou mudar o papel do arquivo não resolve esse bloqueio. "
            "O Radar ainda não analisa nem consolida o conteúdo dos documentos."
        )
    st.write("Monte o conjunto completo da próxima revisão. As anteriores ficam no histórico.")
    limits = service.limits
    st.caption(
        f"Texto .txt em UTF-8 · até {limits.max_documents} documentos · "
        f"{limits.max_document_bytes:,} bytes por arquivo · "
        f"{limits.max_revision_bytes:,} bytes no conjunto. Use somente dados sintéticos."
    )
    snapshot_key = f"documents_snapshot:{contract.id}"
    generation_key = f"documents_generation:{contract.id}"
    st.session_state.setdefault(snapshot_key, contract.document_version)
    st.session_state.setdefault(generation_key, 0)
    generation = st.session_state[generation_key]
    prefix = f"documents:{contract.id}:{generation}"
    if st.button("Atualizar documentos", key=f"refresh:{contract.id}"):
        st.session_state.pop(snapshot_key, None)
        st.session_state[generation_key] += 1
        st.rerun()
    if st.session_state[snapshot_key] != contract.document_version:
        st.error("Os documentos mudaram em outro envio. Atualize antes de salvar.")
        st.info("Use Atualizar documentos para carregar e conferir o conjunto atual.")
        return
    kept = st.multiselect(
        "Documentos atuais que continuarão na nova revisão",
        options=list(range(len(originals))),
        default=list(range(len(originals))),
        key=f"{prefix}:keep",
        format_func=lambda index: f"{index + 1} · {originals[index].filename}",
    )
    uploaded = st.file_uploader(
        "Adicionar documentos sintéticos",
        type=["txt"],
        accept_multiple_files=True,
        max_upload_size=max(1, ceil(limits.max_document_bytes / 1_048_576)),
        key=f"{prefix}:upload",
    )
    st.session_state.setdefault(f"{prefix}:request", str(uuid4()))
    with st.form(f"{prefix}:form"):
        retained_roles = []
        for index in kept:
            st.text(f"Documento mantido {index + 1}: {originals[index].filename}")
            retained_roles.append(
                st.selectbox(
                    f"Papel do documento mantido {index + 1}",
                    options=list(DocumentRole),
                    index=list(DocumentRole).index(originals[index].role),
                    format_func=lambda role: ROLE_LABELS[role],
                    key=f"{prefix}:role:kept:{index}",
                )
            )
        new_roles = []
        for index, item in enumerate(uploaded):
            st.text(f"Arquivo novo {index + 1}: {item.name}")
            new_roles.append(
                st.selectbox(
                    f"Papel do arquivo novo {index + 1}",
                    options=list(DocumentRole),
                    format_func=lambda role: ROLE_LABELS[role],
                    key=f"{prefix}:role:new:{index}",
                )
            )
        actor = st.text_input("Responsável pelo envio (simulação)", value="Operador local")
        synthetic = st.checkbox("Os documentos enviados são sintéticos e pertencem ao case Prisma.")
        allow_empty = False
        if current and not kept and not uploaded:
            allow_empty = st.checkbox(
                "Quero retirar todos os documentos da revisão atual, preservando o histórico."
            )
        submitted = st.form_submit_button("Salvar conjunto documental")
    if submitted:
        try:
            if len(kept) + len(uploaded) > limits.max_documents:
                raise ValidationError(f"O conjunto aceita até {limits.max_documents} documentos.")
            if any(item.size > limits.max_document_bytes for item in uploaded):
                raise ValidationError(f"Um documento excede {limits.max_document_bytes} bytes.")
            inputs = tuple(
                DocumentInput(originals[index].filename, originals[index].original_bytes, role)
                for index, role in zip(kept, retained_roles, strict=True)
            ) + tuple(
                DocumentInput(item.name, item.getvalue(), role)
                for item, role in zip(uploaded, new_roles, strict=True)
            )
            receipt = service.submit(
                contract_id=contract.id,
                documents=inputs,
                expected_version=st.session_state[snapshot_key],
                actor=actor,
                request_id=st.session_state[f"{prefix}:request"],
                synthetic=synthetic,
                allow_empty=allow_empty,
            )
        except RadarError as exc:
            st.error(str(exc))
            if isinstance(exc, StaleRecordError):
                st.info("Use Atualizar documentos e confira o conjunto antes de tentar novamente.")
        else:
            st.session_state[flash_key] = (
                f"Revisão {receipt.revision_number} registrada."
                if receipt.created_revision
                else f"Mesmo conjunto documental: revisão {receipt.revision_number} mantida. "
                "O arquivo recebido foi preservado no histórico de envios."
            )
            st.session_state.pop(snapshot_key, None)
            st.session_state[generation_key] += 1
            st.rerun()

    if not revisions:
        st.info("Este contrato ainda não recebeu documentos.")
        return
    st.write("Histórico documental")
    by_id = {revision.id: revision for revision in revisions}
    selected_id = st.selectbox(
        "Revisão para consultar",
        options=list(by_id),
        key=f"history:{contract.id}",
        format_func=lambda identifier: (
            f"Revisão {by_id[identifier].number}"
            + (
                " · atual"
                if by_id[identifier].number == contract.document_version
                else " · anterior"
            )
        ),
    )
    revision = by_id[selected_id]
    st.caption(
        f"Registrada em {revision.created_at_utc} (UTC) por {revision.actor}. "
        "Receber documentos não significa que eles foram analisados ou conferidos."
    )
    submissions = service.list_submissions(contract.id, revision.id)
    by_request = {receipt.request_id: receipt for receipt in submissions}
    request_id = st.selectbox(
        "Envio recebido para consultar",
        options=list(by_request),
        key=f"submission:{revision.id}",
        format_func=lambda identifier: by_request[identifier].received_at_utc + " (UTC)",
    )
    documents = service.get_documents(contract.id, revision.id, request_id)
    if not documents:
        st.info("Conjunto vazio: aguardando documentos. Isso não é uma análise sem eventos.")
    for index, document in enumerate(documents):
        with st.expander(f"Documento {index + 1} · {ROLE_LABELS[document.role]}"):
            st.text(document.filename)
            st.download_button(
                "Baixar arquivo original",
                document.original_bytes,
                file_name=document.filename,
                mime="application/octet-stream",
                key=f"download:{request_id}:{index}",
            )
            st.code(document.reference_text, language=None, line_numbers=True, wrap_lines=True)
