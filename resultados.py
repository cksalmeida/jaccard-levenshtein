"""Tabela de resultados e exportação para Excel.

Quinta etapa do fluxo:
leitura → pré-processamento → métricas → classificação → resultados

- montar_tabela_resultados: deixa a tabela no formato da seção 7 do enunciado;
- exportar_excel: grava o arquivo Excel pedido na entrega (seção 10).
"""

from pathlib import Path

import pandas as pd
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter

# Mesma ideia do CAMINHO_PADRAO de leitura.py: calculado a partir deste
# arquivo, para funcionar de qualquer pasta de onde o programa seja executado.
RAIZ_PROJETO = Path(__file__).resolve().parent
CAMINHO_RESULTADOS = RAIZ_PROJETO / "resultados" / "resultados_classificacao.xlsx"

NOME_ABA = "Resultados"

# Coluna interna → nome na tabela final, na ordem da seção 7 do enunciado.
# Um dicionário Python preserva a ordem de inserção, então ele define tanto os
# nomes quanto a ordem das colunas.
COLUNAS_TABELA = {
    "ID": "ID",
    "avaliacao": "Avaliação",
    "jaccard_pos": "Jaccard Pos.",
    "jaccard_neg": "Jaccard Neg.",
    "class_jaccard": "Class. Jaccard",
    "lev_pos": "Lev. Pos.",
    "lev_neg": "Lev. Neg.",
    "class_lev": "Class. Lev.",
}

# Colunas cujos valores são decimais e recebem o formato de 4 casas.
COLUNAS_JACCARD = ["Jaccard Pos.", "Jaccard Neg."]

# Formato numérico do Excel: muda só a EXIBIÇÃO, não o valor guardado.
FORMATO_JACCARD = "0.0000"

# Larguras das colunas no Excel (em "caracteres", a unidade do Excel).
LARGURAS = {
    "ID": 6,
    "Avaliação": 80,
    "Jaccard Pos.": 13,
    "Jaccard Neg.": 13,
    "Class. Jaccard": 15,
    "Lev. Pos.": 10,
    "Lev. Neg.": 10,
    "Class. Lev.": 13,
}


def montar_tabela_resultados(df: pd.DataFrame) -> pd.DataFrame:
    """Monta a tabela final no formato da seção 7 do enunciado.

    Recebe o DataFrame de classificar_avaliacoes() e devolve um NOVO DataFrame
    só com as 8 colunas da tabela, na ordem certa e com os nomes de exibição.
    As colunas auxiliares (texto_limpo, tokens) ficam de fora. A avaliação é o
    texto original e os valores de Jaccard continuam completos.
    """
    tabela = df[list(COLUNAS_TABELA)].rename(columns=COLUNAS_TABELA)
    return tabela.reset_index(drop=True)


def _formatar_planilha(planilha) -> None:
    """Ajusta a aparência da aba já gravada pelo pandas (via openpyxl).

    Recebe a planilha (worksheet do openpyxl) e não devolve nada. Deixa o
    cabeçalho em negrito, congela a primeira linha, aplica o formato de 4
    casas ao Jaccard e ajusta larguras e quebra de texto.
    """
    # Cabeçalho (linha 1) em negrito.
    for celula in planilha[1]:
        celula.font = Font(bold=True)

    # "A2" congela tudo ACIMA da célula A2, ou seja, a linha 1 (cabeçalho):
    # ao rolar para baixo, os nomes das colunas continuam visíveis.
    planilha.freeze_panes = "A2"

    # Percorre as colunas pelo nome do cabeçalho, para não depender de letras fixas.
    for indice, celula_cabecalho in enumerate(planilha[1], start=1):
        nome = celula_cabecalho.value
        letra = get_column_letter(indice)  # 1 → "A", 2 → "B", ...
        planilha.column_dimensions[letra].width = LARGURAS.get(nome, 12)

        # min_row=2 pula o cabeçalho; iter_rows devolve uma tupla por linha.
        for (celula,) in planilha.iter_rows(min_row=2, min_col=indice, max_col=indice):
            if nome in COLUNAS_JACCARD:
                celula.number_format = FORMATO_JACCARD
            if nome == "Avaliação":
                celula.alignment = Alignment(wrap_text=True, vertical="top")
            else:
                celula.alignment = Alignment(vertical="top")


