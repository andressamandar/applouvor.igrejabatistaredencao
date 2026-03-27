import datetime
import io
import streamlit as st
import streamlit.components.v1 as components
from mongo_manager import (
    carregar_louvores_lista, carregar_datas, salvar_data, excluir_data,
    carregar_disponibilidade,carregar_integrantes, carregar_funcoes, salvar_escala, carregar_escala, atualizar_louvores_escala
)
from session_manager import login_admin
import streamlit as st
import pandas as pd
from ui_louvores import interface_admin_louvores, interface_integrantes_louvores
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, LongTable
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

FUNCAO_EMOJI_MAP = {
    "Ministração": "MinistraçãoⓂ️","Soprano": "Soprano🎤","Contralto": "Contralto🎤",
    "Tenor": "Tenor 🎤","Baritono": "Baritono 🎤","Teclado": "Teclado 🎹",
    "Violão": "Violão🎶","Cajon": "Cajon🥁","Bateria": "Bateria🥁",
    "Guitarra": "Guitarra 🎸", "Baixo": "Baixo 🎸", "Projeção": "Projeção🖥️",
    "Sonoplastia": "Sonoplastia🔊"
}



# ------------------ Helpers ------------------
def show_round_svg_loader(text="Carregando..."):
    svg = f"""
    <div style="display:flex;align-items:center;gap:10px">
      <div style="width:28px;height:28px">
        <svg width="28" height="28" viewBox="0 0 50 50">
          <circle cx="25" cy="25" r="20" stroke="#115a8a" stroke-width="4" fill="none" stroke-opacity="0.2"/>
          <path d="M25 5 A20 20 0 0 1 45 25" stroke="#115a8a" stroke-width="4" fill="none">
            <animateTransform attributeName="transform" attributeType="XML" type="rotate" from="0 25 25" to="360 25 25" dur="1s" repeatCount="indefinite"/>
          </path>
        </svg>
      </div>
      <div style="font-size:14px;color:#333;">{text}</div>
    </div>
    """
    st.markdown(svg, unsafe_allow_html=True)
    
def normalizar_nomes(nomes):
    if isinstance(nomes, list):
        return nomes
    if isinstance(nomes, str):
        return [nomes]
    return []


def load_with_spinner(fn, *args, label="Carregando informações...", **kwargs):
    placeholder = st.empty()
    with placeholder.container():
        with st.spinner(label):
            show_round_svg_loader(label)
            result = fn(*args, **kwargs)
    placeholder.empty()
    return result

def parse_date_str(data_str):
    try:
        return datetime.datetime.strptime(data_str, "%d/%m/%Y").date()
    except Exception:
        return None

def trigger_refresh():
    st.session_state['refresh'] = not st.session_state.get('refresh', False)

def get_integrante_names(integrantes):
    """
    Garante que retornamos uma lista de nomes (strings) a partir de 'integrantes'
    que pode ser: ['Nome1','Nome2'] ou [{'Nome': 'A'}, {'nome':'B'}] etc.
    """
    if not integrantes:
        return []
    names = []
    for item in integrantes:
        if isinstance(item, str):
            names.append(item)
        elif isinstance(item, dict):
            # tenta chaves comuns
            n = item.get('Nome') or item.get('nome') or item.get('name')
            if n:
                names.append(n)
    # remove duplicados e preserva ordem
    seen = set()
    out = []
    for n in names:
        if n not in seen:
            out.append(n)
            seen.add(n)
    return out

def disponibilidade_is_true(val):
    """Trata diferentes formatos para representar 'Disponivel'."""
    if val is None:
        return False
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val != 0
    if isinstance(val, str):
        return val.strip().lower() in ("true", "1", "sim", "s", "yes", "y")
    return False

