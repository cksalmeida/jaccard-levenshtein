"""Avaliações de referência usadas na classificação.

Textos copiados exatamente do enunciado (docs/enunciado.pdf, seção 3,
"Avaliações de referência", p. 1–2), sem nenhuma alteração. A limpeza desses
textos é feita depois, pelo mesmo pré-processamento aplicado às avaliações
(preprocessamento.py), para que a comparação seja justa.
"""

# Enunciado, seção 3 — Referência positiva.
REFERENCIA_POSITIVA = (
    "O produto possui excelente qualidade, chegou rapidamente e atendeu "
    "completamente às minhas expectativas. Gostei muito da compra e recomendo "
    "este produto para outras pessoas."
)

# Enunciado, seção 3 — Referência negativa.
REFERENCIA_NEGATIVA = (
    "O produto possui péssima qualidade, apresentou problemas logo após a "
    "compra e não atendeu às minhas expectativas. Fiquei muito decepcionado e "
    "não recomendo este produto."
)
