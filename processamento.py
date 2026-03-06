import re
import base64
from io import BytesIO
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


sns.set_theme(style="whitegrid", context="talk")

# BASE64
def gerar_grafico(fig):

    buf = BytesIO()

    fig.savefig(
        buf,
        format="png",
        dpi=120,
        bbox_inches="tight"
    )

    plt.close(fig)

    return base64.b64encode(
        buf.getvalue()
    ).decode("utf-8")


# PROCESSAMENTO 
def processar_arquivo(caminho_csv, caminho_saida):

    print("Lendo:", caminho_csv)

    nome = Path(caminho_csv).stem

    match = re.search(r"(\d{4})_(\d)", nome)

    sufixo_ano = (
        f"{match.group(1)}_{match.group(2)}"
        if match else nome
    )

# COLUNAS 

    colunasSelecionadas=[

'nu_ano','cod_ies','ies','uf_campus',
'municipio_campus','nome_curso','grau',
'turno','tp_modalidade','tp_sexo',
'municipio_candidato','nu_notacorte',
'st_aprovado','st_matricula',
'dt_nascimento'

]

    try:

        microdados=pd.read_csv(

caminho_csv,
sep=",",
encoding="utf-8"

)

    except:

        microdados=pd.read_csv(

caminho_csv,
sep="|",
encoding="utf-8",
decimal=","

)

    microdados.columns=microdados.columns.str.lower()

    colunas_existentes=[

c for c in colunasSelecionadas
if c in microdados.columns

]

    microdados=microdados[colunas_existentes]

# cursos TI 

    padrao_ti=(

"Engenharia da Computação|"
"Ciência da Computação|"
"Análise e Desenvolvimento de Sistemas|"
"Sistemas de Informação|"
"Redes de Computadores|"
"Sistemas Para Internet|"
"Engenharia de Software"

)

    microdados=microdados[

microdados["nome_curso"]
.str.contains(padrao_ti,
case=False,
na=False)

]

# modalidade

    modalidade={

"A":"Ampla concorrência",
"V":"Escola pública",
"L":"PPI + Escola pública",
"B":"Integral escola pública"

}

    microdados["tp_modalidade"]=microdados[
"tp_modalidade"].map(modalidade)

# genero 

    microdados["tp_sexo"]=microdados[
"tp_sexo"].map({

"M":"Masculino",
"F":"Feminino"

})

# filtros

    microdados=microdados[

(microdados["st_aprovado"]=="S") &
(microdados["st_matricula"]=="S")

]

# ---------- idade ----------

    if microdados.empty:
        print("Sem dados após filtros.")
        return

    ano_ref=int(microdados["nu_ano"].iloc[0])

    microdados["dt_nascimento"]=pd.to_numeric(

microdados["dt_nascimento"],
errors="coerce"

)

    microdados["idade"]=ano_ref-microdados["dt_nascimento"]

    microdados["idade"]=microdados["idade"].clip(15,80)

    microdados.dropna(subset=["idade"],inplace=True)

# ---------- nota ----------

    microdados["nu_notacorte"]=pd.to_numeric(

microdados["nu_notacorte"],
errors="coerce"

)

    microdados.dropna(
subset=["nu_notacorte"],
inplace=True)

    microdados=microdados[
microdados["nu_notacorte"].between(400,1000)
]

#  MÉTRICAS

    media_notacorte=microdados["nu_notacorte"].mean()

    mediana_notacorte=microdados["nu_notacorte"].median()

    media_idade=microdados["idade"].mean()

# GRÁFICOS

# GENERO POR CURSO

    fig=plt.figure(figsize=(12,6))

    sns.countplot(

data=microdados,
x="nome_curso",
hue="tp_sexo"

)

    plt.xticks(rotation=45)

    plt.title("Gênero por Curso")

    img_genero=gerar_grafico(fig)

# GENERO GERAL

    fig=plt.figure(figsize=(7,5))

    sns.countplot(

data=microdados,
x="tp_sexo"

)

    plt.title("Distribuição Geral por Gênero")

    img_genero_geral=gerar_grafico(fig)

# MODALIDADE

    fig=plt.figure(figsize=(8,5))

    sns.countplot(

data=microdados,
x="tp_modalidade"

)

    plt.title("Aprovados por Modalidade")

    img_modalidade=gerar_grafico(fig)

