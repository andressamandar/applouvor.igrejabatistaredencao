import streamlit as st
import pandas as pd

ARQ_ESCALA = "escala_final.csv"

FUNCAO_EMOJI_MAP = {
    "Violão": "Violão🎶",
    "Teclado": "Teclado 🎹",
    "Cajon": "Cajon🥁",
    "Bateria": "Bateria🥁",
    "Guitarra": "Guitarra 🎸",
    "Baixo": "Baixo 🎸",
    "Soprano": "Soprano🎤",
    "Contralto": "Contralto🎤",
    "Tenor": "Tenor 🎤",
    "Baritono": "Baritono 🎤",
    "Ministração": "MinistraçãoⓂ️",
    "Sonoplastia": "Sonoplastia🔊",
    "Projeção": "Projeção🖥️"
}

def aplicar_emojis(celula):
    if pd.isna(celula):
        return ""
    funcoes = [f.strip() for f in str(celula).split(",") if f.strip()]
    return ", ".join(FUNCAO_EMOJI_MAP.get(f, f) for f in funcoes)

def interface_escala_do_mes():
    st.markdown("<h1 style='color:#115a8a;'> Escala do Mês", unsafe_allow_html=True)

    try:
        escala_df = pd.read_csv(ARQ_ESCALA)
    except FileNotFoundError:
        st.warning("A escala ainda não foi criada.")
        return
    except pd.errors.EmptyDataError:
        st.warning("O arquivo de escala está vazio.")
        return
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar a escala: {e}")
        return

    # Remove colunas indesejadas como "Unnamed: 0", "Unnamed: 1", etc.
    escala_df = escala_df.loc[:, ~escala_df.columns.str.contains('^Unnamed')]

    if escala_df.empty or "Nome" not in escala_df.columns:
        st.info("Nenhum integrante escalado ainda.")
        return

    nomes = escala_df["Nome"].dropna().unique().tolist()
    nomes.sort()

    nome_escolhido = st.selectbox("Selecione seu nome para ver sua escala:", ["Selecione seu nome"] + nomes)

    # Botão para ver escala completa
    if st.button("👥 Ver Escala Completa"):
        st.markdown("### Escala Completa")
        escala_com_emoji = escala_df.copy()
        for col in escala_com_emoji.columns[1:]:  # Ignora a coluna "Nome"
            escala_com_emoji[col] = escala_com_emoji[col].apply(aplicar_emojis)
        st.dataframe(escala_com_emoji.set_index("Nome"))
        st.markdown("---")

    if nome_escolhido and nome_escolhido != "Selecione seu nome":
        st.markdown(f"### Escala de {nome_escolhido}")

        linha = escala_df[escala_df["Nome"] == nome_escolhido]

        if linha.empty:
            st.info("Você ainda não foi escalado este mês.")
            return

        dados = []
        for data in escala_df.columns[1:]:
            funcoes = linha[data].values[0] if data in linha else ""
            if pd.notna(funcoes) and str(funcoes).strip():
                funcoes_com_emoji = aplicar_emojis(funcoes)
                dados.append((data, funcoes_com_emoji))

        if dados:
            for data, funcoes in dados:
                st.markdown(f"📅 **{data}** — {funcoes}")
        else:
            st.info("Você ainda não foi escalado este mês.")
