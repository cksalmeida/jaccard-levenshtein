"""Testes da SPEC 05: análise dos resultados."""

from pathlib import Path

import openpyxl
import pandas as pd
import pytest

from analise import (
    calcular_evidencias,
    calcular_indicadores,
    exportar_analise,
    listar_divergencias,
    responder_perguntas_1_a_6,
    tabela_cruzada,
)
from classificacao import classificar_avaliacoes
from leitura import carregar_avaliacoes
from metricas import calcular_metricas
from preprocessamento import preprocessar_avaliacoes
from resultados import COLUNAS_TABELA, exportar_excel, montar_tabela_resultados

PARES_DUPLICADOS = [(12, 97), (16, 32), (22, 55), (33, 77), (57, 63)]
ABAS_ESPERADAS = ["Resultados", "Resumo", "Divergências", "Evidências", "Indicadores"]


@pytest.fixture(scope="module")
def classificadas() -> pd.DataFrame:
    df = preprocessar_avaliacoes(carregar_avaliacoes())
    return classificar_avaliacoes(calcular_metricas(df))


@pytest.fixture(scope="module")
def respostas(classificadas) -> dict[int, int]:
    """Perguntas 1 a 6 como dicionário {número da pergunta: resultado}."""
    tabela = responder_perguntas_1_a_6(classificadas)
    return dict(zip(tabela["Pergunta"], tabela["Resultado"]))


@pytest.fixture(scope="module")
def evidencias(classificadas) -> pd.DataFrame:
    return calcular_evidencias(classificadas)


def _linha(df: pd.DataFrame, id_: int) -> pd.Series:
    return df.loc[df["ID"] == id_].iloc[0]


# ---------- perguntas 1 a 6 ----------

def test_perguntas_somam_100(respostas):
    assert respostas[1] + respostas[2] == 100
    assert respostas[3] + respostas[4] == 100
    assert respostas[5] + respostas[6] == 100


def test_perguntas_conferem_com_as_colunas(classificadas, respostas):
    assert respostas[1] == (classificadas["class_jaccard"] == "POSITIVA").sum()
    assert respostas[3] == (classificadas["class_lev"] == "POSITIVA").sum()
    assert respostas[5] == (classificadas["class_jaccard"] == classificadas["class_lev"]).sum()


def test_tabela_cruzada(classificadas, respostas):
    cruzada = tabela_cruzada(classificadas)
    assert cruzada.loc["Total", "Total"] == 100
    diagonal = cruzada.loc["POSITIVA", "POSITIVA"] + cruzada.loc["NEGATIVA", "NEGATIVA"]
    assert diagonal == respostas[5]
    # Totais das linhas (Jaccard) e das colunas (Levenshtein).
    assert cruzada.loc["POSITIVA", "Total"] == respostas[1]
    assert cruzada.loc["NEGATIVA", "Total"] == respostas[2]
    assert cruzada.loc["Total", "POSITIVA"] == respostas[3]
    assert cruzada.loc["Total", "NEGATIVA"] == respostas[4]


# ---------- divergências ----------

def test_divergencias(classificadas, respostas):
    divergencias = listar_divergencias(classificadas)
    assert len(divergencias) == respostas[6]
    assert (divergencias["Class. Jaccard"] != divergencias["Class. Lev."]).all()
    assert list(divergencias.columns) == list(COLUNAS_TABELA.values())
    assert divergencias["ID"].is_monotonic_increasing


# ---------- evidências ----------

def test_tamanho_das_referencias(classificadas, evidencias):
    indicadores = calcular_indicadores(classificadas, evidencias).set_index("Indicador")["Valor"]
    assert indicadores["Tamanho da referência positiva limpa (caracteres)"] == 170
    assert indicadores["Tamanho da referência negativa limpa (caracteres)"] == 166


