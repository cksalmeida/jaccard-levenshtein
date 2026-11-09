"""Ponto de entrada do programa: orquestra as etapas do classificador.


Fluxo: carregar → pré-processar → calcular métricas → classificar →
montar tabela → exportar
"""

import time

import pandas as pd

from analise import exportar_analise
from classificacao import classificar_avaliacoes
from leitura import carregar_avaliacoes
from metricas import calcular_metricas
from resultados import exportar_excel, montar_tabela_resultados
from preprocessamento import limpar_texto, preprocessar_avaliacoes, tokenizar
from referencias import REFERENCIA_NEGATIVA, REFERENCIA_POSITIVA

# Quantos caracteres de cada avaliação mostrar na prévia.
TAMANHO_PREVIA = 80

# Quantas avaliações mostrar na prévia.
QUANTIDADE_PREVIA = 3


def cortar_texto(texto: str, limite: int = TAMANHO_PREVIA) -> str:
    """Encurta um texto para caber numa linha do terminal.

    Recebe o texto e o número máximo de caracteres. Devolve o texto original se
    ele já couber, ou os primeiros `limite` caracteres seguidos de "...".
    """
    if len(texto) <= limite:
        return texto
    return texto[:limite].rstrip() + "..."


def imprimir_resumo(df: pd.DataFrame) -> None:
    """Imprime no terminal um resumo do DataFrame de avaliações.

    Recebe o DataFrame devolvido por carregar_avaliacoes() e não devolve nada.
    Mostra: quantidade de linhas, colunas e tipos, as primeiras avaliações e o
    tamanho mínimo/médio/máximo dos textos.
    """
    print("=== Resumo da leitura ===")
    print(f"Avaliações carregadas: {len(df)}")

    print("\nColunas:")
    for coluna, tipo in df.dtypes.items():
        print(f"  - {coluna}: {tipo}")

    print(f"\nPrimeiras {QUANTIDADE_PREVIA} avaliações:")
    for linha in df.head(QUANTIDADE_PREVIA).itertuples(index=False):
        print(f"  [{linha.ID}] {cortar_texto(linha.avaliacao)}")

    tamanhos = df["avaliacao"].str.len()
    print("\nTamanho dos textos (caracteres):")
    print(f"  mínimo: {tamanhos.min()}")
    print(f"  médio:  {tamanhos.mean():.1f}")
    print(f"  máximo: {tamanhos.max()}")


def imprimir_referencia(nome: str, texto_original: str) -> None:
    """Imprime uma referência já limpa e as contagens de tokens.

    Recebe o nome da referência (ex.: "positiva") e o texto original do
    enunciado. Não devolve nada. Mostra o texto limpo, o total de tokens e
    quantos tokens distintos existem (len(set(...)) descarta as repetições).
    """
    texto_limpo = limpar_texto(texto_original)
    tokens = tokenizar(texto_limpo)
    print(f"\nReferência {nome} (limpa):")
    print(f"  {texto_limpo}")
    print(f"  tokens: {len(tokens)} | tokens distintos: {len(set(tokens))}")


def imprimir_resumo_preprocessamento(processadas: pd.DataFrame) -> None:
    """Imprime o resumo da etapa de pré-processamento.

    Recebe o DataFrame devolvido por preprocessar_avaliacoes() e não devolve
    nada. Mostra as referências limpas, um exemplo de antes e depois (ID 1) e
    quantas avaliações foram pré-processadas.
    """
    print("\n=== Resumo do pré-processamento ===")
    imprimir_referencia("positiva", REFERENCIA_POSITIVA)
    imprimir_referencia("negativa", REFERENCIA_NEGATIVA)

    exemplo = processadas.loc[processadas["ID"] == 1].iloc[0]
    print("\nExemplo (ID 1):")
    print(f"  antes:  {exemplo['avaliacao']}")
    print(f"  depois: {exemplo['texto_limpo']}")

    print(f"\nAvaliações pré-processadas: {len(processadas)}")


COLUNAS_METRICAS = ["jaccard_pos", "jaccard_neg", "lev_pos", "lev_neg"]


def imprimir_resumo_metricas(com_metricas: pd.DataFrame, segundos: float) -> None:
    """Imprime o resumo da etapa de métricas.

    Recebe o DataFrame devolvido por calcular_metricas() e o tempo gasto no
    cálculo, em segundos. Não devolve nada. Mostra o tempo, as métricas das 5
    primeiras avaliações e o mínimo/média/máximo de cada métrica.
    """
    print("\n=== Resumo das métricas ===")
    print(f"Tempo de cálculo: {segundos:.2f} s")

    # to_string(index=False) imprime a tabela sem a coluna de índice do pandas.
    print("\nPrimeiras 5 avaliações:")
    print(com_metricas[["ID", *COLUNAS_METRICAS]].head(5).to_string(index=False))

    # Jaccard é decimal (4 casas); Levenshtein é inteiro, só a média tem decimais.
    print("\nEstatísticas:        mínimo     média    máximo")
    for coluna in COLUNAS_METRICAS:
        valores = com_metricas[coluna]
        if coluna.startswith("jaccard"):
            minimo, maximo = f"{valores.min():.4f}", f"{valores.max():.4f}"
        else:
            minimo, maximo = f"{valores.min()}", f"{valores.max()}"
        print(f"  {coluna:<15} {minimo:>9} {valores.mean():>9.4f} {maximo:>9}")


def imprimir_previa_resultados(tabela: pd.DataFrame, linhas: int = 10) -> None:
    """Imprime as primeiras linhas da tabela de resultados (SPEC 04).

    Recebe a tabela de montar_tabela_resultados() e quantas linhas mostrar.
    Não devolve nada. Corta a avaliação em ~60 caracteres e arredonda o Jaccard
    para 4 casas APENAS nesta exibição: a tabela recebida não é alterada.
    """
    previa = tabela.head(linhas).copy()
    previa["Avaliação"] = previa["Avaliação"].apply(lambda texto: cortar_texto(texto, 60))
    previa[["Jaccard Pos.", "Jaccard Neg."]] = previa[["Jaccard Pos.", "Jaccard Neg."]].round(4)

    print(f"\n=== Resultados (primeiras {linhas} linhas) ===")
    print(previa.to_string(index=False))


def main() -> None:
    """Executa o fluxo completo e imprime os resumos de cada etapa."""
    avaliacoes = carregar_avaliacoes()
    imprimir_resumo(avaliacoes)

    processadas = preprocessar_avaliacoes(avaliacoes)
    imprimir_resumo_preprocessamento(processadas)

    # perf_counter é um cronômetro de alta precisão: medimos o instante antes
    # e depois, e a diferença é o tempo gasto.
    inicio = time.perf_counter()
    com_metricas = calcular_metricas(processadas)
    segundos = time.perf_counter() - inicio
    imprimir_resumo_metricas(com_metricas, segundos)

    classificadas = classificar_avaliacoes(com_metricas)
    tabela = montar_tabela_resultados(classificadas)
    imprimir_previa_resultados(tabela)

    caminho = exportar_excel(tabela)
    abas_novas = exportar_analise(caminho, classificadas)

    print(f"\nArquivo Excel gerado: {caminho}")
    print(f"Abas: Resultados, {', '.join(abas_novas)}")


if __name__ == "__main__":
    main()