# ------------------ Interface ------------------
def interface_admin():
    
    if not st.session_state.get('admin_logado', False):
        senha = st.text_input("Senha do Admin:", type="password")
        if st.button("Login"):
            if login_admin(senha):
                st.success("Login realizado com sucesso!")
                st.session_state['admin_logado'] = True
                trigger_refresh()
                return
            else:
                st.warning("Senha incorreta")
        return

    sub_menu = st.selectbox("Escolha uma opção de administração:", [
        "Gerenciar datas",
        "Criar escala",
        "Editar escala",
        "Escolher louvores",
        "Gerenciar louvores",
        "Escala e Download",
        "Visualizar disponibilidades"   
    ])


    # Carregar dados uma vez (com loader)
    if 'datas_df' not in st.session_state:
        datas = load_with_spinner(carregar_datas, label="Carregando datas do banco...")
        st.session_state['datas_df'] = pd.DataFrame(datas) if datas else pd.DataFrame()
    if 'disp_df' not in st.session_state:
        disp = load_with_spinner(carregar_disponibilidade, label="Carregando disponibilidades...")
        st.session_state['disp_df'] = pd.DataFrame(disp) if disp else pd.DataFrame()
    if 'df_funcoes' not in st.session_state or 'funcoes' not in st.session_state:
        df_funcoes, FUNCOES, INTEGRANTES = load_with_spinner(carregar_funcoes, label="Carregando funções e integrantes...")
        st.session_state['df_funcoes'] = df_funcoes if df_funcoes is not None else pd.DataFrame()
        st.session_state['funcoes'] = FUNCOES or []
        st.session_state['integrantes'] = INTEGRANTES or []

    if sub_menu == "Gerenciar datas":
        gerenciar_datas()
    elif sub_menu == "Criar escala":
        interface_escalar_funcoes()
    elif sub_menu == "Editar escala":
        interface_editar_escala()
    elif sub_menu == "Gerenciar louvores":
        interface_admin_louvores()
    elif sub_menu == "Escolher louvores":
        interface_escolher_louvores()
    elif sub_menu =="Escala e Download":
        download_escala_final()
    elif sub_menu == "Visualizar disponibilidades":
        interface_visualizar_disponibilidades()
        
    if "success_msg_admin" in st.session_state and st.session_state.success_msg_admin:
        st.success(st.session_state.success_msg_admin)
        st.session_state.success_msg_admin = ""


# ------------------ Gerenciar Datas ------------------
def gerenciar_datas():
    datas_df = st.session_state['datas_df']
    st.subheader("Cadastro de Datas de Cultos")
    data_input = st.date_input("Escolha uma data:", min_value=datetime.date.today())
    tipo = st.selectbox("Tipo de culto:", ["Ceia", "Quinta", "Domingo", "Outros"])

    if st.button("Adicionar data"):
        data_str = data_input.strftime("%d/%m/%Y")
        salvar_data(data_str, tipo)
        st.success(f"Data adicionada: {data_str} com sucesso!")
        st.session_state['datas_df'] = pd.DataFrame(load_with_spinner(carregar_datas, label="Atualizando datas..."))
        trigger_refresh()

    st.subheader("Datas cadastradas")
    st.dataframe(datas_df)

    st.subheader("Excluir data")
    if not datas_df.empty:
        data_para_excluir = st.selectbox("Selecione a data a excluir:", datas_df['Data'].unique())
        if st.button("Excluir data selecionada"):
            excluir_data(data_para_excluir)
            st.success(f"Data {data_para_excluir} excluída com sucesso!")
            st.session_state['datas_df'] = pd.DataFrame(load_with_spinner(carregar_datas, label="Atualizando datas..."))
            trigger_refresh()
    else:
        st.info("Nenhuma data cadastrada.")

