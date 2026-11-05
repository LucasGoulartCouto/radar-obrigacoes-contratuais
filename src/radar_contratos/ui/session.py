"""Atualização explícita da base e dos rascunhos que dependem dela."""

import streamlit as st


def refresh_document_context(contract_id: str) -> None:
    for prefix in ("documents", "review"):
        st.session_state.pop(f"{prefix}_snapshot:{contract_id}", None)
        key = f"{prefix}_generation:{contract_id}"
        st.session_state[key] = st.session_state.get(key, 0) + 1
