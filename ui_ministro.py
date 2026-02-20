import streamlit as st
import pandas as pd

from mongo_manager import (
    buscar_ministros,
    buscar_datas_ministro,
    buscar_escala_por_data,
    buscar_louvores_disponiveis,
    verificar_louvor_ja_escolhido,
    salvar_louvores_ministro
)

from session_manager import (
    init_ministro_session,
    login_ministro,
    logout_ministro,
    check_ministro_session
)

# ================== MAPA DE EMOJIS ==================
FUNCAO_EMOJI_MAP = {
    "Ministração": "Ministração 🎤",
    "Soprano": "Soprano 🎶",
    "Contralto": "Contralto 🎶",
    "Tenor": "Tenor 🎶",
    "Barítono": "Barítono 🎶",
    "Teclado": "Teclado 🎹",
    "Violão": "Violão 🎸",
    "Guitarra": "Guitarra 🎸",
    "Baixo": "Baixo 🎸",
    "Bateria": "Bateria 🥁",
    "Cajon": "Cajon 🥁",
    "Projeção": "Projeção 🖥️",
    "Sonoplastia": "Sonoplastia 🔊",
}


def normalizar_nomes(nomes):
    if isinstance(nomes, list):
        return nomes
    if isinstance(nomes, str):
        return [nomes]
    return []


def interface_ministro():
    st.title("🎤 Área do Ministro")

    # ================== SESSÃO ==================
    init_ministro_session()
    check_ministro_session()

    # ================== LOGIN ==================
    if not st.session_state.get("ministro_logado", False):
        st.subheader("🔐 Acesso do Ministro")

        ministros = buscar_ministros()

        nome_ministro = st.selectbox(
            "Selecione seu nome",
            options=ministros,
            index=None,
            placeholder="Escolha seu nome"
        )

        senha = st.text_input("Senha do ministro", type="password")

        if st.button("Entrar"):
            senha_correta = st.secrets["ministro"]["senha"]

            if not nome_ministro:
                st.warning("Selecione seu nome")
            elif senha != senha_correta:
                st.error("Senha incorreta")
            else:
                login_ministro(nome_ministro)
                st.rerun()

        return

    # ================== LOGADO ==================
    nome_ministro = st.session_state["ministro_nome"]
    st.success(f"Bem-vindo(a), **{nome_ministro}** 🎶")

    if st.button("🚪 Sair"):
        logout_ministro()
        st.rerun()

    # ================== DATAS ==================
    datas = buscar_datas_ministro(nome_ministro)

    if not datas:
        st.info("Você não possui ministrações escaladas")
        return

    data_escolhida = st.selectbox(
        "📅 Selecione a data",
        datas,
        format_func=lambda d: f"{d['Data']} - {d['Culto']}"
    )

    # ================== ESCALA COMPLETA (BONITA) ==================
    st.subheader("📋 Escala completa do culto")

    escala = buscar_escala_por_data(data_escolhida["Data"])

    if not escala or not escala.get("Escala"):
        st.info("Nenhuma escala encontrada para esta data")
    else:
        rows = []

        for pessoa in escala["Escala"]:
            nomes = normalizar_nomes(pessoa.get("Nome"))
            funcoes = pessoa.get("Funcoes", [])

            funcoes_formatadas = ", ".join(
                FUNCAO_EMOJI_MAP.get(f, f) for f in funcoes
            )

            for nome in nomes:
                rows.append({
                    "Nome": nome,
                    "Funções": funcoes_formatadas
                })

        df_escala = pd.DataFrame(rows)

        st.dataframe(
            df_escala,
            use_container_width=True,
            hide_index=True
        )

    # ================== LOUVORES ==================
        # ================== LOUVORES ==================
    st.subheader("🎶 Escolha os louvores")

    lista_louvores = buscar_louvores_disponiveis()

    if not lista_louvores:
        st.info("Nenhum louvor cadastrado")
        return

    # 👉 LOUVORES JÁ SALVOS NA ESCALA
    louvores_ja_salvos = escala.get("louvores", []) if escala else []

    louvores_escolhidos = st.multiselect(
        "Selecione um ou mais louvores",
        options=lista_louvores,
        default=louvores_ja_salvos
    )

    # ================== AVISOS ==================
    if louvores_escolhidos:
        for louvor in louvores_escolhidos:
            avisos = verificar_louvor_ja_escolhido(
            data_atual=data_escolhida["Data"],
            louvor=louvor
            )
            for aviso in avisos:
                st.warning(aviso)

    # ================== SALVAR ==================
    if st.button("💾 Salvar louvores"):
        if not louvores_escolhidos:
            st.warning("Selecione ao menos um louvor")
        else:
            salvar_louvores_ministro(
                data=data_escolhida["Data"],
                ministro=nome_ministro,
                louvores=louvores_escolhidos
            )
            st.success("Louvores salvos com sucesso! 🎵")