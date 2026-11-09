"""Testes da SPEC 04: classificação das avaliações."""

import pandas as pd
import pytest

from classificacao import classificar_avaliacoes, classificar_jaccard, classificar_levenshtein
from leitura import carregar_avaliacoes
from metricas import calcular_metricas
from preprocessamento import preprocessar_avaliacoes


@pytest.mark.parametrize(
    "pos, neg, esperado",
    [
        (0.5, 0.3, "POSITIVA"),
        (0.3, 0.3, "NEGATIVA"),  # empate → NEGATIVA (enunciado, seção 6)
        (0.2, 0.3, "NEGATIVA"),
    ],
)
def test_classificar_jaccard(pos, neg, esperado):
    assert classificar_jaccard(pos, neg) == esperado


@pytest.mark.parametrize(
    "pos, neg, esperado",
    [
        (100, 120, "POSITIVA"),
        (120, 120, "NEGATIVA"),  # empate → NEGATIVA (enunciado, seção 6)
        (130, 120, "NEGATIVA"),
    ],
)
def test_classificar_levenshtein(pos, neg, esperado):
    assert classificar_levenshtein(pos, neg) == esperado


# ---------- arquivo real ----------

@pytest.fixture(scope="module")
def com_metricas() -> pd.DataFrame:
    return calcular_metricas(preprocessar_avaliacoes(carregar_avaliacoes()))


@pytest.fixture(scope="module")
def classificadas(com_metricas) -> pd.DataFrame:
    return classificar_avaliacoes(com_metricas)


def _linha(df: pd.DataFrame, id_: int) -> pd.Series:
    return df.loc[df["ID"] == id_].iloc[0]


@pytest.mark.parametrize(
    "id_, class_jaccard, class_lev",
    [
        (1, "POSITIVA", "POSITIVA"),  # caso comum
        (3, "NEGATIVA", "NEGATIVA"),  # caso comum
        (4, "NEGATIVA", "NEGATIVA"),  # empate exato no Jaccard (8/53 × 8/53)
    ],
)
def test_classificacoes_conferidas(classificadas, id_, class_jaccard, class_lev):
    linha = _linha(classificadas, id_)
    assert linha["class_jaccard"] == class_jaccard
    assert linha["class_lev"] == class_lev


def test_empate_jaccard_id_4(classificadas):
    linha = _linha(classificadas, 4)
    # Confere que o empate é EXATO (sem arredondar) e que virou NEGATIVA.
    assert linha["jaccard_pos"] == linha["jaccard_neg"] == pytest.approx(8 / 53)
    assert linha["class_jaccard"] == "NEGATIVA"


def test_empate_levenshtein_id_8(classificadas):
    linha = _linha(classificadas, 8)
    assert linha["lev_pos"] == linha["lev_neg"] == 192
    assert linha["class_lev"] == "NEGATIVA"


def test_somente_rotulos_validos(classificadas):
    for coluna in ["class_jaccard", "class_lev"]:
        assert set(classificadas[coluna]) <= {"POSITIVA", "NEGATIVA"}


def test_entrada_nao_modificada(com_metricas, classificadas):
    assert "class_jaccard" not in com_metricas.columns
    assert "class_lev" not in com_metricas.columns
