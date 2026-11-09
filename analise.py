"""Análise dos resultados (SPEC 05).

Última etapa do fluxo:
leitura → pré-processamento → métricas → classificação → resultados → análise.

Atende ao enunciado, seção 9: calcula os números das perguntas 1 a 6 e reúne
as EVIDÊNCIAS para as respostas escritas das perguntas 7 e 8 (que não são
escritas pelo código). Não há gabarito de sentimento real no arquivo: as
métricas são comparadas ENTRE SI, sem medir acerto.

Todas as funções recebem o DataFrame completo da SPEC 04 (saída de
classificar_avaliacoes, com texto_limpo, tokens, métricas e classificações) e
não o modificam.
"""

from pathlib import Path

import pandas as pd

from classificacao import NEGATIVA, POSITIVA
from preprocessamento import limpar_texto, tokenizar
from referencias import REFERENCIA_NEGATIVA, REFERENCIA_POSITIVA
from resultados import (
    FORMATO_CORRELACAO,
    FORMATO_INTEIRO,
    FORMATO_PERCENTUAL,
    adicionar_abas,
    adicionar_bloco,
    montar_tabela_resultados,
)

# Referências pré-processadas com as funções da SPEC 02 (mesmo tratamento das avaliações).
POSITIVA_LIMPA = limpar_texto(REFERENCIA_POSITIVA)
NEGATIVA_LIMPA = limpar_texto(REFERENCIA_NEGATIVA)
POSITIVA_PALAVRAS = set(tokenizar(POSITIVA_LIMPA))
NEGATIVA_PALAVRAS = set(tokenizar(NEGATIVA_LIMPA))

TITULO_CRUZAMENTO = "Cruzamento Jaccard × Levenshtein"

# Ao gravar no Excel, o pandas mantém só o nome das LINHAS da tabela cruzada e
# descarta o nome das COLUNAS. Este rótulo, no canto superior esquerdo, indica
# as duas direções: linhas = Jaccard, colunas = Levenshtein.
ROTULO_CANTO_CRUZAMENTO = "Jaccard ↓ / Lev. →"

# Linhas em branco entre as perguntas 1 a 6 e a tabela cruzada, na aba Resumo.
LINHAS_EM_BRANCO_RESUMO = 2

# Nomes dos indicadores que precisam de um formato de exibição próprio no Excel.
# Ficam em constantes para que o nome usado na tabela e o nome usado no
# dicionário de formatos (abaixo) sejam sempre o mesmo texto.
IND_PARCELA_POS = "Parcela média da Lev. Pos. explicada pela diferença de tamanho (%)"
IND_PARCELA_NEG = "Parcela média da Lev. Neg. explicada pela diferença de tamanho (%)"
IND_MARGEM_REL_JACCARD = "Margem relativa mediana do Jaccard (%)"
IND_MARGEM_REL_LEV = "Margem relativa mediana da Levenshtein (%)"
IND_MARGEM_ABS_LEV = "Margem absoluta mediana da Levenshtein (caracteres)"

# Correlações com o tamanho do texto: (coluna da métrica, nome do indicador, explicação).
CORRELACOES_TAMANHO = [
    ("lev_pos", "Correlação: tamanho do texto × Lev. Pos.",
     "Perto de 1: a distância acompanha o tamanho do texto."),
    ("lev_neg", "Correlação: tamanho do texto × Lev. Neg.", "Idem."),
    ("jaccard_pos", "Correlação: tamanho do texto × Jaccard Pos.",
     "Perto de 0: o tamanho quase não influencia a métrica."),
    ("jaccard_neg", "Correlação: tamanho do texto × Jaccard Neg.", "Idem."),
]

# Formato de exibição da coluna Valor, por indicador. Os que não aparecem aqui
# usam o padrão: inteiros sem formato especial e decimais com 0.0000.
# O formato muda só a EXIBIÇÃO: a célula guarda o valor completo.
FORMATOS_INDICADORES = {
    IND_PARCELA_POS: FORMATO_PERCENTUAL,
    IND_PARCELA_NEG: FORMATO_PERCENTUAL,
    IND_MARGEM_REL_JACCARD: FORMATO_PERCENTUAL,
    IND_MARGEM_REL_LEV: FORMATO_PERCENTUAL,
    IND_MARGEM_ABS_LEV: FORMATO_INTEIRO,  # é uma contagem de caracteres
    **{nome: FORMATO_CORRELACAO for _, nome, _ in CORRELACOES_TAMANHO},
}


