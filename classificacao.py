"""Classificação das avaliações em POSITIVA ou NEGATIVA.

Quarta etapa do fluxo:
leitura → pré-processamento → métricas → classificação → resultados

Regras do enunciado, seção 6, aplicadas SEPARADAMENTE a cada métrica:

| Métrica     | Condição                  | Classificação |
|-------------|---------------------------|---------------|
| Jaccard     | jaccard_pos >  jaccard_neg | POSITIVA      |
| Jaccard     | jaccard_pos <= jaccard_neg | NEGATIVA      |
| Levenshtein | lev_pos <  lev_neg         | POSITIVA      |
| Levenshtein | lev_pos >= lev_neg         | NEGATIVA      |

Os sinais são opostos porque Jaccard é SIMILARIDADE (maior = mais parecido) e
Levenshtein é DISTÂNCIA (menor = mais parecido). Empates viram NEGATIVA nas
duas métricas, por regra do enunciado.
"""

import pandas as pd

# Rótulos em maiúsculas, como na tabela da seção 6 do enunciado.
POSITIVA = "POSITIVA"
NEGATIVA = "NEGATIVA"


def classificar_jaccard(jaccard_pos: float, jaccard_neg: float) -> str:
    """Classifica uma avaliação pela similaridade de Jaccard.

    Recebe a similaridade com a referência positiva e com a negativa (valores
    completos, sem arredondar). Devolve POSITIVA se a avaliação for MAIS
    parecida com a positiva (pos > neg); caso contrário, inclusive no empate,
    devolve NEGATIVA (enunciado, seção 6).
    """
    if jaccard_pos > jaccard_neg:
        return POSITIVA
    return NEGATIVA


def classificar_levenshtein(lev_pos: int, lev_neg: int) -> str:
    """Classifica uma avaliação pela distância de Levenshtein.

    Recebe a distância até a referência positiva e até a negativa. Devolve
    POSITIVA se a avaliação estiver MAIS PERTO da positiva (pos < neg); caso
    contrário, inclusive no empate, devolve NEGATIVA (enunciado, seção 6).
    """
    if lev_pos < lev_neg:
        return POSITIVA
    return NEGATIVA


def classificar_avaliacoes(df: pd.DataFrame) -> pd.DataFrame:
    """Classifica todas as avaliações pelas duas métricas.

    Recebe o DataFrame de calcular_metricas() (com jaccard_pos, jaccard_neg,
    lev_pos e lev_neg) e devolve uma CÓPIA com duas colunas novas:
    class_jaccard e class_lev. O DataFrame recebido não é modificado.

    Usa .apply(..., axis=1) porque cada classificação depende de DUAS colunas
    da mesma linha: o pandas entrega a linha inteira para a função.
    """
    resultado = df.copy()
    resultado["class_jaccard"] = resultado.apply(
        lambda linha: classificar_jaccard(linha["jaccard_pos"], linha["jaccard_neg"]),
        axis=1,
    )
    resultado["class_lev"] = resultado.apply(
        lambda linha: classificar_levenshtein(linha["lev_pos"], linha["lev_neg"]),
        axis=1,
    )
    return resultado
