"""Leitura e validação do arquivo de avaliações.

Este módulo é a primeira etapa do fluxo do programa:
leitura → pré-processamento → métricas → classificação → resultados

Ele só lê e confere o Excel. Os textos são devolvidos exatamente como estão no
arquivo: qualquer limpeza (minúsculas, pontuação etc.) é papel do módulo de pré-processamento
"""

from pathlib import Path

import pandas as pd

# Pasta onde está este arquivo (leitura.py), ou seja, a raiz do projeto.
# Usamos __file__ (o caminho deste módulo) em vez da "pasta atual" do terminal
# para que o programa encontre o Excel não importa de onde ele seja executado.
RAIZ_PROJETO = Path(__file__).resolve().parent

# Caminho padrão do arquivo de entrada fornecido pelo enunciado (seção 2).
CAMINHO_PADRAO = RAIZ_PROJETO / "dados" / "avaliacoes.xlsx"

# Colunas que o arquivo precisa ter, na ordem em que serão devolvidas.
COLUNAS_ESPERADAS = ["ID", "avaliacao"]


def _verificar_arquivo_existe(caminho: Path) -> None:
    """Confere se o arquivo existe antes de tentar lê-lo.

    Recebe o caminho do Excel e não devolve nada. Lança FileNotFoundError com
    uma mensagem em português mostrando o caminho esperado, que é mais útil para
    quem vai corrigir o problema do que o erro genérico do pandas.
    """
    if not caminho.is_file():
        raise FileNotFoundError(
            f"Arquivo de avaliações não encontrado. Caminho esperado: {caminho}"
        )


def _verificar_colunas(df: pd.DataFrame) -> None:
    """Confere se as colunas obrigatórias (ID e avaliacao) estão presentes.

    Recebe o DataFrame lido e não devolve nada. Lança ValueError dizendo quais
    colunas faltam e quais foram encontradas, para facilitar a correção (por
    exemplo, quando alguém renomeia uma coluna no Excel).
    """
    faltando = [coluna for coluna in COLUNAS_ESPERADAS if coluna not in df.columns]
    if faltando:
        raise ValueError(
            f"Coluna(s) obrigatória(s) ausente(s): {faltando}. "
            f"Colunas encontradas no arquivo: {list(df.columns)}. "
            f"Esperado: {COLUNAS_ESPERADAS}."
        )


def _verificar_avaliacoes_vazias(df: pd.DataFrame) -> None:
    """Confere se nenhuma avaliação está vazia (nula ou só com espaços).

    Recebe o DataFrame e não devolve nada. Lança ValueError com os IDs das
    linhas problemáticas. Uma avaliação vazia não pode ser comparada com as
    referências, então é melhor parar aqui do que gerar um resultado sem sentido.

    Observação: o strip() abaixo é usado só para *testar* se o texto está vazio;
    o texto guardado no DataFrame não é alterado.
    """
    nulas = df["avaliacao"].isna()
    so_espacos = df["avaliacao"].astype(str).str.strip() == ""
    vazias = nulas | so_espacos
    if vazias.any():
        ids = df.loc[vazias, "ID"].tolist()
        raise ValueError(
            f"Há avaliação(ões) vazia(s) nos IDs: {ids}. "
            "Toda linha precisa ter um texto de avaliação."
        )


def _verificar_ids_unicos(df: pd.DataFrame) -> None:
    """Confere se não há IDs repetidos.

    Recebe o DataFrame e não devolve nada. Lança ValueError com os IDs
    repetidos. O ID identifica cada avaliação nos resultados; se ele se
    repetisse, não daria para saber a qual linha cada classificação pertence.
    """
    repetidos = df["ID"].duplicated(keep=False)  # keep=False marca todas as ocorrências
    if repetidos.any():
        ids = sorted(set(df.loc[repetidos, "ID"].tolist()))
        raise ValueError(
            f"Há ID(s) repetido(s): {ids}. Cada avaliação precisa de um ID único."
        )


def carregar_avaliacoes(caminho: Path = CAMINHO_PADRAO) -> pd.DataFrame:
    """Lê o Excel de avaliações e devolve um DataFrame validado.

    Recebe o caminho do arquivo .xlsx (por padrão, dados/avaliacoes.xlsx).
    Devolve um DataFrame com exatamente as colunas ID e avaliacao, na ordem do
    arquivo e com os textos sem nenhuma alteração.

    Lança:
        FileNotFoundError: se o arquivo não existir.
        ValueError: se faltar coluna, houver avaliação vazia ou ID repetido.

    Avaliações com texto duplicado NÃO são removidas: o enunciado (seções 2 e
    5.1) trata as 100 avaliações como o conjunto a classificar.
    """
    caminho = Path(caminho)
    _verificar_arquivo_existe(caminho)

    # sheet_name=0 → primeira aba. O pandas usa o openpyxl por baixo para abrir
    # o .xlsx (enunciado, seção 5.1: leitura do Excel com pandas).
    df = pd.read_excel(caminho, sheet_name=0)

    _verificar_colunas(df)
    _verificar_avaliacoes_vazias(df)
    _verificar_ids_unicos(df)

    # Mantém só as colunas esperadas, na ordem definida. .copy() cria um
    # DataFrame independente, evitando avisos do pandas em alterações futuras.
    return df[COLUNAS_ESPERADAS].copy()