# ---------------------------------------------------------------------------
# Perguntas 1 a 6
# ---------------------------------------------------------------------------

def _contar(coluna: pd.Series, rotulo: str) -> int:
    """Conta quantas vezes um rótulo aparece numa coluna (0 se não aparecer).

    value_counts() devolve a contagem de cada valor distinto; .get(rotulo, 0)
    evita erro caso nenhuma avaliação tenha recebido aquele rótulo.
    """
    return int(coluna.value_counts().get(rotulo, 0))


def responder_perguntas_1_a_6(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula as respostas numéricas das perguntas 1 a 6 (enunciado, seção 9).

    Recebe o DataFrame classificado e devolve uma tabela com as colunas
    Pergunta, Descrição e Resultado, uma linha por pergunta.
    """
    # Comparar duas colunas dá uma coluna de True/False; somar booleanos
    # conta os True (o Python trata True como 1 e False como 0).
    concordam = int((df["class_jaccard"] == df["class_lev"]).sum())
    total = len(df)

    linhas = [
        (1, "Avaliações POSITIVAS pelo Jaccard", _contar(df["class_jaccard"], POSITIVA)),
        (2, "Avaliações NEGATIVAS pelo Jaccard", _contar(df["class_jaccard"], NEGATIVA)),
        (3, "Avaliações POSITIVAS pela Levenshtein", _contar(df["class_lev"], POSITIVA)),
        (4, "Avaliações NEGATIVAS pela Levenshtein", _contar(df["class_lev"], NEGATIVA)),
        (5, "Avaliações com a MESMA classificação nas duas métricas", concordam),
        (6, "Avaliações com classificações DIFERENTES", total - concordam),
    ]
    return pd.DataFrame(linhas, columns=["Pergunta", "Descrição", "Resultado"])


def tabela_cruzada(df: pd.DataFrame) -> pd.DataFrame:
    """Cruza a classificação do Jaccard (linhas) com a da Levenshtein (colunas).

    Recebe o DataFrame classificado e devolve a tabela de contagens com uma
    linha e uma coluna "Total" (margins=True). A diagonal (POSITIVA/POSITIVA e
    NEGATIVA/NEGATIVA) são as concordâncias (pergunta 5); fora dela, as
    divergências (pergunta 6).
    """
    return pd.crosstab(
        df["class_jaccard"].rename("Class. Jaccard"),
        df["class_lev"].rename("Class. Lev."),
        margins=True,
        margins_name="Total",
    )


def listar_divergencias(df: pd.DataFrame) -> pd.DataFrame:
    """Lista as avaliações em que as duas métricas discordam.

    Recebe o DataFrame classificado e devolve as linhas com
    class_jaccard != class_lev, nas 8 colunas da tabela final (SPEC 04),
    ordenadas por ID.
    """
    divergentes = df[df["class_jaccard"] != df["class_lev"]]
    tabela = montar_tabela_resultados(divergentes)
    return tabela.sort_values("ID").reset_index(drop=True)


# ---------------------------------------------------------------------------
# Evidências para as perguntas 7 e 8
# ---------------------------------------------------------------------------

def _dividir(numerador: float, denominador: float) -> float:
    """Divisão que devolve 0 quando o denominador é 0 (evita divisão por zero)."""
    return numerador / denominador if denominador else 0.0


def calcular_evidencias(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula indicadores por avaliação para sustentar as perguntas 7 e 8.

    Recebe o DataFrame classificado e devolve uma NOVA tabela, uma linha por
    avaliação (ordenada por ID), com tamanhos, parcela da distância explicada
    pelo tamanho, palavras em comum, margens, empates e concordância.
    """
    tamanho = df["texto_limpo"].str.len()
    dif_pos = (tamanho - len(POSITIVA_LIMPA)).abs()
    dif_neg = (tamanho - len(NEGATIVA_LIMPA)).abs()

    margem_jaccard = df["jaccard_pos"] - df["jaccard_neg"]
    # lev_neg − lev_pos: positiva quando a avaliação está MAIS PERTO da
    # referência positiva — mesma convenção da margem do Jaccard.
    margem_lev = df["lev_neg"] - df["lev_pos"]

    maior_jaccard = df[["jaccard_pos", "jaccard_neg"]].max(axis=1)
    maior_lev = df[["lev_pos", "lev_neg"]].max(axis=1)

    evidencias = pd.DataFrame({
        "ID": df["ID"],
        "Tam. texto limpo": tamanho,
        "Dif. tam. Pos.": dif_pos,
        "Dif. tam. Neg.": dif_neg,
        # combine aplica a função elemento a elemento em duas colunas.
        "Parcela tam. Lev. Pos.": dif_pos.combine(df["lev_pos"], _dividir),
        "Parcela tam. Lev. Neg.": dif_neg.combine(df["lev_neg"], _dividir),
        "Palavras em comum Pos.": df["tokens"].apply(lambda t: len(set(t) & POSITIVA_PALAVRAS)),
        "Palavras em comum Neg.": df["tokens"].apply(lambda t: len(set(t) & NEGATIVA_PALAVRAS)),
        "Margem Jaccard": margem_jaccard,
        "Margem Lev.": margem_lev,
        "Margem rel. Jaccard": margem_jaccard.abs().combine(maior_jaccard, _dividir),
        "Margem rel. Lev.": margem_lev.abs().combine(maior_lev, _dividir),
        "Empate Jaccard": df["jaccard_pos"] == df["jaccard_neg"],
        "Empate Lev.": df["lev_pos"] == df["lev_neg"],
        "Métricas concordam": df["class_jaccard"] == df["class_lev"],
    })
    return evidencias.sort_values("ID").reset_index(drop=True)


def _pares_duplicados_consistentes(df: pd.DataFrame) -> tuple[int, int]:
    """Conta os grupos de avaliações com texto idêntico e quantos são consistentes.

    Devolve (total de grupos, grupos em que todas as cópias receberam as
    mesmas classificações nas duas métricas). Textos iguais têm métricas
    iguais, então deveriam ter classificações iguais: é uma conferência.
    """
    grupos = df.groupby("avaliacao").filter(lambda g: len(g) > 1).groupby("avaliacao")
    total = grupos.ngroups
    consistentes = sum(
        1 for _, g in grupos
        if g["class_jaccard"].nunique() == 1 and g["class_lev"].nunique() == 1
    )
    return total, consistentes


def calcular_indicadores(df: pd.DataFrame, evidencias: pd.DataFrame) -> pd.DataFrame:
    """Resume as evidências em indicadores gerais.

    Recebe o DataFrame classificado e a tabela de calcular_evidencias(), e
    devolve uma tabela com as colunas Indicador, Valor e Explicação.
    O formato de exibição de cada indicador no Excel está em FORMATOS_INDICADORES.
    """
    tamanho = evidencias["Tam. texto limpo"]
    total_pares, pares_ok = _pares_duplicados_consistentes(df)

    # Correlação de Pearson entre o tamanho do texto limpo e cada métrica.
    # Series.corr emparelha os valores pelo índice; usando o ID como índice nas
    # duas tabelas, cada tamanho é comparado com a métrica da MESMA avaliação,
    # qualquer que seja a ordem das linhas.
    tamanho_por_id = evidencias.set_index("ID")["Tam. texto limpo"]
    metricas_por_id = df.set_index("ID")
    correlacoes = [
        (nome, float(tamanho_por_id.corr(metricas_por_id[coluna])), explicacao)
        for coluna, nome, explicacao in CORRELACOES_TAMANHO
    ]

    linhas = [
        ("Tamanho da referência positiva limpa (caracteres)", len(POSITIVA_LIMPA),
         "Base de comparação da Levenshtein."),
        ("Tamanho da referência negativa limpa (caracteres)", len(NEGATIVA_LIMPA),
         "Base de comparação da Levenshtein."),
        ("Tamanho mínimo das avaliações limpas (caracteres)", int(tamanho.min()),
         "Contraste com o tamanho das referências."),
        ("Tamanho médio das avaliações limpas (caracteres)", float(tamanho.mean()),
         "Contraste com o tamanho das referências."),
        ("Tamanho máximo das avaliações limpas (caracteres)", int(tamanho.max()),
         "Contraste com o tamanho das referências."),
        (IND_PARCELA_POS, float(evidencias["Parcela tam. Lev. Pos."].mean()),
         "Quanto da distância à referência positiva vem só da diferença de tamanho."),
        (IND_PARCELA_NEG, float(evidencias["Parcela tam. Lev. Neg."].mean()),
         "Quanto da distância à referência negativa vem só da diferença de tamanho."),
        *correlacoes,  # o * "desempacota" a lista: cada correlação vira uma linha
        ("Empates no Jaccard", int(evidencias["Empate Jaccard"].sum()),
         "Todos classificados como NEGATIVA (enunciado, seção 6)."),
        ("Empates na Levenshtein", int(evidencias["Empate Lev."].sum()),
         "Todos classificados como NEGATIVA (enunciado, seção 6)."),
        ("Valores distintos em Jaccard Pos.", int(df["jaccard_pos"].nunique()),
         "Quantos resultados diferentes a métrica produziu nas avaliações."),
        ("Valores distintos em Jaccard Neg.", int(df["jaccard_neg"].nunique()),
         "Quantos resultados diferentes a métrica produziu nas avaliações."),
        ("Valores distintos em Lev. Pos.", int(df["lev_pos"].nunique()),
         "Quantos resultados diferentes a métrica produziu nas avaliações."),
        ("Valores distintos em Lev. Neg.", int(df["lev_neg"].nunique()),
         "Quantos resultados diferentes a métrica produziu nas avaliações."),
        (IND_MARGEM_REL_JACCARD, float(evidencias["Margem rel. Jaccard"].median()),
         "Folga típica das decisões do Jaccard."),
        (IND_MARGEM_REL_LEV, float(evidencias["Margem rel. Lev."].median()),
         "Folga típica das decisões da Levenshtein."),
        (IND_MARGEM_ABS_LEV, float(evidencias["Margem Lev."].abs().median()),
         "Quantos caracteres decidem uma classificação típica da Levenshtein."),
        ("Pares de avaliações duplicadas com classificações idênticas", pares_ok,
         f"Conferência de consistência: {pares_ok} de {total_pares} pares de textos "
         "idênticos (SPEC 01) receberam as mesmas classificações."),
    ]
    # dtype=object: a coluna Valor mistura inteiros e decimais. Sem isso, o
    # pandas converteria tudo para decimal (170 viraria 170.0).
    return pd.DataFrame(linhas, columns=["Indicador", "Valor", "Explicação"], dtype=object)


# ---------------------------------------------------------------------------
# Gravação no Excel
# ---------------------------------------------------------------------------

def exportar_analise(caminho: Path, df: pd.DataFrame) -> list[str]:
    """Grava as abas de análise no Excel já gerado pela SPEC 04.

    Recebe o caminho do .xlsx (que já tem a aba Resultados) e o DataFrame
    classificado. Devolve os nomes das abas acrescentadas, na ordem:
    Resumo, Divergências, Evidências e Indicadores.

    A aba Resumo recebe dois blocos: as perguntas 1 a 6 e, depois de duas
    linhas em branco, a tabela cruzada com um título acima.
    """
    perguntas = responder_perguntas_1_a_6(df)
    evidencias = calcular_evidencias(df)
    abas = {
        "Resumo": perguntas,
        "Divergências": listar_divergencias(df),
        "Evidências": evidencias,
        "Indicadores": calcular_indicadores(df, evidencias),
    }
    adicionar_abas(caminho, abas, formatos_indicadores=FORMATOS_INDICADORES)

    # Linha do título = cabeçalho (1) + perguntas (6) + linhas em branco (2) + 1 → linha 10.
    linha_titulo = 1 + len(perguntas) + LINHAS_EM_BRANCO_RESUMO + 1
    cruzada = tabela_cruzada(df).rename_axis(index=ROTULO_CANTO_CRUZAMENTO)
    adicionar_bloco(caminho, "Resumo", cruzada, linha_titulo, TITULO_CRUZAMENTO)
    return list(abas)
