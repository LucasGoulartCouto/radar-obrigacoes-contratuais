"""Agenda de consulta; os controles não alteram a base conferida."""

from datetime import date

import streamlit as st

from radar_contratos.application.agenda import AgendaService
from radar_contratos.application.reviews import ReviewService
from radar_contratos.domain.agenda import (
    EVENT_LABELS,
    AgendaEvent,
    CoverageState,
    summarize_coverage,
)
from radar_contratos.domain.dates import TemporalStatus


def _source(event: AgendaEvent, reviews: ReviewService) -> None:
    analysis = reviews.get_analysis(event.contract_id, event.analysis_id)
    if analysis is None or not analysis.is_current or analysis.review_id != event.review_id:
        st.warning("A base deste evento mudou. Atualize a agenda antes de consultar sua origem.")
        return
    st.text(
        f"Revisão documental {event.document_version} · Levantamento {event.analysis_version}\n"
        f"Conferido por {event.reviewer} · {event.reviewed_at_utc} (UTC)"
    )
    evidence = analysis.payload["evidence"]
    for key, label in (("end_date", "Término informado"), ("notice_rule", "Regra do aviso")):
        if key == "notice_rule" and event.kind != "non_renewal_notice":
            continue
        item = evidence[key]
        st.text(
            f"{label} · Documento {item['document_position'] + 1} · "
            f"Linhas {item['start_line']} a {item['end_line']}"
        )
        st.code(item["quote"], language=None)
    if event.kind == "non_renewal_notice":
        data = analysis.payload["input"]
        st.text(
            f"Cálculo: {date.fromisoformat(data['end_date']):%d/%m/%Y} "
            f"menos {data['notice_days']} dias corridos = {event.event_date:%d/%m/%Y}."
        )
    st.caption("A conferência do significado é manual. O trecho é exibido como dado.")


def render_agenda(service: AgendaService, reviews: ReviewService) -> None:
    st.subheader("Agenda e cobertura")
    st.caption(
        "Simulação com horizonte fixo de 30 dias. A data de referência não é o relógio real. "
        "Uma data ultrapassada não comprova descumprimento ou ação realizada."
    )
    reference = st.date_input(
        "Data de referência da simulação",
        value=date(2027, 5, 1),
        min_value=date.min,
        max_value=date.max,
        format="DD/MM/YYYY",
        key="agenda:reference",
    )
    statuses = st.multiselect(
        "Situações de prazo",
        options=list(TemporalStatus),
        default=[TemporalStatus.PAST, TemporalStatus.TODAY, TemporalStatus.SOON],
        key="agenda:statuses",
    )
    kinds = st.selectbox(
        "Tipo de evento na agenda",
        options=["all", *EVENT_LABELS],
        format_func=lambda kind: "Todos os tipos" if kind == "all" else EVENT_LABELS[kind],
        key="agenda:kind",
    )
    st.button("Atualizar agenda", key="agenda:refresh")
    view = (
        service.read(
            reference,
            statuses=tuple(statuses),
            kinds=tuple(EVENT_LABELS) if kinds == "all" else (kinds,),
        )
        if reference is not None
        else None
    )
    portfolio = view.portfolio if view else service.read_portfolio()
    coverage = view.coverage if view else summarize_coverage(portfolio)
    total = len(portfolio.contracts)
    st.write(
        f"Cobertura de toda a carteira: **{total} contratos**. "
        "Os filtros não alteram essa contagem."
    )
    for start in (0, 3):
        for column, (state, count) in zip(st.columns(3), coverage[start : start + 3], strict=True):
            column.metric(state.value, count)
    if total:
        with st.expander("Situação de cada contrato", expanded=True):
            st.dataframe(
                [
                    {
                        "Contrato": item.title,
                        "Situação": item.state.value,
                        "Próximo passo": item.detail,
                    }
                    for item in portfolio.contracts
                ],
                hide_index=True,
                width="stretch",
                key="agenda:coverage",
            )
        pending = sum(
            count
            for state, count in coverage
            if state not in {CoverageState.WITH_EVENTS, CoverageState.WITHOUT_EVENTS}
        )
        if pending:
            st.warning(
                f"{pending} contrato(s) com pendência. A carteira não está totalmente conferida."
            )
    if view is None:
        st.warning(
            "Informe a data de referência para consultar a agenda. A cobertura permanece acima."
        )
        return
    st.write("Eventos confirmados da base atual")
    st.caption(
        f"Referência: {reference:%d/%m/%Y} · Próximos 30 dias: dias 1 a 30, inclusive. "
        f"Exibindo {len(view.items)} de {len(view.portfolio.events)} eventos confirmados válidos. "
        "A leitura é refeita a cada interação; "
        "use Atualizar agenda para consultar mudanças externas."
    )
    if not view.items:
        st.info(
            "Nenhum evento nos filtros da agenda. Consulte a cobertura acima; "
            "ausência na lista não significa contrato conferido."
        )
        return
    st.dataframe(
        [
            {
                "Contrato": item.event.contract_title,
                "Evento": EVENT_LABELS[item.event.kind],
                "Data": item.event.event_date,
                "Dias até a data": item.days_until,
                "Situação": item.temporal_status.value,
            }
            for item in view.items
        ],
        hide_index=True,
        width="stretch",
        column_config={"Data": st.column_config.DateColumn(format="DD/MM/YYYY")},
        key="agenda:events",
    )
    with st.expander("Origem de um evento exibido"):
        by_id = {item.event.id: item.event for item in view.items}
        selected = st.selectbox(
            "Evento para consultar a origem",
            options=list(by_id),
            format_func=lambda identifier: (
                f"{by_id[identifier].contract_title} · {EVENT_LABELS[by_id[identifier].kind]} · "
                f"{by_id[identifier].event_date:%d/%m/%Y}"
            ),
            key="agenda:source",
        )
        _source(by_id[selected], reviews)