def test_parcelas_entre_0_e_1(evidencias):
    for coluna in ["Parcela tam. Lev. Pos.", "Parcela tam. Lev. Neg."]:
        assert evidencias[coluna].between(0, 1).all()


def test_quantidade_de_empates(evidencias):
    assert evidencias["Empate Jaccard"].sum() == 23
    assert evidencias["Empate Lev."].sum() == 10


def test_empate_jaccard_sse_intersecoes_iguais(evidencias):
    intersecoes_iguais = evidencias["Palavras em comum Pos."] == evidencias["Palavras em comum Neg."]
    assert (evidencias["Empate Jaccard"] == intersecoes_iguais).all()


def test_evidencias_id_4(evidencias):
    linha = _linha(evidencias, 4)
    assert linha["Palavras em comum Pos."] == 8
    assert linha["Palavras em comum Neg."] == 8
    assert linha["Empate Jaccard"]
    assert linha["Margem Lev."] == -1


def test_evidencias_id_8(evidencias):
    assert _linha(evidencias, 8)["Empate Lev."]


def test_evidencias_id_1(evidencias):
    linha = _linha(evidencias, 1)
    assert linha["Margem Lev."] == 7
    assert linha["Margem Jaccard"] > 0


@pytest.mark.parametrize("id_a, id_b", PARES_DUPLICADOS)
def test_duplicados_com_classificacoes_identicas(classificadas, id_a, id_b):
    a, b = _linha(classificadas, id_a), _linha(classificadas, id_b)
    assert a["class_jaccard"] == b["class_jaccard"]
    assert a["class_lev"] == b["class_lev"]


def test_funcoes_nao_modificam_a_entrada(classificadas):
    colunas_antes = list(classificadas.columns)
    copia = classificadas.copy()
    responder_perguntas_1_a_6(classificadas)
    tabela_cruzada(classificadas)
    listar_divergencias(classificadas)
    calcular_indicadores(classificadas, calcular_evidencias(classificadas))
    assert list(classificadas.columns) == colunas_antes
    pd.testing.assert_frame_equal(classificadas, copia)


# ---------- arquivo Excel (em tmp_path) ----------

@pytest.fixture
def arquivos(classificadas, tmp_path: Path) -> tuple[Path, Path]:
    """Gera dois arquivos: um só com a SPEC 04 e outro com as abas da SPEC 05."""
    tabela = montar_tabela_resultados(classificadas)
    so_resultados = exportar_excel(tabela, tmp_path / "spec04.xlsx")
    completo = exportar_excel(tabela, tmp_path / "spec05.xlsx")
    exportar_analise(completo, classificadas)
    return so_resultados, completo


def test_ordem_das_abas(arquivos):
    _, completo = arquivos
    assert openpyxl.load_workbook(completo).sheetnames == ABAS_ESPERADAS


def test_aba_resultados_inalterada(arquivos):
    so_resultados, completo = arquivos
    # Mesmos valores...
    pd.testing.assert_frame_equal(
        pd.read_excel(so_resultados, sheet_name="Resultados"),
        pd.read_excel(completo, sheet_name="Resultados"),
    )
    # ...e mesma formatação, célula por célula.
    antes = openpyxl.load_workbook(so_resultados)["Resultados"]
    depois = openpyxl.load_workbook(completo)["Resultados"]
    assert depois.freeze_panes == antes.freeze_panes
    for linha_antes, linha_depois in zip(antes.iter_rows(), depois.iter_rows()):
        for a, d in zip(linha_antes, linha_depois):
            assert (a.value, a.number_format, a.font.bold, a.alignment.wrap_text) == (
                d.value, d.number_format, d.font.bold, d.alignment.wrap_text
            )
    for letra, dimensao in antes.column_dimensions.items():
        assert depois.column_dimensions[letra].width == dimensao.width


