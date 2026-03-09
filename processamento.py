import re
import base64
from io import BytesIO
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid", context="talk",  palette="colorblind")

historico_notas = []


def gerar_grafico(fig):

    buf = BytesIO()

    fig.savefig(
        buf,
        format="png",
        dpi=120,
        bbox_inches="tight"
    )

    plt.close(fig)

    return base64.b64encode(buf.getvalue()).decode("utf-8")


def processar_arquivo(caminho_csv):

    print("Lendo:", caminho_csv)

    nome = Path(caminho_csv).stem

    match = re.search(r"(\d{4})_(\d)", nome)

    sufixo = f"{match.group(1)}_{match.group(2)}" if match else nome
    sufixo_titulo = sufixo.replace("_",".")

    colunasSelecionadas = [
        'nu_ano','cod_ies','ies','uf_campus',
        'municipio_campus','nome_curso','grau',
        'turno','tp_modalidade','tp_sexo',
        'municipio_candidato','nu_notacorte',
        'st_aprovado','st_matricula',
        'dt_nascimento'
    ]

    try:
        microdados = pd.read_csv(caminho_csv, sep=",", encoding="utf-8")
    except:
        microdados = pd.read_csv(caminho_csv, sep="|", encoding="utf-8", decimal=",")

    microdados.columns = microdados.columns.str.lower()

    colunas_existentes = [c for c in colunasSelecionadas if c in microdados.columns]

    microdados = microdados[colunas_existentes]

# FILTRO CURSOS TI

    padrao_ti = (
        "Engenharia da Computação|"
        "Ciência da Computação|"
        "Análise e Desenvolvimento de Sistemas|"
        "Sistemas de Informação|"
        "Redes de Computadores|"
        "Sistemas Para Internet|"
        "Engenharia de Software"
    )

    microdados = microdados[
        microdados["nome_curso"].str.contains(padrao_ti, case=False, na=False)
    ]

# MODALIDADE

    modalidade = {
        "A":"Ampla concorrência",
        "V":"Escola pública",
        "L":"PPI + Escola pública",
        "B":"Integral escola pública"
    }

    microdados["tp_modalidade"] = microdados["tp_modalidade"].map(modalidade)

# GÊNERO

    microdados["tp_sexo"] = microdados["tp_sexo"].map({
        "M":"Masculino",
        "F":"Feminino"
    })

# FILTROS

    microdados = microdados[
        (microdados["st_aprovado"]=="S") &
        (microdados["st_matricula"]=="S")
    ]

    if microdados.empty:
        return None

# IDADE

    ano_ref = int(microdados["nu_ano"].iloc[0])

    microdados["dt_nascimento"] = pd.to_numeric(
        microdados["dt_nascimento"], errors="coerce"
    )

    microdados["idade"] = ano_ref - microdados["dt_nascimento"]

    microdados["idade"] = microdados["idade"].clip(15,80)

    microdados.dropna(subset=["idade"], inplace=True)

# NOTA

    microdados["nu_notacorte"] = pd.to_numeric(
        microdados["nu_notacorte"], errors="coerce"
    )

    microdados.dropna(subset=["nu_notacorte"], inplace=True)

    microdados = microdados[
        microdados["nu_notacorte"].between(400,1000)
    ]

# MÉTRICAS

    media_notacorte = microdados["nu_notacorte"].mean()
    mediana_notacorte = microdados["nu_notacorte"].median()
    media_idade = microdados["idade"].mean()
    total_candidatos = len(microdados)

# HISTÓRICO PARA EVOLUÇÃO
    historico_notas.append({
         "ano": ano_ref,
         "media_nota": media_notacorte
})
    
    fluxo = (
         microdados
    .groupby(["municipio_candidato","municipio_campus"])
    .size()
    .reset_index(name="qtd")
    .sort_values("qtd", ascending=False)
    .head(10)
)


# SALVAR CSV

    BASE_DIR = Path(__file__).resolve().parent
    pasta_resultados = BASE_DIR / "resultados"
    pasta_resultados.mkdir(exist_ok=True)

    caminho_csv_saida = pasta_resultados / f"dados_tratados_{sufixo}.csv"

    microdados.to_csv(caminho_csv_saida, index=False)