# ------------------ Criar Escala ------------------
def interface_escalar_funcoes():
    disp_df = st.session_state.get('disp_df', pd.DataFrame())
    df_funcoes = st.session_state.get('df_funcoes', pd.DataFrame())
    FUNCOES = st.session_state.get('funcoes', [])
    datas_df = st.session_state.get('datas_df', pd.DataFrame())
    integrantes_raw = st.session_state.get('integrantes', [])
    integrantes = get_integrante_names(integrantes_raw)

    if datas_df.empty:
        st.warning("⚠️ Nenhuma data cadastrada ainda. Adicione datas antes de criar a escala.")
        return

    ordem_desejada = ["Ministração","Sonoplastia","Bateria","Violão","Teclado","Cajon","Soprano", "Contralto", "Tenor", 
                        "Baritono", "Guitarra", "Baixo", "Projeção"]
    FUNCOES_ordenadas = [f for f in ordem_desejada if f in FUNCOES]

    datas_cadastradas = sorted(datas_df['Data'].unique())
    escalas = load_with_spinner(carregar_escala, label="Carregando escalas...")
    datas_escaladas = [esc['Data'] for esc in escalas] if escalas else []

    hoje = datetime.date.today()
    datas_futuras = [d for d in datas_cadastradas if parse_date_str(d) and parse_date_str(d) >= hoje]
    datas_para_escalar = [d for d in datas_futuras if d not in datas_escaladas]

    if not datas_para_escalar:
        st.warning("Todas as datas futuras cadastradas já foram escaladas (ou não há datas futuras).")
        return

    data_escolhida = st.selectbox("Escolha a data para escalar:", datas_para_escalar)
    tipo_culto = datas_df.loc[datas_df['Data'] == data_escolhida, 'Tipo'].values[0]

    # Status de disponibilidade
    preenchidos = set()
    if not disp_df.empty:
        col_nome = 'Nome' if 'Nome' in disp_df.columns else ('nome' if 'nome' in disp_df.columns else None)
        if col_nome:
            preenchidos = set(disp_df[disp_df['Data'] == data_escolhida][col_nome].dropna().astype(str).tolist())

    faltando = [n for n in integrantes if n not in preenchidos]
    presentes = [n for n in integrantes if n in preenchidos]

    if not faltando and len(integrantes) > 0:
        st.success("✅ Todos os integrantes já preencheram a disponibilidade!")
    else:
        st.warning("⚠️ Ainda existem integrantes que não preencheram a disponibilidade.")
        # --- Dentro de ui_admin.py, na função interface_escalar_funcoes() ---

    if not faltando and len(integrantes) > 0:
        st.success("✅ Todos já preencheram!")
    else:
        if not faltando and len(integrantes) > 0:
            st.success("✅ Todos já preencheram!")
        else:
            with st.expander("📋 Status de Disponibilidade"):

                texto_copia = "📊 STATUS DE DISPONIBILIDADE\n\n"
                texto_copia += "✅ Disponibilidade Preenchida:\n" + ("\n".join([f"- {n}" for n in presentes]) if presentes else "Nenhum")
                texto_copia += "\n\n❌ Falta Preencher Disponidade:\n" + ("\n".join([f"- {n}" for n in faltando]) if faltando else "Nenhum")

                # Botão copiar funcional
                components.html(f"""
                    <button onclick="navigator.clipboard.writeText(`{texto_copia}`)"
                    style="
                        background-color:#115a8a;
                        color:white;
                        padding:8px 12px;
                        border:none;
                        border-radius:6px;
                        cursor:pointer;
                        font-size:14px;
                    ">
                    📋 Copiar lista
                    </button>
                """, height=50)

                st.divider()

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Disponibilidade Preenchida**")
                    for nome in presentes:
                        st.write(f"✅ {nome}")

                with col2:
                    st.markdown("**Falta Preencher Disponidade**")
                    for nome in faltando:
                        st.write(f"❌ {nome}")


    # Escala por função
    st.subheader("🎯 Escalar por Função")

    disponiveis = []
    if not disp_df.empty:
        for r in disp_df.to_dict('records'):
            data_r = r.get('Data') or r.get('data')
            if data_r != data_escolhida:
                continue
            nome_r = r.get('Nome') or r.get('nome') or r.get('NomeCompleto')
            dispo_raw = r.get('Disponivel') if 'Disponivel' in r else r.get('disponivel') if 'disponivel' in r else r.get('Disponibilidade')
            if nome_r and disponibilidade_is_true(dispo_raw):
                disponiveis.append(nome_r)
    seen = set(); disponiveis = [x for x in disponiveis if not (x in seen or seen.add(x))]

    if len(disponiveis) == 0:
        st.warning("Ninguém se disponibilizou para esta data ainda.")
        return

    escala_escolhidos = {f: [] for f in FUNCOES_ordenadas}
    for funcao in FUNCOES_ordenadas:
        habilitados = []
        if not df_funcoes.empty and funcao in df_funcoes.columns:
            try:
                habilitados = df_funcoes[df_funcoes[funcao] == "ok"]['Nome'].tolist()
            except Exception:
                habilitados = [r.get('Nome') or r.get('nome') for r in df_funcoes.to_dict('records') if r.get(funcao) == "ok"]

        candidatos = [n for n in disponiveis if n in habilitados] if habilitados else list(disponiveis)

        # Criar opções de selectbox com aviso de "já escalado", exceto Ministração
        opcoes = [""]
        for n in candidatos:
            if funcao != "Ministração" and n in escala_escolhidos.values():
                opcoes.append(f"{n} (escalado em Ministração)")
            else:
                opcoes.append(n)

        # pessoas já escaladas em outras funções
        avisos = {}
        for f, nomes in escala_escolhidos.items():
            for n in nomes:
                avisos.setdefault(n, []).append(f)

        opcoes = candidatos

        selecionados = st.multiselect(
            f"{funcao}:",
            options=opcoes,
            key=f"{funcao}_{data_escolhida}"
        )

        for nome in selecionados:
            if nome in avisos:
                funcoes_previas = ", ".join(avisos[nome])
                st.caption(f"⚠️ {nome} já escalado também em: {funcoes_previas}")

        escala_escolhidos[funcao] = selecionados


    # Pré-visualização
    if escala_escolhidos:
        st.subheader("📋 Pré-visualização da Escala do Dia")
        for funcao, nome in escala_escolhidos.items():
            st.write(f"{funcao}: {nome}")

        # Salvar escala
        if st.button("Salvar Escala"):
            escala_temp = []
            for funcao, nome in escala_escolhidos.items():
                item = next((p for p in escala_temp if p["Nome"] == nome), None)
                if item:
                    if funcao not in item["Funcoes"]:
                        item["Funcoes"].append(funcao)
                else:
                    escala_temp.append({"Nome": nome, "Funcoes": [funcao]})

            salvar_escala(data_escolhida, tipo_culto, escala_temp)
            
            st.session_state.success_msg_admin = f"✅ Escala de {data_escolhida} salva com sucesso!"
            st.rerun()


