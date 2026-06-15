import streamlit as st
import os
import pandas as pd

from mongo_manager import (
    criar_solicitacao_arte,
    carregar_solicitacoes_arte,
    aprovar_solicitacao_arte,
    rejeitar_solicitacao_arte,
    converter_solicitacao_em_tarefa,
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
        ["Integrantes", "Liderança", "Solicitações"]
    )

    st.markdown(
        "<h1 style='color:#115a8a;'>📹 Ministério de Mídia</h1>",
        unsafe_allow_html=True
    )

    if menu == "Integrantes":
        interface_midia_integrantes()

    elif menu == "Liderança":
        interface_admin_midia()

    elif menu == "Solicitações":
        interface_solicitacoes_arte()


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
        "🎨 Aprovar Solicitações",
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
        
    elif sub == "🎨 Aprovar Solicitações":
        aprovacao_solicitacoes()


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
                            
# ================= Solicitações =================
def interface_solicitacoes_arte():
    
    if st.session_state.get("arte_enviada"):
        st.success("✅ Solicitação enviada com sucesso!")

    st.subheader("🎨 Solicitações")

    tab1, tab2 = st.tabs([
        "➕ Nova Solicitação",
        "📋 Solicitações"
    ])

    # ================= NOVA SOLICITAÇÃO =================
    with tab1:
        
        with st.expander("ℹ️ Informações e dúvidas frequentes!", expanded=False):

            st.markdown("""
            ℹ️ Informações Importantes

            Este espaço foi criado para que os líderes dos ministérios possam solicitar artes ao Ministério de Mídia, 
            seja para exibição na projeção durante os cultos e eventos, 
            seja para divulgação nas redes sociais da igreja.
            Nosso objetivo é organizar as demandas, otimizar o fluxo de trabalho da equipe e manter um padrão visual em todas as artes produzidas.

            Após realizar sua solicitação, pedimos que envie uma mensagem para a liderança da mídia via WhatsApp informando que o pedido foi registrado.

            Importante: este formulário não substitui a comunicação com a liderança. Caso seja necessário realizar ajustes, complementações ou esclarecer dúvidas sobre a solicitação, você poderá entrar em contato normalmente pelo WhatsApp.

            📞 Contato da Liderança de Mídia

            • Beatriz Moraes – (11) 94261-4410
            • Andressa Mandar – (11) 94315-6150

            ❓ Dúvidas Frequentes

            Com quantos dias de antecedência devo solicitar uma arte?

            Resposta: Recomendamos que as solicitações sejam realizadas com pelo menos 30 dias de antecedência. No entanto, entendemos que podem surgir situações excepcionais. Nesses casos, faça a solicitação normalmente e entre em contato com a liderança da mídia pelo WhatsApp para informar a urgência.

            Quem pode solicitar artes?

            Resposta: As solicitações devem ser realizadas pelos líderes dos ministérios da igreja.

            As solicitações são apenas para eventos?

            Resposta: Não. Além de artes para eventos, você também pode solicitar materiais para avisos, comunicados, campanhas, projeção, redes sociais e outras necessidades relacionadas à comunicação visual da igreja.

            """)

        with st.form("form_solicitacao"):
            
            ministerio = st.text_input(
                "Ministério"
            )

            titulo = st.text_input(
                "Título da Arte"
            )

            descricao = st.text_area(
                "Descrição(informações que deseja na arte)"
            )
            
            sugestao = st.text_area(
                "Sugestão (Caso tenha já tenha uma ideia de como quer a arte, exemplo: imagem de uma bíblia, imagem de uma cruz...)"
            )

            solicitante = st.text_input(
                "Solicitante(Nome e Telefone)"
            )

            data_evento = st.date_input(
                "Data do Evento"
            )
            
            horario = st.text_input(
                "Horário do Evento"
            )
            
            data_entrega = st.date_input(
                "Data de Entrega"
            )

            enviar = st.form_submit_button(
                "Enviar Solicitação"
            )

            if enviar:

                if not titulo:
                    st.warning(
                        "Informe um título"
                    )
                    return

                criar_solicitacao_arte(
                    ministerio,
                    titulo,
                    descricao,
                    sugestao,
                    solicitante,
                    data_evento.strftime("%d/%m/%Y"),
                    horario,
                    data_entrega.strftime("%d/%m/%Y")
                )

                st.session_state["arte_enviada"] = True
                st.rerun()
                
                st.session_state["titulo_arte"] = ""
                st.session_state["descricao_arte"] = ""
                st.session_state["solicitante_arte"] = ""
                st.session_state["observacoes_arte"] = ""

    # ================= LISTAGEM =================
    with tab2:

        solicitacoes = carregar_solicitacoes_arte()

        if not solicitacoes:
            st.info(
                "Nenhuma solicitação cadastrada."
            )
            return

        for s in solicitacoes:

            titulo = s.get("titulo")
            status = s.get("status")

            with st.expander(
                f"{titulo} - {status}"
            ):
                st.write(
                    f"**Qual ministério?:** {s.get('ministerio','')}"
                )

                st.write(
                    f"**Solicitante:** {s.get('solicitante','')}"
                )
                
                st.write(
                    f"**Descrição(coloque informações que deseja na arte):** {s.get('descricao','')}"
                )
                
                st.write(
                    f"**Nos informe se tem alguma ideia ou sugestão para a arte:** {s.get('sugestao','')}"
                )

                st.write(
                    f"**Data do Evento:** {s.get('data_evento','')}"
                )
                
                st.write(
                    f"**Horário do Evento:** {s.get('horario','')}"
                )

                
                st.write(
                    f"**Entregar arte até qual data?:** {s.get('data_entrega','')}"
                )

                # ===== APROVAÇÃO =====
                if status == "Pendente":

                    col1, col2 = st.columns(2)


                # ===== CONVERTER =====
                elif status == "Aprovado":

                    if st.button(
                        "📋 Converter em Tarefa",
                        key=f"converter_{titulo}"
                    ):

                        converter_solicitacao_em_tarefa(
                            titulo
                        )

                        st.success(
                            "✅ Convertida para o Kanban!"
                        )

                        st.rerun()

                elif status == "Tarefa":

                    st.success(
                        "✔ Já convertida em tarefa."
                    )

                elif status == "Rejeitado":

                    st.error(
                        "❌ Solicitação rejeitada."
                    )
                    
                    