def exportar_excel(tabela: pd.DataFrame, caminho: Path = CAMINHO_RESULTADOS) -> Path:
    """Salva a tabela de resultados num arquivo Excel formatado.

    Recebe a tabela de montar_tabela_resultados() e o caminho de destino (por
    padrão, resultados/resultados_classificacao.xlsx). Cria a pasta se ela não
    existir, sobrescreve o arquivo se ele já existir e devolve o caminho.

    O pandas grava os DADOS; em seguida, o openpyxl ajusta a APARÊNCIA.
    """
    caminho = Path(caminho)
    # parents=True cria pastas intermediárias; exist_ok=True não reclama se já existir.
    caminho.parent.mkdir(parents=True, exist_ok=True)

    # O "with" garante que o arquivo seja fechado e salvo ao final do bloco,
    # mesmo se ocorrer um erro no meio.
    with pd.ExcelWriter(caminho, engine="openpyxl") as escritor:
        tabela.to_excel(escritor, sheet_name=NOME_ABA, index=False)
        # escritor.sheets dá acesso à aba do openpyxl que o pandas acabou de criar.
        _formatar_planilha(escritor.sheets[NOME_ABA])

    return caminho

# Proporções (0 a 1) exibidas como porcentagem: 0.6123 aparece como 61,2%.
FORMATO_PERCENTUAL = "0.0%"
COLUNAS_PERCENTUAIS = {
    "Parcela tam. Lev. Pos.",
    "Parcela tam. Lev. Neg.",
    "Margem rel. Jaccard",
    "Margem rel. Lev.",
}
# Correlações (de −1 a 1) com 2 casas decimais.
FORMATO_CORRELACAO = "0.00"
# Contagens exibidas como número inteiro (3.0 aparece como 3).
FORMATO_INTEIRO = "0"

# Na aba Indicadores, a coluna Valor mistura tipos de valor; o formato de cada
# linha vem de um dicionário {indicador: formato} definido em analise.py.
COLUNA_INDICADOR = "Indicador"
COLUNA_VALOR = "Valor"

# Colunas de texto longo: largas e com quebra de texto.
LARGURAS_TEXTO_LONGO = {"Avaliação": 80, "Explicação": 70}

LARGURA_MAXIMA_AUTOMATICA = 60


def _formatar_aba_analise(planilha, formatos_indicadores: dict[str, str]) -> None:
    """Formata uma aba de análise (via openpyxl), no mesmo padrão da SPEC 04.

    Recebe a planilha e o dicionário {indicador: formato} da aba Indicadores.
    Não devolve nada. Cabeçalho em negrito, linha 1 congelada, larguras
    confortáveis, quebra de texto nas colunas longas e formatos numéricos:
    - coluna Valor de um indicador listado no dicionário → o formato dele;
    - colunas de proporção → porcentagem (0.0%);
    - demais decimais → 4 casas (0.0000).
    """
    for celula in planilha[1]:
        celula.font = Font(bold=True)
    planilha.freeze_panes = "A2"

    for indice, celula_cabecalho in enumerate(planilha[1], start=1):
        nome = celula_cabecalho.value
        letra = get_column_letter(indice)
        celulas = [c for (c,) in planilha.iter_rows(min_row=2, min_col=indice, max_col=indice)]

        # Largura: fixa para textos longos; senão, pelo maior conteúdo da coluna.
        if nome in LARGURAS_TEXTO_LONGO:
            largura = LARGURAS_TEXTO_LONGO[nome]
        else:
            textos = [str(nome)] + [str(c.value) for c in celulas if c.value is not None]
            largura = min(max(len(t) for t in textos) + 2, LARGURA_MAXIMA_AUTOMATICA)
        planilha.column_dimensions[letra].width = largura

        for celula in celulas:
            celula.alignment = Alignment(
                wrap_text=nome in LARGURAS_TEXTO_LONGO, vertical="top"
            )
            formato = _formato_da_celula(planilha, celula, nome, formatos_indicadores)
            if formato:
                celula.number_format = formato


