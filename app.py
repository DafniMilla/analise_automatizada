import os
import streamlit as st



BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PASTA_HTML = os.path.join(BASE_DIR, "notebooks")

st.set_page_config(layout="wide")

st.title("Visualização das Análises SISU")

os.makedirs(PASTA_HTML, exist_ok=True)



try:
    conteudo = os.listdir(PASTA_HTML)
except FileNotFoundError:
    conteudo = []


arquivos_html = [
    arq for arq in conteudo
    if arq.lower().endswith(".html")
]


if not arquivos_html:

    st.warning(
        f"""
Nenhum arquivo HTML encontrado em:

{PASTA_HTML}

Execute primeiro o arquivo:

processamento.py

para gerar os relatórios HTML e CSV.
"""
    )

else:

    arquivos_html.sort()

    opcao = st.selectbox(
        "Escolha a análise:",
        arquivos_html,
    )

    caminho = os.path.join(PASTA_HTML, opcao)

    if os.path.exists(caminho):

        with open(caminho, "r", encoding="utf-8") as f:
            html = f.read()

        
        st.components.v1.html(
            html,
            height=900,
            scrolling=True
        )

    else:
        st.error(f"Arquivo HTML não encontrado: {caminho}")