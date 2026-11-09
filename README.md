# Classificador de Avaliações — Jaccard e Levenshtein

Projeto acadêmico (Fatec Registro) do **Estudo de Caso: Classificação de Avaliações de Produtos**.

O programa lê **100 avaliações de clientes** de uma planilha Excel e classifica cada uma como
**POSITIVA** ou **NEGATIVA**, comparando-a com duas avaliações de referência (uma positiva e uma
negativa) por meio de duas métricas de comparação de textos, ambas **implementadas do zero em
Python puro**:

- **Similaridade de Jaccard** — compara os *conjuntos de palavras* dos textos;
- **Distância de Levenshtein** — conta quantas *edições de caracteres* transformam um texto no outro.

No final, o programa gera uma planilha Excel com os resultados de cada avaliação e uma análise
comparando o comportamento das duas métricas.

---

## Sumário

- [Como funciona](#como-funciona)
- [As métricas](#as-métricas)
- [Regras de classificação](#regras-de-classificação)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Como rodar](#como-rodar)
- [Saída gerada](#saída-gerada)
- [Testes](#testes)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Módulos em detalhe](#módulos-em-detalhe)
- [Resultados obtidos](#resultados-obtidos)
- [Decisões de projeto](#decisões-de-projeto)
- [Solução de problemas](#solução-de-problemas)

---

## Como funciona

O programa é um *pipeline* (uma linha de montagem): cada etapa recebe o resultado da anterior,
acrescenta alguma informação e passa adiante.

```
┌────────────┐   ┌──────────────────┐   ┌──────────────────────┐   ┌───────────────┐   ┌──────────────┐   ┌──────────┐
│  Leitura   │ → │ Pré-processamento│ → │ Jaccard e Levenshtein│ → │ Classificação │ → │  Resultados  │ → │ Análise  │
│ (Excel)    │   │ (limpeza/tokens) │   │ (4 valores/avaliação)│   │ (POS/NEG × 2) │   │ (tabela/xlsx)│   │ (abas)   │
└────────────┘   └──────────────────┘   └──────────────────────┘   └───────────────┘   └──────────────┘   └──────────┘
  leitura.py      preprocessamento.py         metricas.py            classificacao.py     resultados.py     analise.py
```

1. **Leitura** — abre `dados/avaliacoes.xlsx`, confere se o arquivo existe, se tem as colunas `ID` e
   `avaliacao`, se não há textos vazios nem IDs repetidos.
2. **Pré-processamento** — padroniza os textos: letras minúsculas, pontuação removida, espaços extras
   eliminados, e divide cada texto em palavras (*tokens*).
3. **Métricas** — para cada avaliação, calcula 4 números: Jaccard com a referência positiva e com a
   negativa, e Levenshtein com a positiva e com a negativa.
4. **Classificação** — decide POSITIVA ou NEGATIVA **separadamente** para cada métrica.
5. **Resultados** — monta a tabela final e grava o Excel formatado.
6. **Análise** — acrescenta ao Excel abas que respondem às perguntas da atividade e reúnem
   evidências para comparar as métricas.

---

## As métricas

### Similaridade de Jaccard

Trata cada texto como um **conjunto de palavras** (sem repetição e sem ordem) e mede quanto os
dois conjuntos se sobrepõem:

```
J(A, B) = |A ∩ B| / |A ∪ B|
          ─────────   ─────────
          palavras    todas as palavras
          em comum    dos dois textos (sem repetir)
```

- Vai de **0** (nenhuma palavra em comum) a **1** (exatamente as mesmas palavras).
- **Quanto MAIOR, mais parecidos** são os textos.

Exemplo: `A = {o, produto, é, bom}` e `B = {o, produto, é, ruim}`
→ interseção = `{o, produto, é}` (3) · união = `{o, produto, é, bom, ruim}` (5) → **J = 3/5 = 0,6**.

### Distância de Levenshtein

Conta o **menor número de operações de caractere** — inserir, remover ou substituir — necessárias
para transformar um texto no outro.

- Vai de **0** (textos idênticos) até o tamanho do maior texto.
- **Quanto MENOR, mais parecidos** são os textos.

Exemplo: `gato → rato` = 1 (substitui *g* por *r*); `casa → casas` = 1 (insere *s*).

A implementação usa **programação dinâmica**: uma tabela em que a célula `[i][j]` guarda a distância
entre os `i` primeiros caracteres de um texto e os `j` primeiros do outro. Cada célula é calculada a
partir de três vizinhas já conhecidas (cima = remover, esquerda = inserir, diagonal = substituir ou
manter), e a resposta final fica no canto inferior direito — exatamente como se faz o cálculo à mão.

> Nenhuma biblioteca de distância de texto é usada no programa. A biblioteca `rapidfuzz` aparece
> **somente nos testes**, como "gabarito" para conferir que a nossa Levenshtein dá o resultado certo.

---

## Regras de classificação

As regras vêm da seção 6 do enunciado e são aplicadas **separadamente** para cada métrica:

| Métrica     | Condição                    | Classificação |
|-------------|-----------------------------|---------------|
| Jaccard     | `jaccard_pos > jaccard_neg` | POSITIVA      |
| Jaccard     | `jaccard_pos <= jaccard_neg`| NEGATIVA      |
| Levenshtein | `lev_pos < lev_neg`         | POSITIVA      |
| Levenshtein | `lev_pos >= lev_neg`        | NEGATIVA      |

Os sinais são opostos porque Jaccard é **similaridade** (maior = mais parecido) e Levenshtein é
**distância** (menor = mais parecido). Em caso de **empate**, as duas métricas classificam como
**NEGATIVA**.

### Avaliações de referência (enunciado, seção 3)

- **Positiva:** "O produto possui excelente qualidade, chegou rapidamente e atendeu completamente às
  minhas expectativas. Gostei muito da compra e recomendo este produto para outras pessoas."
- **Negativa:** "O produto possui péssima qualidade, apresentou problemas logo após a compra e não
  atendeu às minhas expectativas. Fiquei muito decepcionado e não recomendo este produto."

As referências passam pelo **mesmo pré-processamento** das avaliações, para que a comparação seja
justa.

---

## Pré-requisitos

| Ferramenta | Versão  | Para quê                                                    |
|------------|---------|-------------------------------------------------------------|
| Python     | 3.12+   | Linguagem do projeto                                        |
| [uv](https://docs.astral.sh/uv/) | recente | Gerencia o Python, o ambiente virtual e as dependências |
| Git        | qualquer| Para clonar o repositório                                    |

O **uv** substitui o `pip` e o `venv`: ele cria o ambiente virtual automaticamente e instala as
versões exatas registradas no `uv.lock`, garantindo que todo mundo rode o projeto com as mesmas
bibliotecas. Se o Python 3.12 não estiver instalado, o próprio uv baixa a versão indicada em
`.python-version`.

### Instalando o uv

**macOS / Linux:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**macOS com Homebrew:**

```bash
brew install uv
```

**Windows (PowerShell):**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Confira a instalação com `uv --version`.

---

## Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/cksalmeida/jaccard-levenshtein.git
cd jaccard-levenshtein

# 2. Instale as dependências (cria a pasta .venv automaticamente)
uv sync
```

O `uv sync` instala:

- **Dependências do programa:** `pandas` (tabelas de dados) e `openpyxl` (leitura e escrita de
  arquivos `.xlsx`);
- **Dependências de desenvolvimento:** `pytest` (testes automatizados) e `rapidfuzz` (gabarito da
  Levenshtein nos testes).

> Não é preciso ativar o ambiente virtual: o comando `uv run` já usa o `.venv` do projeto.

---

## Como rodar

```bash
uv run python main.py
```

O programa pode ser executado de qualquer pasta (os caminhos são resolvidos a partir da raiz do
projeto com `pathlib`), por exemplo:

```bash
uv run --project /caminho/para/jaccard-levenshtein python /caminho/para/jaccard-levenshtein/main.py
```

### O que aparece no terminal

O programa imprime um resumo de cada etapa:

```
=== Resumo da leitura ===
Avaliações carregadas: 100
...
=== Resumo do pré-processamento ===
Referência positiva (limpa):
  o produto possui excelente qualidade chegou rapidamente e atendeu completamente às minhas ...
  tokens: 24 | tokens distintos: 22
...
=== Resumo das métricas ===
Tempo de cálculo: 0.81 s

Primeiras 5 avaliações:
 ID  jaccard_pos  jaccard_neg  lev_pos  lev_neg
  1     0.148148     0.127273      192      199
  2     0.122807     0.103448      205      207
  3     0.101695     0.203704      222      215
...
=== Resultados (primeiras 10 linhas) ===
 ID  Avaliação                          Jaccard Pos.  Jaccard Neg. Class. Jaccard  Lev. Pos.  Lev. Neg. Class. Lev.
  1  Na minha experiência, Excelente...       0.1481        0.1273       POSITIVA        192        199    POSITIVA
...
Arquivo Excel gerado: .../resultados/resultados_classificacao.xlsx
Abas: Resultados, Resumo, Divergências, Evidências, Indicadores
```

---

## Saída gerada

O arquivo **`resultados/resultados_classificacao.xlsx`** é criado (ou sobrescrito) a cada execução,
com 5 abas:

| Aba              | Conteúdo                                                                                         |
|------------------|--------------------------------------------------------------------------------------------------|
| **Resultados**   | Tabela final (enunciado, seção 7): `ID`, `Avaliação`, `Jaccard Pos.`, `Jaccard Neg.`, `Class. Jaccard`, `Lev. Pos.`, `Lev. Neg.`, `Class. Lev.` |
| **Resumo**       | Respostas numéricas das perguntas 1 a 6 (seção 9) e a tabela cruzada Jaccard × Levenshtein      |
| **Divergências** | Avaliações em que as duas métricas discordaram                                                  |
| **Evidências**   | Indicadores por avaliação: tamanho do texto, palavras em comum, margens de decisão, empates etc. |
| **Indicadores**  | Resumo geral: correlações com o tamanho do texto, número de empates, margens medianas etc.       |

Detalhes de formatação: cabeçalho em negrito, primeira linha congelada (fica visível ao rolar),
Jaccard exibido com 4 casas decimais, proporções em porcentagem e quebra de linha nas colunas de
texto longo. O arredondamento é **só de exibição** — as células guardam os valores completos.

---

## Testes

```bash
uv run pytest -v
```

São **126 testes** automatizados com `pytest`, um arquivo por módulo:

| Arquivo                          | O que verifica                                                                 |
|----------------------------------|--------------------------------------------------------------------------------|
| `tests/test_leitura.py`          | Leitura das 100 avaliações, IDs únicos, textos intactos e erros (arquivo ausente, coluna faltando) |
| `tests/test_preprocessamento.py` | Minúsculas, remoção de pontuação, espaços, acentos preservados, tokenização     |
| `tests/test_metricas.py`         | Jaccard e Levenshtein em casos conhecidos e comparação com o `rapidfuzz`        |
| `tests/test_classificacao.py`    | Regras de classificação, incluindo os empates                                   |
| `tests/test_resultados.py`       | Colunas, ordem e formatação da tabela e do Excel                                |
| `tests/test_analise.py`          | Perguntas 1 a 6, tabela cruzada, divergências, evidências e indicadores         |

Saída esperada (resumida):

```
126 passed in 4.65s
```

Para rodar só um arquivo ou um teste específico:

```bash
uv run pytest tests/test_metricas.py -v
uv run pytest -k levenshtein -v
```

---

## Estrutura do projeto

```
jaccard-levenshtein/
├── README.md                este arquivo
├── pyproject.toml           configuração do projeto e dependências (uv)
├── uv.lock                  versões exatas das dependências
├── .python-version          versão do Python usada pelo uv (3.12)
├── main.py                  ponto de entrada: orquestra as etapas e imprime os resumos
├── leitura.py               leitura e validação do Excel
├── preprocessamento.py      limpeza e tokenização dos textos
├── referencias.py           textos das avaliações de referência
├── metricas.py              Jaccard e Levenshtein (do zero)
├── classificacao.py         regras POSITIVA / NEGATIVA
├── resultados.py            tabela final e exportação/formatação do Excel
├── analise.py               perguntas da atividade e evidências comparativas
├── dados/
│   └── avaliacoes.xlsx      entrada: 100 avaliações (colunas ID e avaliacao)
├── docs/
│   └── enunciado.pdf        enunciado da atividade
├── resultados/
│   └── resultados_classificacao.xlsx   saída gerada pelo programa
└── tests/                   testes automatizados (pytest)
```

---

## Módulos em detalhe

### `leitura.py`

- `carregar_avaliacoes(caminho)` → `DataFrame` com as colunas `ID` e `avaliacao`, textos **sem
  nenhuma alteração**.
- Validações com mensagens de erro em português: arquivo inexistente (`FileNotFoundError`), coluna
  ausente, avaliação vazia e ID repetido (`ValueError`).
- Avaliações com texto duplicado **não** são removidas: o enunciado trata as 100 avaliações como o
  conjunto a classificar.

### `preprocessamento.py`

- `limpar_texto(texto)` → minúsculas, pontuação trocada por espaço (para não colar palavras:
  `"bom,ótimo"` vira `"bom ótimo"`), espaços repetidos reduzidos a um. **Acentos são mantidos.**
- `tokenizar(texto_limpo)` → lista de palavras.
- `preprocessar_avaliacoes(df)` → cópia do DataFrame com as colunas `texto_limpo` (usada pela
  Levenshtein) e `tokens` (usada pelo Jaccard).

### `referencias.py`

Constantes `REFERENCIA_POSITIVA` e `REFERENCIA_NEGATIVA`, copiadas literalmente do enunciado.

### `metricas.py`

- `similaridade_jaccard(tokens_a, tokens_b)` → `float` de 0 a 1.
- `distancia_levenshtein(texto_a, texto_b)` → `int`, pela tabela completa de programação dinâmica.
- `calcular_metricas(df)` → acrescenta `jaccard_pos`, `jaccard_neg`, `lev_pos` e `lev_neg`.

### `classificacao.py`

- `classificar_jaccard(pos, neg)` e `classificar_levenshtein(pos, neg)` → `"POSITIVA"` ou `"NEGATIVA"`.
- `classificar_avaliacoes(df)` → acrescenta `class_jaccard` e `class_lev`.

### `resultados.py`

- `montar_tabela_resultados(df)` → as 8 colunas da seção 7, na ordem e com os nomes de exibição.
- `exportar_excel(tabela)` → grava a aba **Resultados** (o pandas grava os dados; o openpyxl ajusta a
  aparência).
- `adicionar_abas(...)` e `adicionar_bloco(...)` → acrescentam as abas de análise sem apagar o que já
  existe.

### `analise.py`

- `responder_perguntas_1_a_6(df)` → contagens de POSITIVAS/NEGATIVAS por métrica, concordâncias e
  divergências.
- `tabela_cruzada(df)` → matriz Jaccard × Levenshtein.
- `listar_divergencias(df)` → avaliações em que as métricas discordam.
- `calcular_evidencias(df)` e `calcular_indicadores(df, evidencias)` → números que sustentam as
  respostas escritas das perguntas 7 e 8 (qual métrica parece mais adequada e por quê).
- `exportar_analise(caminho, df)` → grava as abas Resumo, Divergências, Evidências e Indicadores.

### `main.py`

Chama as etapas na ordem, mede o tempo do cálculo das métricas e imprime um resumo de cada etapa.

---

## Resultados obtidos

Com o arquivo `dados/avaliacoes.xlsx` fornecido:

| Pergunta | Descrição                                               | Resultado |
|:--------:|---------------------------------------------------------|:---------:|
| 1        | Avaliações POSITIVAS pelo Jaccard                        | 29        |
| 2        | Avaliações NEGATIVAS pelo Jaccard                        | 71        |
| 3        | Avaliações POSITIVAS pela Levenshtein                    | 43        |
| 4        | Avaliações NEGATIVAS pela Levenshtein                    | 57        |
| 5        | Avaliações com a MESMA classificação nas duas métricas   | 66        |
| 6        | Avaliações com classificações DIFERENTES                 | 34        |

**Tabela cruzada** (linhas = Jaccard, colunas = Levenshtein):

| Jaccard ↓ / Lev. → | NEGATIVA | POSITIVA | Total |
|--------------------|:--------:|:--------:|:-----:|
| NEGATIVA           | 47       | 24       | 71    |
| POSITIVA           | 10       | 19       | 29    |
| Total              | 57       | 43       | 100   |

**Alguns indicadores da análise:**

- As referências limpas têm **170** e **166** caracteres; as avaliações limpas têm entre **232** e
  **309** (média ≈ 268). Em média, **mais da metade** da distância de Levenshtein vem só da diferença
  de tamanho entre os textos.
- Correlação entre o tamanho do texto e a Levenshtein: **0,95** (positiva) e **0,90** (negativa) — a
  distância acompanha quase linearmente o tamanho do texto. Para o Jaccard, a correlação fica perto de
  zero (**−0,02** na positiva).
- A decisão típica da Levenshtein é tomada por uma margem mediana de apenas **3 caracteres**
  (≈ 1,6% da distância), contra uma margem relativa mediana de ≈ 20% no Jaccard.
- Empates: **23** no Jaccard e **10** na Levenshtein (todos classificados como NEGATIVA, pela regra
  do enunciado).
- Conferência de consistência: os **5** pares de avaliações com texto idêntico receberam as mesmas
  classificações.

> Não há rótulo de sentimento real no arquivo de entrada, então as métricas são comparadas **entre
> si**; o programa não calcula taxa de acerto.

---

## Decisões de projeto

- **Métricas do zero:** Jaccard e Levenshtein são implementadas em Python puro, para que o raciocínio
  de cada uma fique visível no código.
- **Sem arredondar antes de classificar:** os valores de Jaccard são comparados completos;
  arredondar antes poderia criar empates falsos (ex.: 0,1481 e 0,1479 viram ambos 0,15).
- **Representações separadas:** `texto_limpo` (string) alimenta a Levenshtein, que compara
  caracteres; `tokens` (lista) alimenta o Jaccard, que compara palavras.
- **Acentos e stopwords mantidos:** o pré-processamento segue exatamente o pedido no enunciado
  (minúsculas, pontuação, espaços e tokenização), sem etapas extras.
- **Funções puras:** cada etapa devolve uma **cópia** do DataFrame com colunas novas, sem modificar a
  entrada — facilita testar e entender cada passo isoladamente.
- **Caminhos com `pathlib`** resolvidos a partir do próprio arquivo, para o programa funcionar de
  qualquer pasta.
- **Código em português:** nomes de funções e variáveis em português (sem acentos), com docstrings e
  comentários didáticos.

---

## Solução de problemas

| Problema                                              | Solução                                                                 |
|-------------------------------------------------------|-------------------------------------------------------------------------|
| `command not found: uv`                               | Instale o uv (veja [Pré-requisitos](#pré-requisitos)) e abra um novo terminal. |
| `Arquivo de avaliações não encontrado`                | Confira se `dados/avaliacoes.xlsx` existe na raiz do projeto.            |
| `Coluna(s) obrigatória(s) ausente(s)`                 | A primeira aba do Excel precisa ter as colunas `ID` e `avaliacao`.      |
| `PermissionError` ao gravar o resultado               | Feche o `resultados_classificacao.xlsx` no Excel e rode de novo.        |
| `ModuleNotFoundError: No module named 'pandas'`       | Rode com `uv run ...` (e não `python ...` direto) ou execute `uv sync`. |

---

## Tecnologias

- [Python 3.12](https://www.python.org/)
- [uv](https://docs.astral.sh/uv/) — gerenciamento de projeto e dependências
- [pandas](https://pandas.pydata.org/) — manipulação de tabelas
- [openpyxl](https://openpyxl.readthedocs.io/) — leitura e formatação de arquivos Excel
- [pytest](https://docs.pytest.org/) — testes automatizados
- [RapidFuzz](https://github.com/rapidfuzz/RapidFuzz) — usado apenas nos testes, como referência

---

Projeto desenvolvido para a disciplina da **Fatec Registro**.
