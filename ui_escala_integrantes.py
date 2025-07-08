import streamlit as st
import pandas as pd

ARQ_ESCALA = "escala_final.csv"

def interface_escala_do_mes():
    st.subheader("\U0001F4CB Escala do Mês")

    try:
        escala_df = pd.read_csv(ARQ_ESCALA)
    except FileNotFoundError:
        st.warning("A escala ainda não foi criada.")
        return

    if escala_df.empty or "Nome" not in escala_df.columns:
        st.info("Nenhum integrante escalado ainda.")
        return

    nomes = escala_df["Nome"].dropna().unique().tolist()
    nomes.sort()

    nome_escolhido = st.selectbox("Selecione seu nome para ver sua escala:", ["Selecione seu nome"] + nomes)

    if nome_escolhido and nome_escolhido != "Selecione seu nome":
        st.markdown(f"### Escala de {nome_escolhido}")

        linha = escala_df[escala_df["Nome"] == nome_escolhido]

        dados = []
        for data in escala_df.columns[1:]:
            funcoes = linha[data].values[0] if data in linha else ""
            if pd.notna(funcoes) and str(funcoes).strip():
                dados.append((data, funcoes.strip(", ")))

        if dados:
            for data, funcoes in dados:
                st.markdown(f"\U0001F4C5 **{data}** — {funcoes}")
        else:
            st.info("Você ainda não foi escalado este mês.")
