"""Testes da SPEC 02: pré-processamento dos textos."""

import re

import pandas as pd
import pytest

from leitura import carregar_avaliacoes
from preprocessamento import limpar_texto, preprocessar_avaliacoes, tokenizar
from referencias import REFERENCIA_NEGATIVA, REFERENCIA_POSITIVA

POSITIVA_LIMPA_ESPERADA = (
    "o produto possui excelente qualidade chegou rapidamente e atendeu "
    "completamente às minhas expectativas gostei muito da compra e recomendo "
    "este produto para outras pessoas"
)
NEGATIVA_LIMPA_ESPERADA = (
    "o produto possui péssima qualidade apresentou problemas logo após a "
    "compra e não atendeu às minhas expectativas fiquei muito decepcionado e "
    "não recomendo este produto"
)


# ---------- limpar_texto ----------

@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("Bom,ótimo!!", "bom ótimo"),      # pontuação vira espaço, sem colar palavras
        ("  Muito   BOM.  ", "muito bom"),  # minúsculas + espaços normalizados
        ("Péssima", "péssima"),            # acento preservado
        ("bem-vindo", "bem vindo"),        # hífen é pontuação
        ("", ""),                          # texto vazio
    ],
)
def test_limpar_texto(entrada, esperado):
    assert limpar_texto(entrada) == esperado


@pytest.mark.parametrize("referencia", [REFERENCIA_POSITIVA, REFERENCIA_NEGATIVA])
def test_limpar_texto_idempotente(referencia):
    uma_vez = limpar_texto(referencia)
    assert limpar_texto(uma_vez) == uma_vez


# ---------- tokenizar ----------

@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("muito bom", ["muito", "bom"]),
        ("muito muito bom", ["muito", "muito", "bom"]),  # repetição preservada
        ("", []),
    ],
)
def test_tokenizar(entrada, esperado):
    assert tokenizar(entrada) == esperado


# ---------- referências ----------

def test_referencia_positiva_limpa():
    assert limpar_texto(REFERENCIA_POSITIVA) == POSITIVA_LIMPA_ESPERADA


def test_referencia_negativa_limpa():
    assert limpar_texto(REFERENCIA_NEGATIVA) == NEGATIVA_LIMPA_ESPERADA


def test_referencia_positiva_contagem_tokens():
    tokens = tokenizar(limpar_texto(REFERENCIA_POSITIVA))
    assert len(tokens) == 24
    assert len(set(tokens)) == 22


def test_referencia_negativa_contagem_tokens():
    tokens = tokenizar(limpar_texto(REFERENCIA_NEGATIVA))
    assert len(tokens) == 25
    assert len(set(tokens)) == 22


# ---------- preprocessar_avaliacoes (arquivo real) ----------

@pytest.fixture(scope="module")
def originais() -> pd.DataFrame:
    return carregar_avaliacoes()


@pytest.fixture(scope="module")
def processadas(originais) -> pd.DataFrame:
    return preprocessar_avaliacoes(originais)


def test_formato_do_resultado(processadas):
    assert len(processadas) == 100
    assert list(processadas.columns) == ["ID", "avaliacao", "texto_limpo", "tokens"]


def test_coluna_avaliacao_intacta(processadas):
    assert processadas["avaliacao"].equals(carregar_avaliacoes()["avaliacao"])


def test_entrada_nao_modificada(originais, processadas):
    assert list(originais.columns) == ["ID", "avaliacao"]


def test_texto_limpo_id_1(processadas):
    texto = processadas.loc[processadas["ID"] == 1, "texto_limpo"].iloc[0]
    assert texto.startswith("na minha experiência excelente aquisição o produto é leve")


def test_texto_limpo_sem_pontuacao_nem_espacos_extras(processadas):
    for texto in processadas["texto_limpo"]:
        assert re.search(r"[^\w\s]", texto) is None, texto  # nenhuma pontuação
        assert "  " not in texto, texto
        assert texto == texto.strip(), texto


def test_tokens_coerentes_com_texto_limpo(processadas):
    for texto, tokens in zip(processadas["texto_limpo"], processadas["tokens"]):
        assert tokens == texto.split()