@pytest.mark.parametrize("aba", ABAS_ESPERADAS[1:])
def test_abas_novas_formatadas(arquivos, aba):
    _, completo = arquivos
    planilha = openpyxl.load_workbook(completo)[aba]
    cabecalho = [c for c in planilha[1] if c.value is not None]
    assert cabecalho and all(c.font.bold for c in cabecalho)
    assert planilha.freeze_panes == "A2"


def test_resumo_tem_os_dois_blocos(arquivos):
    _, completo = arquivos
    planilha = openpyxl.load_workbook(completo)["Resumo"]
    assert planilha["A1"].value == "Pergunta"
    assert planilha["A7"].value == 6                     # última pergunta
    assert planilha["A8"].value is None and planilha["A9"].value is None  # 2 linhas em branco
    assert planilha["A10"].value == "Cruzamento Jaccard × Levenshtein"
    assert planilha["A14"].value == "Total"
    assert planilha["D14"].value == 100


def test_rodar_duas_vezes_nao_duplica_abas(classificadas, tmp_path: Path):
    caminho = exportar_excel(montar_tabela_resultados(classificadas), tmp_path / "r.xlsx")
    exportar_analise(caminho, classificadas)
    exportar_analise(caminho, classificadas)
    assert openpyxl.load_workbook(caminho).sheetnames == ABAS_ESPERADAS


# ---------- ajuste: correlações com o tamanho e formatos (aba Indicadores) ----------

CORRELACOES_ESPERADAS = {
    "Correlação: tamanho do texto × Lev. Pos.": 0.9476,
    "Correlação: tamanho do texto × Lev. Neg.": 0.8973,
    "Correlação: tamanho do texto × Jaccard Pos.": -0.0249,
    "Correlação: tamanho do texto × Jaccard Neg.": 0.3201,
}


@pytest.fixture(scope="module")
def indicadores(classificadas, evidencias) -> pd.Series:
    """Aba Indicadores como Series {indicador: valor}."""
    return calcular_indicadores(classificadas, evidencias).set_index("Indicador")["Valor"]


@pytest.mark.parametrize("indicador, esperado", CORRELACOES_ESPERADAS.items())
def test_correlacoes_com_o_tamanho(indicadores, indicador, esperado):
    assert indicadores[indicador] == pytest.approx(esperado, abs=0.001)


def test_correlacoes_entre_menos_1_e_1(indicadores):
    for indicador in CORRELACOES_ESPERADAS:
        assert -1 <= indicadores[indicador] <= 1


def _formato_no_excel(arquivo: Path, indicador: str) -> tuple[object, str]:
    """Devolve (valor, formato) da célula Valor de um indicador na aba Indicadores."""
    planilha = openpyxl.load_workbook(arquivo)["Indicadores"]
    for celula_nome, celula_valor, _ in planilha.iter_rows(min_row=2):
        if celula_nome.value == indicador:
            return celula_valor.value, celula_valor.number_format
    raise AssertionError(f"Indicador não encontrado: {indicador}")


def test_correlacoes_no_excel(arquivos):
    _, completo = arquivos
    for indicador, esperado in CORRELACOES_ESPERADAS.items():
        valor, formato = _formato_no_excel(completo, indicador)
        assert formato == "0.00"
        # Valor completo guardado na célula (não arredondado para 2 casas).
        assert valor == pytest.approx(esperado, abs=0.001)
        assert valor != round(valor, 2)


def test_margem_absoluta_lev_em_formato_inteiro(arquivos):
    _, completo = arquivos
    _, formato = _formato_no_excel(completo, "Margem absoluta mediana da Levenshtein (caracteres)")
    assert formato == "0"


def test_formatos_anteriores_preservados(arquivos):
    _, completo = arquivos
    assert _formato_no_excel(completo, "Margem relativa mediana do Jaccard (%)")[1] == "0.0%"
    assert _formato_no_excel(completo, "Tamanho médio das avaliações limpas (caracteres)")[1] == "0.0000"
    assert _formato_no_excel(completo, "Empates no Jaccard")[1] == "General"
