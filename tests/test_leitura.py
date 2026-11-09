"""Testes da SPEC 01: leitura e validação do Excel de avaliações."""

from pathlib import Path

import pandas as pd
import pytest

from leitura import carregar_avaliacoes

# Pares de IDs cujos textos são idênticos no arquivo real (verificado na SPEC 01).
PARES_DUPLICADOS = [(12, 97), (16, 32), (22, 55), (33, 77), (57, 63)]


@pytest.fixture(scope="module")
def avaliacoes() -> pd.DataFrame:
    """Carrega o arquivo real uma única vez e reaproveita em vários testes."""
    return carregar_avaliacoes()


def test_carrega_100_linhas(avaliacoes):
    assert len(avaliacoes) == 100


def test_colunas_exatas(avaliacoes):
    assert list(avaliacoes.columns) == ["ID", "avaliacao"]


def test_ids_unicos_de_1_a_100(avaliacoes):
    assert avaliacoes["ID"].is_unique
    assert sorted(avaliacoes["ID"]) == list(range(1, 101))


def test_nenhuma_avaliacao_vazia(avaliacoes):
    assert avaliacoes["avaliacao"].notna().all()
    assert (avaliacoes["avaliacao"].str.strip() != "").all()


def test_texto_nao_foi_alterado(avaliacoes):
    texto_id_1 = avaliacoes.loc[avaliacoes["ID"] == 1, "avaliacao"].iloc[0]
    assert texto_id_1.startswith("Na minha experiência, Excelente aquisição.")


def test_duplicados_continuam_presentes(avaliacoes):
    textos = avaliacoes.set_index("ID")["avaliacao"]
    for id_a, id_b in PARES_DUPLICADOS:
        assert textos[id_a] == textos[id_b], f"IDs {id_a} e {id_b} deveriam ser iguais"
    # 10 linhas envolvidas em textos repetidos, nenhuma removida.
    assert avaliacoes["avaliacao"].duplicated(keep=False).sum() == 10


def test_caminho_inexistente_gera_file_not_found(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="não encontrado"):
        carregar_avaliacoes(tmp_path / "nao_existe.xlsx")


def test_planilha_sem_coluna_avaliacao_gera_value_error(tmp_path: Path):
    # Cria uma planilha temporária só com a coluna ID.
    caminho = tmp_path / "sem_avaliacao.xlsx"
    pd.DataFrame({"ID": [1, 2, 3]}).to_excel(caminho, index=False)

    with pytest.raises(ValueError, match="avaliacao"):
        carregar_avaliacoes(caminho)