# ------------------ Editar Escala ------------------
# ------------------ Editar Escala ------------------
# ------------------ Editar Escala ------------------
def interface_editar_escala():
    disp_df = st.session_state.get('disp_df', pd.DataFrame())
    df_funcoes = st.session_state.get('df_funcoes', pd.DataFrame())
    FUNCOES = st.session_state.get('funcoes', [])
    datas_df = st.session_state.get('datas_df', pd.DataFrame())
    integrantes_raw = st.session_state.get('integrantes', [])
    integrantes = get_integrante_names(integrantes_raw)

    escalas_existentes = load_with_spinner(carregar_escala, label="Carregando escalas...")
    if not escalas_existentes:
        st.warning("⚠️ Nenhuma escala foi criada ainda.")
        return

    # ---------------- FILTRO DE DATAS FUTURAS ----------------
    hoje = datetime.date.today()
    datas_escaladas = sorted(
        [esc['Data'] for esc in escalas_existentes if parse_date_str(esc['Data']) and parse_date_str(esc['Data']) >= hoje]
    )

    if not datas_escaladas:
        st.info("Não há datas futuras para editar a escala.")
        return

    data_escolhida = st.selectbox("Escolha a data para editar a escala:", datas_escaladas)
    escala_atual = next((e for e in escalas_existentes if e['Data'] == data_escolhida), None)

    if not escala_atual:
        st.warning("Escala não encontrada.")
        return

    st.subheader("🎯 Editar Escala por Função")

    # ---------------- MAPA DA ESCALA ATUAL ----------------
    escala_por_funcao = {}
    for p in escala_atual.get("Escala", []):
        nomes = normalizar_nomes(p.get("Nome"))
        for funcao in p.get("Funcoes", []):
            escala_por_funcao.setdefault(funcao, [])
            escala_por_funcao[funcao].extend(nomes)

    # ---------------- DISPONÍVEIS ----------------
    disponiveis = []
    if not disp_df.empty:
        for r in disp_df.to_dict("records"):
            if r.get("Data") != data_escolhida:
                continue
            nome = r.get("Nome") or r.get("nome")
            dispo = r.get("Disponivel") if "Disponivel" in r else r.get("disponivel")
            if nome and disponibilidade_is_true(dispo):
                disponiveis.append(nome)

    # garantir que quem já estava escalado apareça
    for nomes in escala_por_funcao.values():
        for n in nomes:
            if n not in disponiveis:
                disponiveis.append(n)

    disponiveis = sorted(set(disponiveis))

    ordem_desejada = [
        "Ministração","Sonoplastia","Bateria","Violão","Teclado","Cajon",
        "Soprano","Contralto","Tenor","Baritono","Guitarra","Baixo","Projeção"
    ]
    FUNCOES_ordenadas = [f for f in ordem_desejada if f in FUNCOES]

    escala_escolhidos = {}

    # ---------------- MULTISELECT COM DEFAULT ----------------
    for funcao in FUNCOES_ordenadas:
        habilitados = []
        if not df_funcoes.empty and funcao in df_funcoes.columns:
            habilitados = df_funcoes[df_funcoes[funcao] == "ok"]["Nome"].tolist()

        candidatos = [n for n in disponiveis if n in habilitados] if habilitados else disponiveis

        # Multiselect com default dos nomes já escalados
        selecionados = st.multiselect(
            f"{funcao}:",
            options=candidatos,
            default=escala_por_funcao.get(funcao, []),
            key=f"edit_{funcao}_{data_escolhida}"
        )

        escala_escolhidos[funcao] = selecionados

    # ---------------- PRÉ-VISUALIZAÇÃO ----------------
    st.subheader("📋 Pré-visualização da Edição")
    for funcao, nomes in escala_escolhidos.items():
        st.write(f"{funcao}: {', '.join(nomes) if nomes else '—'}")

    # ---------------- SALVAR ----------------
    if st.button("Salvar Edição"):
        escala_final = []

        for funcao, nomes in escala_escolhidos.items():
            for nome in nomes:
                # Verifica se já existe esse integrante na escala_final
                item = next((x for x in escala_final if x["Nome"] == nome), None)
                if item:
                    if funcao not in item["Funcoes"]:
                        item["Funcoes"].append(funcao)
                else:
                    escala_final.append({"Nome": nome, "Funcoes": [funcao]})

        tipo_culto = datas_df.loc[
            datas_df["Data"] == data_escolhida, "Tipo"
        ].values[0]

        salvar_escala(data_escolhida, tipo_culto, escala_final)

        st.session_state.success_msg_admin = (
            f"✅ Escala de {data_escolhida} atualizada com sucesso!"
        )
        st.rerun()