# GRÁFICOS

# GÊNERO POR CURSO

    fig = plt.figure(figsize=(14,8))
    sns.countplot(
        data=microdados,
        x="nome_curso",
        hue="tp_sexo",
        palette={"Masculino":"#297BFF","Feminino":"#FF3EA8"}
    )
    plt.xticks(rotation=30)
    plt.title("Gênero por Curso")
    img_genero = gerar_grafico(fig)

# GÊNERO GERAL

    fig = plt.figure(figsize=(7,5))
    sns.countplot(data=microdados, x="tp_sexo", palette="Set1")
    plt.title("Distribuição Geral por Gênero")
    img_genero_geral = gerar_grafico(fig)

# MODALIDADE

    fig = plt.figure(figsize=(8,5))
    sns.countplot(data=microdados, x="tp_modalidade", palette="Set2")
    plt.title("Aprovados por Modalidade")
    img_modalidade = gerar_grafico(fig)

# IDADE

    fig = plt.figure(figsize=(10,5))
    sns.histplot(microdados["idade"], bins=25, kde=True, color="#001F52")
    plt.title("Distribuição Idade")
    img_idade = gerar_grafico(fig)

# IDADE POR CURSO

    fig = plt.figure(figsize=(12,7))
    sns.boxplot(data=microdados, x="idade", y="nome_curso", palette="pastel"
)
    plt.title("Idade por Curso")
    img_idade_curso = gerar_grafico(fig)

# TURNOS

    fig = plt.figure(figsize=(8,5))
    sns.countplot(data=microdados, x="turno", palette="muted")
    plt.title("Turnos Escolhidos")
    img_turno = gerar_grafico(fig)

# MUNICÍPIOS

    topMun = microdados["municipio_campus"].value_counts().head(10).reset_index()
    topMun.columns = ["Municipio","Qtd"]

    fig = plt.figure(figsize=(12,6))
    sns.barplot(data=topMun, x="Qtd", y="Municipio", palette="viridis")
    plt.title("Top Municípios Campus")
    img_mun = gerar_grafico(fig)

# NOTA POR UF

    rankingUF = microdados.groupby("uf_campus")["nu_notacorte"].mean().reset_index()

    fig = plt.figure(figsize=(10,5))
    sns.barplot(data=rankingUF, x="uf_campus", y="nu_notacorte", color="#e6fd65")
    plt.title("Nota Média por UF")
    img_uf = gerar_grafico(fig)

# RANKING CURSOS

    ranking = (
        microdados
        .groupby("nome_curso")["nu_notacorte"]
        .mean()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )

    fig = plt.figure(figsize=(12,6))
    sns.barplot(data=ranking, x="nu_notacorte", y="nome_curso", palette="viridis")
    plt.title("Ranking Média Nota")
    img_rank = gerar_grafico(fig)

    # FLUXO ORIGEM -> DESTINO

    fluxo["fluxo"] = fluxo["municipio_candidato"] + " → " + fluxo["municipio_campus"]

    fig = plt.figure(figsize=(12,6))

    sns.barplot(
        data=fluxo,
        x="qtd",
        y="fluxo", 
        color="#ff7e33"
)

    plt.title("Principais Fluxos de Origem → Destino")
    plt.xlabel("Quantidade de Alunos")
    plt.ylabel("Fluxo")

    img_fluxo = gerar_grafico(fig)


    origem = (
        microdados["municipio_candidato"]
    .value_counts()
    .head(10)
    .reset_index()
)

    origem.columns = ["Municipio","Qtd"]

    fig = plt.figure(figsize=(12,6))

    sns.barplot(
        data=origem,
        x="Qtd",
        y="Municipio"
)

    plt.title("Principais Municípios de Origem dos Candidatos"  )

    img_origem = gerar_grafico(fig)

