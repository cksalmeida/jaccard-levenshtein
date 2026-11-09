"""Métricas de comparação de textos.

Terceira etapa do fluxo:
leitura → pré-processamento → métricas → classificação → resultados

As duas métricas são implementadas do zero, em Python puro:
- similaridade de Jaccard (enunciado, seção 5.3): compara CONJUNTOS de
  palavras; quanto MAIOR (0 a 1), mais parecidos são os textos;
- distância de Levenshtein (enunciado, seção 5.4): conta edições de
  CARACTERES; quanto MENOR, mais parecidos são os textos.

Nenhuma biblioteca de distância de texto é usada aqui. O rapidfuzz aparece
apenas nos testes, como gabarito para conferir a nossa Levenshtein.
"""

import pandas as pd

from preprocessamento import limpar_texto, tokenizar
from referencias import REFERENCIA_NEGATIVA, REFERENCIA_POSITIVA


def similaridade_jaccard(tokens_a: list[str], tokens_b: list[str]) -> float:
    """Calcula a similaridade de Jaccard entre duas listas de palavras.

    Recebe duas listas de tokens (saída de tokenizar()) e devolve um número de
    0.0 (nenhuma palavra em comum) a 1.0 (mesmo conjunto de palavras), pela
    fórmula J(A,B) = |A ∩ B| / |A ∪ B| (enunciado, seção 5.3).

    A e B são os CONJUNTOS de palavras: a conversão para set acontece aqui,
    e é só neste ponto que a ordem e as repetições deixam de importar.
    """
    conjunto_a = set(tokens_a)
    conjunto_b = set(tokens_b)

    intersecao = conjunto_a & conjunto_b  # palavras presentes nos dois textos
    uniao = conjunto_a | conjunto_b       # todas as palavras dos dois textos

    # Caso especial: dois textos vazios são idênticos. Também evita a divisão
    # por zero (len(uniao) == 0). Não ocorre nos dados reais.
    if not uniao:
        return 1.0

    return len(intersecao) / len(uniao)


def distancia_levenshtein(texto_a: str, texto_b: str) -> int:
    """Calcula a distância de Levenshtein entre dois textos.

    Recebe dois textos e devolve o MENOR número de
    inserções, remoções e substituições de caracteres necessárias para
    transformar texto_a em texto_b (enunciado, seção 5.4).

    Usa a tabela completa da programação dinâmica, igual ao cálculo à mão:
    a célula tabela[i][j] guarda a distância entre os i primeiros caracteres
    de texto_a e os j primeiros caracteres de texto_b.
    """
    linhas = len(texto_a) + 1
    colunas = len(texto_b) + 1

    # 1. Tabela de (linhas x colunas) preenchida com zeros.
    tabela = [[0] * colunas for _ in range(linhas)]

    # 2. Bordas.
    # Primeira coluna: transformar os i primeiros caracteres de texto_a em
    # texto vazio exige apagar os i caracteres → 0, 1, 2, ...
    for i in range(linhas):
        tabela[i][0] = i
    # Primeira linha: transformar texto vazio nos j primeiros caracteres de
    # texto_b exige inserir os j caracteres → 0, 1, 2, ...
    for j in range(colunas):
        tabela[0][j] = j

    # 3. Demais células: de cima para baixo, da esquerda para a direita.
    for i in range(1, linhas):
        for j in range(1, colunas):
            # A linha i corresponde ao caractere texto_a[i - 1] e a coluna j
            # ao caractere texto_b[j - 1] (a linha/coluna 0 é o texto vazio).
            custo = 0 if texto_a[i - 1] == texto_b[j - 1] else 1

            apagar = tabela[i - 1][j] + 1               # célula de cima + 1
            inserir = tabela[i][j - 1] + 1              # célula da esquerda + 1
            substituir = tabela[i - 1][j - 1] + custo   # diagonal + custo

            tabela[i][j] = min(apagar, inserir, substituir)

    # 4. A resposta está na última célula (canto inferior direito).
    return tabela[linhas - 1][colunas - 1]


def calcular_metricas(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula Jaccard e Levenshtein de cada avaliação contra as referências.

    Recebe o DataFrame de preprocessar_avaliacoes() (com as colunas tokens e
    texto_limpo) e devolve uma CÓPIA com todas as colunas anteriores mais:
    jaccard_pos, jaccard_neg, lev_pos e lev_neg.

    Os valores de Jaccard NÃO são arredondados: arredondar antes de classificar
    poderia criar empates falsos (ex.: 0,1481 e 0,1479 viram ambos 0,15). O
    arredondamento é só de apresentação.
    """
    # As referências passam pelo MESMO pré-processamento das avaliações.
    positiva_limpa = limpar_texto(REFERENCIA_POSITIVA)
    negativa_limpa = limpar_texto(REFERENCIA_NEGATIVA)
    positiva_tokens = tokenizar(positiva_limpa)
    negativa_tokens = tokenizar(negativa_limpa)

    resultado = df.copy()

    # lambda: função "de uma linha" que fixa a referência e recebe só o valor
    # de cada linha da coluna.
    resultado["jaccard_pos"] = resultado["tokens"].apply(
        lambda tokens: similaridade_jaccard(tokens, positiva_tokens)
    )
    resultado["jaccard_neg"] = resultado["tokens"].apply(
        lambda tokens: similaridade_jaccard(tokens, negativa_tokens)
    )
    resultado["lev_pos"] = resultado["texto_limpo"].apply(
        lambda texto: distancia_levenshtein(texto, positiva_limpa)
    )
    resultado["lev_neg"] = resultado["texto_limpo"].apply(
        lambda texto: distancia_levenshtein(texto, negativa_limpa)
    )
    return resultado
