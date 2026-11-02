"""Motivos apresentados ao operador, sem códigos internos no fluxo principal."""

BLOCKER_LABELS = {
    "known_amendment_history": "Há aditivo conhecido no histórico; consolidação fora do recorte.",
    "amendment_not_supported": "Há indicação de aditivo; não é possível confirmar seus efeitos.",
    "unsupported_scope": "Há trecho cujo contexto exige revisão ou informação adicional.",
    "incomplete_analysis": "A análise não conseguiu concluir a leitura de todo o conjunto.",
    "undefined_day_unit": "A unidade de dias corridos não está explícita.",
    "unsupported_day_unit": "O prazo usa uma unidade não suportada, como meses ou dias úteis.",
    "invalid_notice_days": "A antecedência contém número negativo ou fracionário.",
    "conflicting_notice_days": "Há divergência entre as regras de antecedência.",
    "conflicting_end_dates": "Há datas de término conflitantes; não é possível escolher uma.",
    "invalid_end_date": "O documento contém uma data de término impossível.",
    "unsupported_anchor": "O prazo não está ligado a um término explícito suportado.",
}