# ------------------ Escolher Louvores ------------------
def interface_escolher_louvores():
    st.subheader("🎶 Escolher louvores por Data")
    
    # Carregar escalas do banco
    escalas = load_with_spinner(carregar_escala, label="Carregando escalas...")
    if not escalas:
        st.warning("Nenhuma escala criada ainda.")
        return

    hoje = datetime.date.today()
    datas_disponiveis = sorted([
        e['Data'] for e in escalas
        if parse_date_str(e['Data']) and parse_date_str(e['Data']) >= hoje
    ])
    if not datas_disponiveis:
        st.info("Não há datas futuras para escolher louvores.")
        return

    # Seleção da data
    data_selecionada = st.selectbox("Escolha a data:", datas_disponiveis)
    escala = next((e for e in escalas if e['Data'] == data_selecionada), None)
    if not escala:
        st.warning("Escala não encontrada.")
        return

    st.subheader("📋 Escala desta data")

    # --- Pré-visualização da escala ---
    registros = []
    for p in escala.get('Escala', []):
        nomes = normalizar_nomes(p.get("Nome"))
        funcoes = p.get("Funcoes", [])
        if nomes:  # só adiciona se tiver pelo menos um integrante
            registros.append({
                "Nome": ", ".join(nomes),
                "Funcoes": ", ".join([FUNCAO_EMOJI_MAP.get(f.strip(), f.strip()) for f in funcoes])
            })

    if registros:
        escala_df = pd.DataFrame(registros)
        st.table(escala_df)
    else:
        st.info("Nenhum integrante escalado para esta data.")

    # --- Louvores ---
    louvores_cadastrados = load_with_spinner(carregar_louvores_lista, label="Carregando louvores...")
    lista_louvores = [l['louvor'] for l in louvores_cadastrados] if louvores_cadastrados else []

    louvores_selecionados = st.multiselect(
        "Selecione os louvores:",
        options=lista_louvores,
        default=escala.get('louvores', [])
    )

    if st.button("Salvar louvores"):
        atualizar_louvores_escala(data_selecionada, louvores_selecionados)
        st.session_state.success_msg_admin = f"🎶 Louvores de {data_selecionada} salvos com sucesso!"
        st.rerun()

