import streamlit as st
import os
import pandas as pd

from mongo_manager import (
    carregar_escala_midia,
    carregar_escala_midia_por_data,
    carregar_integrantes_midia,
    editar_tarefa_midia,
    excluir_integrante_midia,
    excluir_tarefa_midia,
    salvar_data_midia,
    carregar_datas_midia,
    excluir_data_midia,
    salvar_escala_midia,
    carregar_funcoes_midia,
    criar_tarefa_midia,
    carregar_tarefas_midia,
    atualizar_status_tarefa_midia,
    salvar_integrante_midia,
    carregar_disponibilidade_midia_por_data
)

from session_manager import (
    login_admin_midia,
    check_login,
    logout_admin
)

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

    st.markdown(
        "<h1 style='color:#115a8a;'>📹 Ministério de Mídia</h1>",
        unsafe_allow_html=True
    )

    if menu == "Integrantes":
        interface_midia_integrantes()

    elif menu == "Liderança":
        interface_admin_midia()


# ================= ADMIN =================
def interface_admin_midia():

    check_login()

    if not st.session_state.get("admin_logado", False):

        st.subheader("🔒 Acesso restrito - Liderança")

        senha = st.text_input(
            "Digite a senha",
            type="password"
        )

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
        gerenciar_integrantes()

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
        tipo = st.selectbox(
            "Tipo",
            ["Quinta", "Domingo", "Outros"]
        )

    tipo_personalizado = None

    if tipo == "Outros":

        tipo_personalizado = st.text_input(
            "Digite o tipo do evento"
        )

    if st.button("Salvar data", use_container_width=True):

        tipo_final = tipo

        if tipo == "Outros":

            if not tipo_personalizado:
                st.warning("Digite o nome do evento")
                return

            tipo_final = tipo_personalizado

        salvar_data_midia(
            data.strftime("%d/%m/%Y"),
            tipo_final
        )

        st.success("✅ Data salva!")
        st.rerun()

    dados = pd.DataFrame(
        carregar_datas_midia() or []
    )

    st.dataframe(
        dados,
        use_container_width=True
    )

    if not dados.empty:

        d = st.selectbox(
            "Excluir data",
            dados["Data"]
        )

        if st.button("Excluir data", use_container_width=True):

            excluir_data_midia(d)

            st.success("🗑️ Data excluída!")
            st.rerun()


# ================= ESCALA =================
def criar_escala():

    st.subheader("🗓️ Criar escala")

    datas = carregar_datas_midia()

    if not datas:
        st.warning("Cadastre datas primeiro")
        return

    df = pd.DataFrame(datas)

    df["Data_Tipo"] = (
        df["Data"] + " - " + df["Tipo"]
    )

    data_tipo = st.selectbox(
        "Escolha a data",
        df["Data_Tipo"]
    )

    linha = df[
        df["Data_Tipo"] == data_tipo
    ].iloc[0]

    data = linha["Data"]
    tipo = linha["Tipo"]

    _, funcoes, _ = carregar_funcoes_midia()

    disponibilidade = carregar_disponibilidade_midia_por_data(data)

    if not disponibilidade:
        st.warning(
            "Ninguém informou disponibilidade para essa data"
        )
        return

    integrantes = []

    for d in disponibilidade:

        nome = d.get("Nome") or d.get("nome")

        if nome:
            integrantes.append(nome)

    integrantes = sorted(list(set(integrantes)))

    # 🔥 CARREGA ESCALA EXISTENTE
    escala_existente = carregar_escala_midia_por_data(data)

    escala_dict = {}

    if escala_existente:

        st.success("✅ Essa data já possui escala salva")

        for pessoa in escala_existente:

            nome = pessoa.get("Nome")

            for funcao in pessoa.get("Funcoes", []):

                if funcao not in escala_dict:
                    escala_dict[funcao] = []

                escala_dict[funcao].append(nome)

        st.info(
            "Você pode editar a escala abaixo."
        )

    st.markdown("### 🎯 Distribuir funções")

    escala = {}

    for f in funcoes:

        valores_iniciais = escala_dict.get(f, [])

        escala[f] = st.multiselect(
            f,
            integrantes,
            default=valores_iniciais,
            key=f"funcao_{data}_{f}"
        )

    texto_botao = (
        "💾 Editar escala"
        if escala_existente
        else "Salvar escala"
    )

    if st.button(
        texto_botao,
        use_container_width=True
    ):

        escala_lista = []

        for f, nomes in escala.items():

            for nome in nomes:

                item = next(
                    (
                        x for x in escala_lista
                        if x["Nome"] == nome
                    ),
                    None
                )

                if item:

                    item["Funcoes"].append(f)

                else:

                    escala_lista.append({
                        "Nome": nome,
                        "Funcoes": [f]
                    })

        salvar_escala_midia(
            data,
            tipo,
            escala_lista
        )

        st.success("✅ Escala salva!")
        st.rerun()