# IDADE

    fig=plt.figure(figsize=(10,5))

    sns.histplot(

microdados["idade"],
bins=25,
kde=True

)

    plt.title("Distribuição Idade")

    img_idade=gerar_grafico(fig)

# IDADE POR CURSO

    fig=plt.figure(figsize=(12,7))

    sns.boxplot(

data=microdados,
x="idade",
y="nome_curso"

)

    plt.title("Idade por Curso")

    img_idade_curso=gerar_grafico(fig)

# TURNOS

    fig=plt.figure(figsize=(8,5))

    sns.countplot(

data=microdados,
x="turno"

)

    plt.title("Turnos Escolhidos")

    img_turno=gerar_grafico(fig)

# MUNICIPIOS CAMPUS

    topMun=(

microdados["municipio_campus"]
.value_counts()
.head(10)
.reset_index()

)

    topMun.columns=["Municipio","Qtd"]

    fig=plt.figure(figsize=(12,6))

    sns.barplot(

data=topMun,
x="Qtd",
y="Municipio"

)

    plt.title("Top Municípios Campus")

    img_mun=gerar_grafico(fig)

# NOTA POR UF

    rankingUF=(

microdados
.groupby("uf_campus")["nu_notacorte"]
.mean()
.reset_index()

)

    fig=plt.figure(figsize=(10,5))

    sns.barplot(

data=rankingUF,
x="uf_campus",
y="nu_notacorte"

)

    plt.title("Nota Média por UF")

    img_uf=gerar_grafico(fig)

# RANKING CURSO

    ranking=(

microdados
.groupby("nome_curso")["nu_notacorte"]
.mean()
.sort_values(ascending=False)
.head(10)
.reset_index()

)

    fig=plt.figure(figsize=(12,6))

    sns.barplot(

data=ranking,
x="nu_notacorte",
y="nome_curso"

)

    plt.title("Ranking Média Nota")

    img_rank=gerar_grafico(fig)

# HTML 

    html_colunas="".join(

f"<li>{c}</li>"
for c in colunasSelecionadas

)

    html=f"""

<html>

<head>

<meta charset="UTF-8">

<style>

body{{font-family:Arial;margin:40px}}

img{{width:100%;margin-bottom:30px}}

</style>

</head>

<body>

<h1>Relatório SISU {sufixo_ano}</h1>

<h2>Métricas</h2>

<p>Média Nota Corte:{media_notacorte:.2f}</p>

<p>Mediana:{mediana_notacorte:.2f}</p>

<p>Média Idade:{media_idade:.1f}</p>

<h2>Colunas</h2>

<ul>

{html_colunas}

</ul>

<h2>Genero por Curso</h2>
<img src="data:image/png;base64,{img_genero}"/>

<h2>Genero Geral</h2>
<img src="data:image/png;base64,{img_genero_geral}"/>

<h2>Modalidade</h2>
<img src="data:image/png;base64,{img_modalidade}"/>

<h2>Idade</h2>
<img src="data:image/png;base64,{img_idade}"/>

<h2>Idade por Curso</h2>
<img src="data:image/png;base64,{img_idade_curso}"/>

<h2>Turnos</h2>
<img src="data:image/png;base64,{img_turno}"/>

<h2>Municípios</h2>
<img src="data:image/png;base64,{img_mun}"/>

<h2>Nota Média UF</h2>
<img src="data:image/png;base64,{img_uf}"/>

<h2>Ranking Nota</h2>
<img src="data:image/png;base64,{img_rank}"/>

</body>

</html>

"""

    Path(caminho_saida).parent.mkdir(
parents=True,
exist_ok=True
)

    with open(
caminho_saida,
"w",
encoding="utf-8"

) as f:

        f.write(html)

    print("HTML gerado:",caminho_saida)



# MAIN 

if __name__=="__main__":

    BASE_DIR=Path(__file__).resolve().parent

    pasta_dados=BASE_DIR/"dados"

    pasta_saida=BASE_DIR/"notebooks"

    pasta_saida.mkdir(exist_ok=True)

    arquivos=list(pasta_dados.glob("*.csv"))

    for arquivo in arquivos:

        nome=arquivo.stem

        caminho_html=pasta_saida/f"analise_{nome}.html"

        processar_arquivo(

            str(arquivo),
            str(caminho_html)

        )