# ===================== NOVA ABA — Visualizar Disponibilidades =====================
def interface_visualizar_disponibilidades():
    st.title("📊 Visualizar Disponibilidades")

    # Carregar dados
    datas = carregar_datas()
    disp = carregar_disponibilidade()
    integrantes = carregar_integrantes()

    if not datas:
        st.warning("Nenhuma data cadastrada.")
        return

    # Converter datas para objetos datetime
    datas_dt = [
        datetime.datetime.strptime(d["Data"], "%d/%m/%Y")
        for d in datas
    ]

    # Descobrir o mês mais recente disponível
    ultima_data = max(datas_dt)
    ultimo_mes = ultima_data.strftime("%m/%Y")

    st.info(f"📅 Exibindo disponibilidades para o mês mais recente: **{ultimo_mes}**")

    # Filtrar datas do último mês
    datas_mes = [
        d["Data"] for d in datas
        if datetime.datetime.strptime(d["Data"], "%d/%m/%Y").strftime("%m/%Y") == ultimo_mes
    ]

    datas_mes = sorted(
        datas_mes,
        key=lambda x: datetime.datetime.strptime(x, "%d/%m/%Y")
    )

    # Lista de integrantes
    lista_integrantes = sorted([
        item.get("Nome") or item.get("nome")
        for item in integrantes
        if item.get("Nome") or item.get("nome")
    ])

    if not lista_integrantes:
        st.warning("Nenhum integrante cadastrado.")
        return

    # Construir tabela
    matriz = []
    disponibilidade_por_integrante = {}

    for nome in lista_integrantes:
        linha = {"Nome": nome}
        disponibilidade_por_integrante[nome] = []

        for data in datas_mes:
            reg = next((x for x in disp if x["Nome"] == nome and x["Data"] == data), None)

            if reg is None:
                linha[data] = "⚪ —"
            else:
                if reg["Disponivel"]:
                    linha[data] = "🟢 Sim"
                    disponibilidade_por_integrante[nome].append(data)
                else:
                    linha[data] = "🔴 Não"

        matriz.append(linha)

    df_disp = pd.DataFrame(matriz)

    # ---- Tabela ----
    st.subheader(f"📅 Tabela de Disponibilidades — {ultimo_mes}")
    st.dataframe(
        df_disp, # Corrigido de df para df_disp
        use_container_width=True, 
        hide_index=True,
        column_config={"Nome": st.column_config.TextColumn("Nome", pinned=True)}
    )

    # =================== PAINEL — Integrantes com 1 data ===================
    st.markdown("---")
    st.subheader("⚠️ Integrantes disponíveis somente em uma data")

    lista_limitados = [
        (nome, disp_list[0])
        for nome, disp_list in disponibilidade_por_integrante.items()
        if len(disp_list) == 1
    ]

    if lista_limitados:
        for nome, unica_data in lista_limitados:
            st.write(f"• **{nome}** — disponível apenas em **{unica_data}**")
    else:
        st.info("Nenhum integrante com disponibilidade limitada neste mês.")

    # =================== PDF ===================
    st.markdown("---")
    st.subheader("📥 Exportar tabela em PDF")

    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=landscape(A4))
    styles = getSampleStyleSheet()

    colunas = df_disp.columns.tolist()
    data_pdf = [colunas]

    for _, row in df_disp.iterrows():
        data_pdf.append([row[col] for col in colunas])

    tabela = Table(data_pdf, colWidths=[80] + [70 for _ in range(len(colunas)-1)])
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightblue),
        ("TEXTCOLOR", (0,0), (-1,0), colors.black),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 8),
    ]))

    elems = [
        Paragraph(f"Disponibilidades — {ultimo_mes}", styles["Title"]),
        tabela
    ]
    doc.build(elems)
    pdf_data = pdf_buffer.getvalue()

    st.download_button(
        label="📄 Baixar PDF",
        data=pdf_data,
        file_name=f"disponibilidades_{ultimo_mes}.pdf",
        mime="application/pdf"
    )