# ================= INTEGRANTES =================
def gerenciar_integrantes():

    st.subheader("👥 Gerenciar Integrantes")

    _, funcoes, _ = carregar_funcoes_midia()

    st.markdown(
        "### ➕ Cadastrar / Editar integrante"
    )

    nome = st.text_input("Nome do integrante")

    funcoes_selecionadas = st.multiselect(
        "Funções",
        funcoes
    )

    if st.button(
        "Salvar integrante",
        use_container_width=True
    ):

        if not nome:
            st.warning("Digite o nome")
            return

        salvar_integrante_midia(
            nome,
            funcoes_selecionadas
        )

        st.success(
            "✅ Integrante salvo com sucesso!"
        )

        st.rerun()

    st.markdown(
        "### 📋 Integrantes cadastrados"
    )

    nomes = carregar_integrantes_midia()

    if not nomes:
        st.info("Nenhum integrante cadastrado")
        return

    df = pd.DataFrame({
        "Nome": nomes
    })

    st.dataframe(
        df,
        use_container_width=True
    )

    st.markdown("### ❌ Excluir integrante")

    nome_excluir = st.selectbox(
        "Selecione o integrante",
        nomes
    )

    if st.button(
        "Excluir integrante",
        use_container_width=True
    ):

        excluir_integrante_midia(nome_excluir)

        st.success("🗑️ Integrante excluído!")

        st.rerun()


# ================= TAREFAS =================
def criar_tarefa_ui():

    st.subheader("➕ Criar tarefa")

    titulo = st.text_input(
        "Título da tarefa"
    )

    if st.button(
        "Criar tarefa",
        use_container_width=True
    ):

        if not titulo:
            st.warning("Digite o título")
            return

        criar_tarefa_midia(titulo)

        st.success(
            "✅ Tarefa criada com sucesso!"
        )

        st.rerun()


# ================= KANBAN =================
def kanban():

    st.subheader("📋 Quadro de tarefas")

    tarefas = carregar_tarefas_midia() or []

    col1, col2, col3 = st.columns(3)

    # ================= A FAZER =================
    with col1:

        st.markdown("### 📝 A Fazer")

        for t in tarefas:

            if t.get("status") == "A Fazer":

                titulo = t.get("titulo")

                with st.expander(titulo):

                    novo_titulo = st.text_input(
                        "Editar título",
                        value=titulo,
                        key=f"editar_afazer_{titulo}"
                    )

                    c1, c2 = st.columns(2)

                    with c1:

                        if st.button(
                            "💾 Salvar",
                            key=f"save_afazer_{titulo}"
                        ):

                            editar_tarefa_midia(
                                titulo,
                                novo_titulo
                            )

                            st.success(
                                "✅ Tarefa editada!"
                            )

                            st.rerun()

                    with c2:

                        if st.button(
                            "🗑️ Excluir",
                            key=f"delete_afazer_{titulo}"
                        ):

                            excluir_tarefa_midia(titulo)

                            st.success(
                                "🗑️ Tarefa excluída!"
                            )

                            st.rerun()

    # ================= FAZENDO =================
    with col2:

        st.markdown("### ⚙️ Fazendo")

        for t in tarefas:

            if t.get("status") == "Fazendo":

                titulo = t.get("titulo")

                responsavel = t.get(
                    "responsavel",
                    "Ninguém"
                )

                with st.expander(titulo):

                    st.caption(
                        f"👤 {responsavel}"
                    )

                    novo_titulo = st.text_input(
                        "Editar título",
                        value=titulo,
                        key=f"fazendo_{titulo}"
                    )

                    c1, c2, c3 = st.columns(3)

                    with c1:

                        if st.button(
                            "💾",
                            key=f"edit_fazendo_{titulo}"
                        ):

                            editar_tarefa_midia(
                                titulo,
                                novo_titulo
                            )

                            st.rerun()

                    with c2:

                        if st.button(
                            "✅",
                            key=f"concluir_{titulo}"
                        ):

                            atualizar_status_tarefa_midia(
                                titulo,
                                "Concluído"
                            )

                            st.rerun()

                    with c3:

                        if st.button(
                            "🗑️",
                            key=f"delete_fazendo_{titulo}"
                        ):

                            excluir_tarefa_midia(titulo)

                            st.rerun()

    # ================= CONCLUÍDO =================
    with col3:

        st.markdown("### ✅ Concluído")

        for t in tarefas:

            if t.get("status") == "Concluído":

                titulo = t.get("titulo")

                responsavel = t.get(
                    "responsavel",
                    "N/A"
                )

                with st.expander(titulo):

                    st.caption(
                        f"👤 {responsavel}"
                    )

                    c1, c2 = st.columns(2)

                    with c1:

                        if st.button(
                            "↩️ Reabrir",
                            key=f"reabrir_{titulo}"
                        ):

                            atualizar_status_tarefa_midia(
                                titulo,
                                "A Fazer"
                            )

                            st.rerun()

                    with c2:

                        if st.button(
                            "🗑️ Excluir",
                            key=f"delete_concluido_{titulo}"
                        ):

                            excluir_tarefa_midia(titulo)

                            st.rerun()