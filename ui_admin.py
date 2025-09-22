import datetime
import io
from mongo_manager import (
    carregar_louvores_lista, carregar_datas, salvar_data, excluir_data,
    carregar_disponibilidade, carregar_funcoes, salvar_escala, carregar_escala, atualizar_louvores_escala
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
        "Gerenciar datas", "Criar escala", "Editar escala", "Escolher louvores","Gerenciar louvores","Escala e Download"
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

    ordem_desejada = ["Ministração","Bateria","Violão","Teclado","Sonoplastia","Cajon","Soprano", "Contralto", "Tenor", 
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
        with st.expander("📋 Status de Disponibilidade"):
            if presentes:
                for n in presentes:
                    st.write(f"✅ {n}")
            else:
                st.write("— Nenhum integrante marcou disponibilidade ainda —")
            if faltando:
                for n in faltando:
                    st.write(f"❌ {n}")

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

    escala_escolhidos = {}

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

        key_select = f"{funcao}_{data_escolhida}"
        escolhido_raw = st.selectbox(f"{funcao}:", opcoes, key=key_select)

        # Remove aviso
        escolhido = escolhido_raw.replace("(escalado em Ministração)", "").strip() if escolhido_raw else ""

        if escolhido:
            escala_escolhidos[funcao] = escolhido
            # Remove dos disponíveis apenas se não for Ministração
            if funcao != "Ministração" and escolhido in disponiveis:
                disponiveis.remove(escolhido)

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
            st.success(f"✅ Escala de {data_escolhida} salva com sucesso!")
            trigger_refresh()


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

    hoje = datetime.date.today()
    datas_escaladas = sorted([esc['Data'] for esc in escalas_existentes if parse_date_str(esc['Data']) and parse_date_str(esc['Data']) >= hoje])
    if not datas_escaladas:
        st.info("Não há escalas futuras para editar.")
        return

    data_escolhida = st.selectbox("Escolha a data para editar a escala:", datas_escaladas)
    escala_atual = next((e for e in escalas_existentes if e['Data'] == data_escolhida), None)
    if not escala_atual:
        st.warning("Escala não encontrada para esta data.")
        return

    st.subheader("🎯 Editar Escala por Função")

    # Disponíveis
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

    # Adiciona os integrantes já escalados na lista de disponíveis
    for p in escala_atual.get('Escala', []):
        if p['Nome'] not in disponiveis:
            disponiveis.append(p['Nome'])

    ordem_desejada = ["Ministração", "Soprano", "Contralto", "Tenor","Baritono", "Violão",
                      "Teclado", "Bateria", "Cajon", "Guitarra", "Baixo", "Projeção", "Sonoplastia"]
    FUNCOES_ordenadas = [f for f in ordem_desejada if f in FUNCOES]

    escala_escolhidos = {}

    for funcao in FUNCOES_ordenadas:
        # Integrante já escalado para essa função
        integrante_na_escala = next((p['Nome'] for p in escala_atual['Escala'] if funcao in p['Funcoes']), "")

        habilitados = []
        if not df_funcoes.empty and funcao in df_funcoes.columns:
            try:
                habilitados = df_funcoes[df_funcoes[funcao] == "ok"]['Nome'].tolist()
            except Exception:
                habilitados = [r.get('Nome') or r.get('nome') for r in df_funcoes.to_dict('records') if r.get(funcao) == "ok"]

        candidatos = [n for n in disponiveis if n in habilitados] if habilitados else list(disponiveis)
        if integrante_na_escala and integrante_na_escala not in candidatos:
            candidatos.append(integrante_na_escala)

        # Opções de selectbox com aviso de "já escalado", exceto Ministração
        opcoes = [""]
        for n in candidatos:
            if funcao != "Ministração" and n in escala_escolhidos.values():
                opcoes.append(f"{n} (escalado em Ministração)")
            else:
                opcoes.append(n)

        default_index = 0
        if integrante_na_escala:
            escolha_default = integrante_na_escala
            if escolha_default not in opcoes:
                escolha_default = ""
            default_index = opcoes.index(escolha_default)

        key_select = f"editar_{funcao}_{data_escolhida}"
        escolhido_raw = st.selectbox(f"{funcao}:", opcoes, key=key_select, index=default_index)

        # Remove aviso
        escolhido = escolhido_raw.replace("(escalado em Ministração)", "").strip() if escolhido_raw else ""

        if escolhido:
            escala_escolhidos[funcao] = escolhido
            # Remove dos disponíveis apenas se não for Ministração
            if funcao != "Ministração" and escolhido in disponiveis:
                disponiveis.remove(escolhido)

    # Pré-visualização
    if escala_escolhidos:
        st.subheader("📋 Pré-visualização da Edição")
        for funcao, nome in escala_escolhidos.items():
            st.write(f"{funcao}: {nome}")

        # Salvar edição
        if st.button("Salvar Edição"):
            escala_temp = []
            for funcao, nome in escala_escolhidos.items():
                item = next((p for p in escala_temp if p["Nome"] == nome), None)
                if item:
                    if funcao not in item["Funcoes"]:
                        item["Funcoes"].append(funcao)
                else:
                    escala_temp.append({"Nome": nome, "Funcoes": [funcao]})
            tipo_culto = datas_df.loc[datas_df['Data'] == data_escolhida, 'Tipo'].values[0]
            salvar_escala(data_escolhida, tipo_culto, escala_temp)
            st.success(f"✅ Escala de {data_escolhida} atualizada!")
            st.rerun()


# ------------------ Escolher Louvores ------------------
def interface_escolher_louvores():
    st.subheader("🎶 Escolher louvores por Data")
    escalas = load_with_spinner(carregar_escala, label="Carregando escalas...")
    if not escalas:
        st.warning("Nenhuma escala criada ainda.")
        return

    hoje = datetime.date.today()
    datas_disponiveis = sorted([e['Data'] for e in escalas if parse_date_str(e['Data']) and parse_date_str(e['Data']) >= hoje])
    if not datas_disponiveis:
        st.info("Não há datas futuras para escolher louvores.")
        return

    data_selecionada = st.selectbox("Escolha a data:", datas_disponiveis)
    escala = next((e for e in escalas if e['Data'] == data_selecionada), None)
    if not escala:
        st.warning("Escala não encontrada.")
        return

    st.subheader("📋 Escala desta data")
    escala_df = pd.DataFrame([
        {"Nome": p['Nome'], "Funcoes": ", ".join([FUNCAO_EMOJI_MAP.get(f, f) for f in p['Funcoes']])}
        for p in escala['Escala']
    ])
    st.table(escala_df)

    louvores_cadastrados = load_with_spinner(carregar_louvores_lista, label="Carregando louvores...")
    lista_louvores = [l['louvor'] for l in louvores_cadastrados] if louvores_cadastrados else []

    louvores_selecionados = st.multiselect("Selecione os louvores:", options=lista_louvores, default=escala.get('louvores', []))

    if st.button("Salvar louvores"):
        atualizar_louvores_escala(data_selecionada, louvores_selecionados)
        st.success(f"Louvores atualizados para {data_selecionada}!")
        st.rerun()

# ------------------ Escala Completa + Download ------------------
def download_escala_final():
    escalas = load_with_spinner(carregar_escala, label="Carregando escalas...")
    if not escalas:
        st.info("Nenhuma escala salva ainda.")
        return

    meses_disponiveis = sorted({datetime.datetime.strptime(e['Data'], "%d/%m/%Y").strftime("%m/%Y") for e in escalas})
    mes_atual = datetime.datetime.today().strftime("%m/%Y")
    index_padrao = meses_disponiveis.index(mes_atual) if mes_atual in meses_disponiveis else 0
    mes_escolhido = st.selectbox("📅 Selecione o mês:", meses_disponiveis, index=index_padrao)

    escalas_filtradas = [e for e in escalas if datetime.datetime.strptime(e['Data'], "%d/%m/%Y").strftime("%m/%Y") == mes_escolhido]
    escalas_ordenadas = sorted(escalas_filtradas, key=lambda e: datetime.datetime.strptime(e['Data'], "%d/%m/%Y"))

    st.subheader(f"🗓️ Escala Completa - {mes_escolhido}")
    nomes_unicos = sorted(set(p['Nome'] for esc in escalas_ordenadas for p in esc['Escala']))
    df = pd.DataFrame({"Nome": nomes_unicos})
    for esc in escalas_ordenadas:
        col = f"{esc['Data']} - {esc['Tipo']}"
        temp = {p['Nome']: ", ".join(p['Funcoes']) for p in esc['Escala']}
        df[col] = df['Nome'].map(temp).fillna("")

    df_display = df.copy()
    for col in df_display.columns[1:]:
        df_display[col] = df_display[col].apply(
            lambda x: ", ".join([
                FUNCAO_EMOJI_MAP.get(f.strip(), f.strip())
                for f in x.split(',') if f.strip()
            ]) if x else ""
        )
    st.dataframe(df_display, use_container_width=True)

    # --- Download Excel ---
    towrite = io.BytesIO()
    with pd.ExcelWriter(towrite, engine='xlsxwriter') as writer:
        df_display.to_excel(writer, index=False, sheet_name='Escala')
    st.download_button(
        label="📥 Baixar Escala em Excel (.xlsx)",
        data=towrite.getvalue(),
        file_name=f"escala_{mes_escolhido}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # --- Download CSV ---
    st.download_button(
        label="📥 Baixar Escala em CSV",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name=f"escala_{mes_escolhido}.csv",
        mime="text/csv"
    )

    # --- Download PDF ---
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    style_normal = ParagraphStyle(name='Normal', fontSize=7, leading=12, wordWrap='CJK')
    elements = []

    elements.append(Paragraph(f"Escala Completa - {mes_escolhido}", styles["Title"]))
    elements.append(Paragraph(" ", style_normal))

    colunas = df.columns.tolist()
    data_table = [colunas]

    for _, row in df.iterrows():
        linha = []
        for col in colunas:
            valor = row[col]
            if col != "Nome":
                valor = Paragraph(valor.replace(", ", "<br/>"), style_normal)
            linha.append(valor)
        data_table.append(linha)

    col_widths = [70] + [90 for _ in range(len(colunas)-1)]

    table = LongTable(data_table, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightblue),
        ("TEXTCOLOR", (0,0), (-1,0), colors.black),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("BOTTOMPADDING", (0,0), (-1,0), 6),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
    ]))

    elements.append(table)
    doc.build(elements)
    pdf_data = pdf_buffer.getvalue()

    st.download_button(
        label="📥 Baixar Escala em PDF",
        data=pdf_data,
        file_name=f"escala_{mes_escolhido}.pdf",
        mime="application/pdf"
    )
