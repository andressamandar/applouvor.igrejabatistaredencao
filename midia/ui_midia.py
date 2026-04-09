import streamlit as st
import os
import pandas as pd
from mongo_manager import (
    carregar_integrantes_midia, excluir_integrante_midia, salvar_data_midia, carregar_datas_midia, excluir_data_midia,
    salvar_escala_midia,
    carregar_funcoes_midia,
    criar_tarefa_midia, carregar_tarefas_midia, atualizar_status_tarefa_midia, salvar_integrante_midia
)
from session_manager import login_admin_midia, check_login, logout_admin
from midia.ui_midia_integrantes import interface_midia_integrantes

# ================= MENU PRINCIPAL =================
def interface_midia():

    if os.path.exists("logo.png"):
        st.sidebar.image("logo.png", width=200)

    st.sidebar.title("☰ Menu")

    menu = st.sidebar.radio(
        "Ir para:",
        ["Integrantes", "Liderança"]
    )

    st.markdown("<h1 style='color:#115a8a;'>📹 Ministério de Mídia</h1>", unsafe_allow_html=True)

    if menu == "Integrantes":
        interface_midia_integrantes()

    elif menu == "Liderança":
        interface_admin_midia()


# ================= ADMIN =================
def interface_admin_midia():

    check_login()

    if not st.session_state.get("admin_logado", False):
        st.subheader("🔒 Acesso restrito - Liderança")

        senha = st.text_input("Digite a senha", type="password")

        if st.button("Entrar", use_container_width=True):
            if login_admin_midia(senha):
                st.success("✅ Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("❌ Senha incorreta")
        return

    st.markdown("## 🔒 Área da Liderança")

    col1, col2 = st.columns([8, 1])

    with col2:
        if st.button("🚪 Sair"):
            logout_admin()
            st.rerun()

    sub = st.selectbox(
        "Selecione uma opção:",
        [
            "📅 Gerenciar datas",
            "🗓️ Criar escala",
            "👥 Gerenciar integrantes",
            "➕ Criar tarefas",
            "📋 Quadro de tarefas"
        ]
    )

    if sub == "📅 Gerenciar datas":
        gerenciar_datas()

    elif sub == "🗓️ Criar escala":
        criar_escala()

    elif sub == "👥 Gerenciar integrantes":
        gerenciar_integrantes()  # 🔥 AGORA FUNCIONANDO

    elif sub == "➕ Criar tarefas":
        criar_tarefa_ui()

    elif sub == "📋 Quadro de tarefas":
        kanban()


# ================= DATAS =================
def gerenciar_datas():
    st.subheader("📅 Datas Mídia")

    col1, col2 = st.columns(2)

    with col1:
        data = st.date_input("Data")

    with col2:
        tipo = st.selectbox("Tipo", ["Quinta", "Domingo", "Outros"])

    # 🔥 CAMPO DINÂMICO
    tipo_personalizado = None
    if tipo == "Outros":
        tipo_personalizado = st.text_input("Digite o tipo do evento (ex: Vigília, Culto de Natal...)")

    if st.button("Salvar data", use_container_width=True):

        # 🔥 DEFINE O TIPO FINAL
        tipo_final = tipo

        if tipo == "Outros":
            if not tipo_personalizado:
                st.warning("Digite o nome do evento")
                return
            tipo_final = tipo_personalizado

        salvar_data_midia(data.strftime("%d/%m/%Y"), tipo_final)
        st.success("Data salva!")

    dados = pd.DataFrame(carregar_datas_midia() or [])
    st.dataframe(dados, use_container_width=True)

    if not dados.empty:
        d = st.selectbox("Excluir data", dados["Data"])
        if st.button("Excluir", use_container_width=True):
            excluir_data_midia(d)
            st.rerun()

# ================= ESCALA =================
def criar_escala():
    st.subheader("🗓️ Criar escala")

    datas = carregar_datas_midia()

    if not datas:
        st.warning("Cadastre datas primeiro")
        return

    df = pd.DataFrame(datas)

    col1, col2 = st.columns(2)

    with col1:
        data = st.selectbox("Escolha a data", df["Data"])

    with col2:
        tipo = df[df["Data"] == data]["Tipo"].values[0]

    _, funcoes, integrantes = carregar_funcoes_midia()

    st.markdown("### 🎯 Distribuir funções")

    escala = {}

    for f in funcoes:
        escala[f] = st.multiselect(f, integrantes)

    if st.button("Salvar escala", use_container_width=True):
        escala_lista = []

        for f, nomes in escala.items():
            for nome in nomes:
                item = next((x for x in escala_lista if x["Nome"] == nome), None)

                if item:
                    item["Funcoes"].append(f)
                else:
                    escala_lista.append({
                        "Nome": nome,
                        "Funcoes": [f]
                    })

        salvar_escala_midia(data, tipo, escala_lista)
        st.success("Escala salva com sucesso!")


# ================= INTEGRANTES =================
def gerenciar_integrantes():
    st.subheader("👥 Gerenciar Integrantes")

    _, funcoes, _ = carregar_funcoes_midia()

    # CADASTRAR
    st.markdown("### ➕ Cadastrar / Editar integrante")

    nome = st.text_input("Nome do integrante")
    funcoes_selecionadas = st.multiselect("Funções", funcoes)

    if st.button("Salvar integrante", use_container_width=True):
        if not nome:
            st.warning("Digite o nome")
            return

        salvar_integrante_midia(nome, funcoes_selecionadas)
        st.success("✅ Integrante salvo com sucesso!")
        st.rerun()

    # LISTAR
    st.markdown("### 📋 Integrantes cadastrados")

    nomes = carregar_integrantes_midia()

    if not nomes:
        st.info("Nenhum integrante cadastrado")
        return

    df = pd.DataFrame({"Nome": nomes})
    st.dataframe(df, use_container_width=True)

    # EXCLUIR
    st.markdown("### ❌ Excluir integrante")

    nome_excluir = st.selectbox("Selecione o integrante", nomes)

    if st.button("Excluir integrante", use_container_width=True):
        excluir_integrante_midia(nome_excluir)
        st.success("🗑️ Integrante excluído")
        st.rerun()


# ================= TAREFAS =================
def criar_tarefa_ui():
    st.subheader("➕ Criar tarefa")

    titulo = st.text_input("Título da tarefa")

    if st.button("Criar tarefa", use_container_width=True):
        if not titulo:
            st.warning("Digite o título")
            return

        criar_tarefa_midia(titulo)
        st.success("✅ Tarefa criada com sucesso!")
        st.rerun()


# ================= KANBAN =================
def kanban():
    st.subheader("📋 Quadro de tarefas")

    tarefas = carregar_tarefas_midia() or []

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 📝 A Fazer")
        for t in tarefas:
            if t.get("status") == "A Fazer":
                st.info(t["titulo"])

    with col2:
        st.markdown("### ⚙️ Fazendo")
        for t in tarefas:
            if t.get("status") == "Fazendo":
                titulo = t.get("titulo")
                responsavel = t.get("responsavel", "Ninguém")

                st.write(f"**{titulo}**")
                st.caption(f"👤 {responsavel}")

                if st.button("Concluir", key=titulo + "_lider"):
                    atualizar_status_tarefa_midia(titulo, "Concluído")
                    st.rerun()

    with col3:
        st.markdown("### ✅ Concluído")
        for t in tarefas:
            if t.get("status") == "Concluído":
                titulo = t.get("titulo")
                responsavel = t.get("responsavel", "N/A")

                st.success(titulo)
                st.caption(f"👤 {responsavel}")
