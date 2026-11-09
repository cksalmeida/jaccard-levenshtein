"""Testes da SPEC 04: tabela de resultados e exportação para Excel.

Toda exportação é feita em tmp_path, para não tocar na pasta resultados/ real.
"""

from pathlib import Path

import openpyxl
import pandas as pd
import pytest

from classificacao import classificar_avaliacoes
from leitura import carregar_avaliacoes
from metricas import calcular_metricas
from preprocessamento import preprocessar_avaliacoes
from resultados import exportar_excel, montar_tabela_resultados

COLUNAS_ESPERADAS = [
    "ID", "Avaliação", "Jaccard Pos.", "Jaccard Neg.",
    "Class. Jaccard", "Lev. Pos.", "Lev. Neg.", "Class. Lev.",
]


@pytest.fixture(scope="module")
def tabela() -> pd.DataFrame:
    df = carregar_avaliacoes()
    df = preprocessar_avaliacoes(df)
    df = calcular_metricas(df)
    df = classificar_avaliacoes(df)
    return montar_tabela_resultados(df)


@pytest.fixture
def arquivo_exportado(tabela, tmp_path: Path) -> Path:
    return exportar_excel(tabela, tmp_path / "resultados.xlsx")


def test_formato_da_tabela(tabela):
    assert len(tabela) == 100
    assert list(tabela.columns) == COLUNAS_ESPERADAS


def test_avaliacao_e_o_texto_original(tabela):
    assert tabela["Avaliação"].equals(carregar_avaliacoes()["avaliacao"])


def test_excel_relido_com_pandas(arquivo_exportado):
    relida = pd.read_excel(arquivo_exportado)
    assert len(relida) == 100
    assert list(relida.columns) == COLUNAS_ESPERADAS
    jaccard_pos_id_1 = relida.loc[relida["ID"] == 1, "Jaccard Pos."].iloc[0]
    # 0.148148 tem 6 casas: se o valor tivesse sido arredondado para 0.1481, falharia.
    assert jaccard_pos_id_1 == pytest.approx(0.148148, abs=1e-6)


def test_excel_formatacao_com_openpyxl(arquivo_exportado):
    livro = openpyxl.load_workbook(arquivo_exportado)
    assert livro.sheetnames == ["Resultados"]
    planilha = livro["Resultados"]

    assert all(celula.font.bold for celula in planilha[1])
    assert planilha.freeze_panes == "A2"

    # Colunas C e D são Jaccard Pos. e Jaccard Neg. (linhas 2 a 101 = 100 avaliações).
    for coluna in ["C", "D"]:
        for linha in range(2, 102):
            assert planilha[f"{coluna}{linha}"].number_format == "0.0000"


def test_exportar_cria_pasta(tabela, tmp_path: Path):
    destino = tmp_path / "pasta" / "nova" / "resultados.xlsx"
    assert not destino.parent.exists()
    devolvido = exportar_excel(tabela, destino)
    assert devolvido == destino
    assert destino.is_file()
