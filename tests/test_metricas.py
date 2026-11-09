"""Testes da SPEC 03: similaridade de Jaccard e distância de Levenshtein."""

import pandas as pd
import pytest
from rapidfuzz.distance import Levenshtein as LevenshteinGabarito

from leitura import carregar_avaliacoes
from metricas import calcular_metricas, distancia_levenshtein, similaridade_jaccard
from preprocessamento import limpar_texto, preprocessar_avaliacoes, tokenizar
from referencias import REFERENCIA_NEGATIVA, REFERENCIA_POSITIVA

POSITIVA_LIMPA = limpar_texto(REFERENCIA_POSITIVA)
NEGATIVA_LIMPA = limpar_texto(REFERENCIA_NEGATIVA)

# ---------- similaridade_jaccard ----------

CASOS_JACCARD = [
    ("o produto é muito bom", "o produto é muito ruim", 4 / 6),
    ("não gostei do produto", "gostei muito do produto", 3 / 5),
    ("entrega rápida e produto bom", "produto bom mas entrega lenta", 3 / 7),
    ("muito muito bom", "muito bom", 1.0),                            # repetição ignorada
    ("o cachorro mordeu o homem", "o homem mordeu o cachorro", 1.0),  # ordem ignorada
    ("gostei do produto", "entrega lenta", 0.0),
    ("", "", 1.0),                                                    # caso especial
    ("", "bom", 0.0),
]


@pytest.mark.parametrize("texto_a, texto_b, esperado", CASOS_JACCARD)
def test_jaccard_casos(texto_a, texto_b, esperado):
    assert similaridade_jaccard(tokenizar(texto_a), tokenizar(texto_b)) == pytest.approx(esperado)


@pytest.mark.parametrize("texto_a, texto_b, _esperado", CASOS_JACCARD)
def test_jaccard_simetria(texto_a, texto_b, _esperado):
    a, b = tokenizar(texto_a), tokenizar(texto_b)
    assert similaridade_jaccard(a, b) == similaridade_jaccard(b, a)


def test_jaccard_referencias():
    resultado = similaridade_jaccard(tokenizar(POSITIVA_LIMPA), tokenizar(NEGATIVA_LIMPA))
    assert resultado == pytest.approx(13 / 31)


# ---------- distancia_levenshtein ----------

CASOS_LEVENSHTEIN = [
    ("bom", "boa", 1),
    ("mar", "amor", 2),
    ("livro", "libra", 2),
    ("gato", "rato", 1),
    ("carro", "caro", 1),
    ("otimo", "ótimo", 1),
    ("pessimo", "péssima", 2),
    ("chegou rápido bem", "chegou rápidobem", 1),
    ("", "abc", 3),
    ("abc", "", 3),
    ("produto", "produto", 0),
]


@pytest.mark.parametrize("texto_a, texto_b, esperado", CASOS_LEVENSHTEIN)
def test_levenshtein_casos(texto_a, texto_b, esperado):
    assert distancia_levenshtein(texto_a, texto_b) == esperado


@pytest.mark.parametrize("texto_a, texto_b, _esperado", CASOS_LEVENSHTEIN)
def test_levenshtein_simetria(texto_a, texto_b, _esperado):
    assert distancia_levenshtein(texto_a, texto_b) == distancia_levenshtein(texto_b, texto_a)


def test_levenshtein_referencias():
    assert distancia_levenshtein(POSITIVA_LIMPA, NEGATIVA_LIMPA) == 83


# ---------- calcular_metricas (arquivo real) ----------

@pytest.fixture(scope="module")
def processadas() -> pd.DataFrame:
    return preprocessar_avaliacoes(carregar_avaliacoes())


@pytest.fixture(scope="module")
def com_metricas(processadas) -> pd.DataFrame:
    return calcular_metricas(processadas)


def test_levenshtein_igual_ao_rapidfuzz(com_metricas):
    """Gabarito: 100 avaliações x 2 referências = 200 comparações."""
    for linha in com_metricas.itertuples(index=False):
        assert linha.lev_pos == LevenshteinGabarito.distance(linha.texto_limpo, POSITIVA_LIMPA), linha.ID
        assert linha.lev_neg == LevenshteinGabarito.distance(linha.texto_limpo, NEGATIVA_LIMPA), linha.ID


def test_formato_do_resultado(processadas, com_metricas):
    assert len(com_metricas) == 100
    assert list(com_metricas.columns) == list(processadas.columns) + [
        "jaccard_pos", "jaccard_neg", "lev_pos", "lev_neg",
    ]
    # As colunas anteriores continuam com os mesmos valores.
    for coluna in processadas.columns:
        assert com_metricas[coluna].equals(processadas[coluna])


def test_entrada_nao_modificada(processadas, com_metricas):
    # Pedir com_metricas garante que calcular_metricas já rodou sobre processadas.
    assert list(processadas.columns) == ["ID", "avaliacao", "texto_limpo", "tokens"]


def test_faixas_de_valores(com_metricas):
    for coluna in ["jaccard_pos", "jaccard_neg"]:
        assert com_metricas[coluna].between(0, 1).all()
    for coluna in ["lev_pos", "lev_neg"]:
        assert pd.api.types.is_integer_dtype(com_metricas[coluna])
        assert (com_metricas[coluna] >= 0).all()


def test_limite_inferior_levenshtein(com_metricas):
    tamanhos = com_metricas["texto_limpo"].str.len()
    assert (com_metricas["lev_pos"] >= (tamanhos - len(POSITIVA_LIMPA)).abs()).all()
    assert (com_metricas["lev_neg"] >= (tamanhos - len(NEGATIVA_LIMPA)).abs()).all()


@pytest.mark.parametrize(
    "id_, jaccard_pos, jaccard_neg, lev_pos, lev_neg",
    [
        (1, 0.1481, 0.1273, 192, 199),
        (3, 0.1017, 0.2037, 222, 215),
    ],
)
def test_valores_conferidos(com_metricas, id_, jaccard_pos, jaccard_neg, lev_pos, lev_neg):
    linha = com_metricas.loc[com_metricas["ID"] == id_].iloc[0]
    # abs=1e-4: os valores esperados foram escritos com 4 casas decimais.
    assert linha["jaccard_pos"] == pytest.approx(jaccard_pos, abs=1e-4)
    assert linha["jaccard_neg"] == pytest.approx(jaccard_neg, abs=1e-4)
    assert linha["lev_pos"] == lev_pos
    assert linha["lev_neg"] == lev_neg