def download_escala_final():
    escalas = load_with_spinner(carregar_escala, label="Carregando escalas...")
    if not escalas:
        st.info("Nenhuma escala salva ainda.")
        return

    # normalizar datas
    for esc in escalas:
        esc['Data_obj'] = parse_date_str(esc['Data'])

    # meses disponíveis (string mm/YYYY)
    meses_disponiveis = sorted({esc['Data_obj'].strftime("%m/%Y") for esc in escalas if esc['Data_obj']})

    if not meses_disponiveis:
        st.info("Nenhuma escala com data válida.")
        return

    mes_atual = datetime.datetime.today().strftime("%m/%Y")
    index_padrao = meses_disponiveis.index(mes_atual) if mes_atual in meses_disponiveis else 0

    mes_escolhido = st.selectbox(
        "📅 Selecione o mês:",
        meses_disponiveis,
        index=index_padrao
    )

    # filtrar escalas do mês escolhido
    escalas_filtradas = [
        e for e in escalas
        if e['Data_obj'] and e['Data_obj'].strftime("%m/%Y") == mes_escolhido
    ]

    escalas_ordenadas = sorted(escalas_filtradas, key=lambda e: e['Data_obj'])

    if not escalas_ordenadas:
        st.info(f"Nenhuma escala encontrada para {mes_escolhido}")
        return

    st.subheader(f"🗓️ Escala Completa - {mes_escolhido}")

    # nomes únicos
    nomes_unicos = sorted({
        p["Nome"] if isinstance(p.get("Nome"), str) else p.get("Nome")[0]
        for esc in escalas_ordenadas
        for p in esc.get("Escala", [])
        if p.get("Nome")
    })

    df_export = pd.DataFrame({"Nome": nomes_unicos})
    df_display = pd.DataFrame({"Nome": nomes_unicos})  # para visualização com emojis

    for esc in escalas_ordenadas:
        col = f"{esc['Data']} - {esc['Tipo']}"
        temp = {}
        for p in esc.get("Escala", []):
            nomes = normalizar_nomes(p.get("Nome"))
            temp.update({n: p.get("Funcoes", []) for n in nomes})

        # versão para export (sem emojis)
        df_export[col] = df_export["Nome"].map(lambda n: ", ".join(temp.get(n, [])))

        # versão para display (com emojis)
        df_display[col] = df_display["Nome"].map(
            lambda n: ", ".join(FUNCAO_EMOJI_MAP.get(f.strip(), f.strip()) for f in temp.get(n, []))
        )

    # mostrar apenas a versão com emojis
    st.dataframe(
        df_display, 
        use_container_width=True, 
        hide_index=True,
        column_config={"Nome": st.column_config.TextColumn("Nome", pinned=True)}
    )

    # --- GERAR EXCEL ---
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
        df_export.to_excel(writer, index=False, sheet_name="Escala")
    st.download_button(
        label="📥 Baixar Excel",
        data=excel_buffer.getvalue(),
        file_name=f"escala_{mes_escolhido}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # --- GERAR PDF ---
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=landscape(A4))
    styles = getSampleStyleSheet()

    colunas = df_export.columns.tolist()
    data_pdf = [colunas]

    for _, row in df_export.iterrows():
        data_pdf.append([row[col] for col in colunas])

    tabela = Table(data_pdf, colWidths=[100] + [80 for _ in range(len(colunas)-1)])
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightblue),
        ("TEXTCOLOR", (0,0), (-1,0), colors.black),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 8),
    ]))

    elems = [Paragraph(f"Escala de Louvor — {mes_escolhido}", styles["Title"]), tabela]
    doc.build(elems)

    st.download_button(
        label="📄 Baixar PDF",
        data=pdf_buffer.getvalue(),
        file_name=f"escala_{mes_escolhido}.pdf",
        mime="application/pdf"
    )