# HTML 


    html = f"""
<html>
<head>
<meta charset="UTF-8">
<style>
body{{font-family:Arial;margin:40px}}
img{{width:100%;margin-bottom:40px}}
</style>
</head>

<body>

<h1>Análise SISU {sufixo_titulo}</h1>

<h2>Métricas</h2>
<p>Total de Candidatos: {total_candidatos}</p>
<p>Média Nota Corte: {media_notacorte:.2f}</p>
<p>Mediana: {mediana_notacorte:.2f}</p>
<p>Média Idade: {media_idade:.1f}</p>

<h2>Distribuição de Gênero por Curso</h2>
<img src="data:image/png;base64,{img_genero}"/>

<h2>Distribuição Geral de Gênero entre os Aprovados</h2>
<img src="data:image/png;base64,{img_genero_geral}"/>

<h2>Aprovados por Modalidade de Concorrência</h2>
<img src="data:image/png;base64,{img_modalidade}"/>

<h2>Distribuição da Idade dos Estudantes Aprovados</h2>
<img src="data:image/png;base64,{img_idade}"/>

<h2>Distribuição da Idade por Curso</h2>
<img src="data:image/png;base64,{img_idade_curso}"/>

<h2>Distribuição de Matrículas por Turno</h2>
<img src="data:image/png;base64,{img_turno}"/>

<h2>Principais Municípios com Oferta de Cursos</h2>
<img src="data:image/png;base64,{img_mun}"/>

<h2>Média da Nota de Corte por Unidade Federativa</h2>
<img src="data:image/png;base64,{img_uf}"/>

<h2>Ranking dos Cursos mais Concorridos</h2>
<img src="data:image/png;base64,{img_rank}"/>

<h2>Principais Fluxos de Origem e Destino dos Estudantes</h2>
<img src="data:image/png;base64,{img_fluxo}"/>

<h2>Municípios de Origem dos Candidatos</h2>
<img src="data:image/png;base64,{img_origem}"/>

</body>
</html>
"""

    return sufixo, html



# MAIN


if __name__ == "__main__":

    BASE_DIR = Path(__file__).resolve().parent
    pasta_dados = BASE_DIR / "dados"
    pasta_saida = BASE_DIR / "notebooks"
    pasta_saida.mkdir(exist_ok=True)

    arquivos = list(pasta_dados.rglob("*.csv"))

    for arquivo in arquivos:

        resultado = processar_arquivo(str(arquivo))

        if resultado is None:
            continue

        sufixo, html = resultado

        caminho_html = pasta_saida / f"analise_{sufixo}.html"

        with open(caminho_html,"w",encoding="utf-8") as f:
            f.write(html)

        print("Relatório gerado:", caminho_html)

# GRÁFICO EVOLUÇÃO


df_hist = pd.DataFrame(historico_notas)


df_hist = df_hist.groupby("ano").mean().reset_index()

df_hist = df_hist.sort_values("ano")

fig = plt.figure(figsize=(12,6))

plt.plot(
    df_hist["ano"],
    df_hist["media_nota"],
    marker="o",
    linewidth=3
)

for i, row in df_hist.iterrows():
    plt.text(
        row["ano"],
        row["media_nota"] + 2,
        f"{row['media_nota']:.1f}",
        ha="center",
        fontsize=12
    )

    plt.title("Evolução da Média da Nota de Corte por Ano", fontsize=18)

    plt.xlabel("Ano", fontsize=14)

    plt.ylabel("Média da Nota de Corte", fontsize=14)

    plt.xticks(df_hist["ano"])

    plt.grid(True, linestyle="--", alpha=0.5)

    img = gerar_grafico(fig)

    html_evolucao = f"""
<html>
<head>
<meta charset="UTF-8">
<style>
body{{font-family:Arial;margin:40px}}
img{{width:100%}}
</style>
</head>
<body>

<h1>Evolução das Notas ao Longo dos Anos</h1>

<img src="data:image/png;base64,{img}"/>

</body>
</html>
"""

    caminho_html = pasta_saida / "evolucao_notas.html"

    with open(caminho_html,"w",encoding="utf-8") as f:
        f.write(html_evolucao)

    print("Gráfico evolução gerado:", caminho_html)