def aprovacao_solicitacoes():

    st.subheader("🎨 Aprovação de Solicitações")

    solicitacoes = carregar_solicitacoes_arte()

    if not solicitacoes:
        st.info("Nenhuma solicitação encontrada.")
        return

    for s in solicitacoes:

        titulo = s.get("titulo", "")
        status = s.get("status", "")

        with st.expander(
            f"{titulo} - {status}"
        ):

            st.write(
                f"**Ministério:** {s.get('ministerio','')}"
            )

            st.write(
                f"**Título da Arte:** {titulo}"
            )

            st.write(
                f"**Solicitante:** {s.get('solicitante','')}"
            )

            st.write(
                f"**Descrição:** {s.get('descricao','')}"
            )

            st.write(
                f"**Sugestão para a arte:** {s.get('sugestao','')}"
            )

            st.write(
                f"**Data do Evento:** {s.get('data_evento','')}"
            )

            st.write(
                f"**Horário do Evento:** {s.get('horario','')}"
            )

            st.write(
                f"**Data de Entrega:** {s.get('data_entrega','')}"
            )

            st.write(
                f"**Status:** {status}"
            )

            st.divider()

            # ================= PENDENTE =================
            if status == "Pendente":

                col1, col2 = st.columns(2)

                with col1:

                    if st.button(
                        "✅ Aprovar",
                        key=f"aprovar_{titulo}"
                    ):

                        aprovar_solicitacao_arte(
                            titulo
                        )

                        st.success(
                            "Solicitação aprovada!"
                        )

                        st.rerun()

                with col2:

                    if st.button(
                        "❌ Reprovar",
                        key=f"reprovar_{titulo}"
                    ):

                        rejeitar_solicitacao_arte(
                            titulo
                        )

                        st.success(
                            "Solicitação reprovada!"
                        )

                        st.rerun()

            # ================= APROVADO =================
            elif status == "Aprovado":

                if st.button(
                    "📋 Converter em tarefa",
                    key=f"converter_{titulo}"
                ):

                    converter_solicitacao_em_tarefa(
                        titulo
                    )

                    st.success(
                        "Convertida para o Kanban!"
                    )

                    st.rerun()

            # ================= Tarefa =================
            elif status == "Tarefa":

                st.success(
                    "✔ Solicitação já convertida em tarefa."
                )

            # ================= REJEITADO =================
            elif status == "Rejeitado":

                st.error(
                    "❌ Solicitação rejeitada."
                )