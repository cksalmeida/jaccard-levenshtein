"""Pré-processamento dos textos.

Segunda etapa do fluxo:
leitura → pré-processamento → métricas → classificação → resultados

Atende ao enunciado, seção 5.2: minúsculas, remoção de pontuação, remoção de
espaços desnecessários e tokenização. Cada texto ganha duas representações:

- texto_limpo (string): usado pela distância de Levenshtein (seção 5.4), que
  compara sequências de caracteres;
- tokens (lista de palavras): usados pela similaridade de Jaccard (seção 5.3),
  que compara conjuntos de palavras. 
"""

import re

import pandas as pd

# Expressões regulares compiladas uma vez só (são reaproveitadas em cada texto).
# [^\w\s] → qualquer caractere que NÃO seja letra/número/_ nem espaço em branco,
#           ou seja, a pontuação. Em Python 3, \w reconhece letras acentuadas.
PADRAO_PONTUACAO = re.compile(r"[^\w\s]")

# \s+ → uma ou mais ocorrências seguidas de espaço em branco (espaço, tab, quebra
#       de linha). Usado para reduzir qualquer sequência a um único espaço.
PADRAO_ESPACOS = re.compile(r"\s+")


def limpar_texto(texto: str) -> str:
    """Padroniza um texto para comparação.

    Recebe o texto original e devolve uma nova string com:
    1. todas as letras em minúsculas;
    2. a pontuação trocada por espaço (trocar, e não apagar, evita colar
       palavras: "bom,ótimo" vira "bom ótimo", e não "bomótimo");
    3. sequências de espaços reduzidas a um único espaço, sem espaços no
       início nem no fim.

    Acentos, stopwords e a forma das palavras são mantidos.
    """
    texto = texto.lower()
    texto = PADRAO_PONTUACAO.sub(" ", texto)
    texto = PADRAO_ESPACOS.sub(" ", texto)
    return texto.strip()


def tokenizar(texto_limpo: str) -> list[str]:
    """Divide um texto já limpo em palavras (tokens).

    Recebe a saída de limpar_texto() e devolve a lista de palavras, na ordem
    em que aparecem e com as repetições. Como a pontuação já foi removida,
    separar pelos espaços basta. Texto vazio devolve lista vazia.
    """
    return texto_limpo.split()


def preprocessar_avaliacoes(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica o pré-processamento a todas as avaliações.

    Recebe o DataFrame de carregar_avaliacoes() (colunas ID e avaliacao) e
    devolve uma CÓPIA com duas colunas novas: texto_limpo e tokens.

    O DataFrame recebido não é modificado, e a coluna avaliacao continua com o
    texto original, que aparece na tabela final (enunciado, seção 7).
    """
    resultado = df.copy()
    resultado["texto_limpo"] = resultado["avaliacao"].apply(limpar_texto)
    resultado["tokens"] = resultado["texto_limpo"].apply(tokenizar)
    return resultado