def _formato_da_celula(planilha, celula, nome_coluna: str, formatos_indicadores: dict[str, str]):
    """Escolhe o formato numérico de uma célula (ou None para não mudar nada)."""
    # Aba Indicadores: o nome do indicador fica na coluna A da mesma linha.
    if nome_coluna == COLUNA_VALOR and planilha["A1"].value == COLUNA_INDICADOR:
        indicador = planilha.cell(row=celula.row, column=1).value
        if indicador in formatos_indicadores:
            return formatos_indicadores[indicador]

    # bool é subclasse de int no Python, mas nunca é float: não é afetado.
    if not isinstance(celula.value, float):
        return None
    if nome_coluna in COLUNAS_PERCENTUAIS:
        return FORMATO_PERCENTUAL
    return FORMATO_JACCARD


def adicionar_abas(
    caminho: Path,
    abas: dict[str, pd.DataFrame],
    formatos_indicadores: dict[str, str] | None = None,
) -> None:
    """Acrescenta abas a um Excel existente, sem alterar a aba 'Resultados'.

    Recebe o caminho de um .xlsx já gerado por exportar_excel(), um
    dicionário {nome da aba: tabela} e, opcionalmente, o formato de exibição
    de cada indicador da aba Indicadores ({indicador: formato}). As abas são
    gravadas na ordem do dicionário, depois das que já existem, e formatadas.
    Não devolve nada.

    mode="a" (append) abre o arquivo existente em vez de criar um novo, e
    if_sheet_exists="replace" troca uma aba de mesmo nome que já exista (por
    exemplo, ao rodar o programa duas vezes sobre o mesmo arquivo).
    """
    formatos_indicadores = formatos_indicadores or {}
    with pd.ExcelWriter(caminho, engine="openpyxl", mode="a", if_sheet_exists="replace") as escritor:
        for nome, tabela in abas.items():
            tabela.to_excel(escritor, sheet_name=nome, index=False)
            _formatar_aba_analise(escritor.sheets[nome], formatos_indicadores)


def adicionar_bloco(
    caminho: Path, aba: str, tabela: pd.DataFrame, linha_inicial: int, titulo: str
) -> None:
    """Grava uma tabela extra (com título) abaixo do conteúdo de uma aba existente.

    Recebe o caminho do .xlsx, o nome da aba, a tabela (o índice também é
    gravado, pois nele ficam os rótulos das linhas), a linha onde o título
    deve ficar (contando a partir de 1, como no Excel) e o texto do título.
    Não devolve nada.

    Usa if_sheet_exists="overlay" ("sobrepor"): escreve nas células indicadas
    SEM apagar o resto da aba. Com "replace", a aba inteira seria recriada e o
    conteúdo anterior (as perguntas 1 a 6) se perderia.
    """
    with pd.ExcelWriter(caminho, engine="openpyxl", mode="a", if_sheet_exists="overlay") as escritor:
        # startrow do pandas conta a partir de 0: linha_inicial (base 1) é a
        # linha do título, então a tabela começa logo abaixo dela.
        tabela.to_excel(escritor, sheet_name=aba, startrow=linha_inicial)
        planilha = escritor.sheets[aba]
        celula_titulo = planilha.cell(row=linha_inicial, column=1, value=titulo)
        celula_titulo.font = Font(bold=True)
        for celula in planilha[linha_inicial + 1]:  # cabeçalho da tabela extra
            celula.font = Font(bold=True)

        # Alarga as colunas, se preciso, para caber o conteúdo da tabela extra
        # (a largura anterior foi calculada só para o bloco que já existia).
        for indice in range(1, tabela.shape[1] + 2):  # +1 do índice, +1 porque começa em 1
            letra = get_column_letter(indice)
            linhas = planilha.iter_rows(min_row=linha_inicial + 1, min_col=indice, max_col=indice)
            maior = max(len(str(c.value)) for (c,) in linhas if c.value is not None)
            atual = planilha.column_dimensions[letra].width or 0
            planilha.column_dimensions[letra].width = max(atual, maior + 2)
