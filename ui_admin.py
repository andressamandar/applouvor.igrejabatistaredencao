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
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from reportlab.platypus import LongTable
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import ParagraphStyle

FUNCAO_EMOJI_MAP = {
    "Ministração": "MinistraçãoⓂ️","Soprano": "Soprano🎤","Contralto": "Contralto🎤",
    "Tenor": "Tenor 🎤","Baritono": "Baritono 🎤","Teclado": "Teclado 🎹",
    "Violão": "Violão🎶","Cajon": "Cajon🥁","Bateria": "Bateria🥁", 
    "Guitarra": "Guitarra 🎸", "Baixo": "Baixo 🎸", "Projeção": "Projeção🖥️",
    "Sonoplastia": "Sonoplastia🔊"
}

def trigger_refresh():
    st.session_state['refresh'] = not st.session_state.get('refresh', False)

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
        "Gerenciar Datas", "Criar Escala", "Escolher Louvores","Gerenciar Louvores","Escala e Download"
    ])

    # Carregar dados uma vez
    if 'datas_df' not in st.session_state:
        st.session_state['datas_df'] = pd.DataFrame(carregar_datas())
    if 'disp_df' not in st.session_state:
        st.session_state['disp_df'] = pd.DataFrame(carregar_disponibilidade())
    if 'df_funcoes' not in st.session_state or 'funcoes' not in st.session_state:
        df_funcoes, FUNCOES, INTEGRANTES = carregar_funcoes()
        st.session_state['df_funcoes'] = df_funcoes
        st.session_state['funcoes'] = FUNCOES
        st.session_state['integrantes'] = INTEGRANTES

    if sub_menu == "Gerenciar Datas":
        gerenciar_datas()
    elif sub_menu == "Criar Escala":
        interface_escalar_funcoes()
    elif sub_menu == "Escolher Louvores":
        interface_escolher_louvores()
    elif sub_menu == "Gerenciar Louvores":
         interface_admin_louvores()
    elif sub_menu =="Escala e Download":
        download_escala_final()

def gerenciar_datas():
    datas_df = st.session_state['datas_df']
    st.subheader("Cadastro de Datas de Cultos")
    data_input = st.date_input("Escolha uma data:", min_value=pd.to_datetime('today').date())
    tipo = st.selectbox("Tipo de culto:", ["Ceia", "Quinta", "Domingo", "Outros"])

    if st.button("Adicionar data"):
        data_str = data_input.strftime("%d/%m/%Y")
        salvar_data(data_str, tipo)
        st.success(f"Data adicionada: {data_str} com sucesso!")
        st.session_state['datas_df'] = pd.DataFrame(carregar_datas())
        trigger_refresh()

    st.subheader("Datas cadastradas")
    st.dataframe(datas_df)

    st.subheader("Excluir data")
    if not datas_df.empty:
        data_para_excluir = st.selectbox("Selecione a data a excluir:", datas_df['Data'].unique())
        if st.button("Excluir data selecionada"):
            excluir_data(data_para_excluir)
            st.success(f"Data {data_para_excluir} excluída com sucesso!")
            st.session_state['datas_df'] = pd.DataFrame(carregar_datas())
            trigger_refresh()
    else:
        st.info("Nenhuma data cadastrada.")

def todos_preencheram_disponibilidade(data_escolhida, integrantes, disp_df):
    """
    Verifica se todos os integrantes já preencheram disponibilidade para a data escolhida.
    """
    nomes_integrantes = set(integrantes)
    preenchidos = set(disp_df[disp_df['Data'] == data_escolhida]['Nome'])
    return nomes_integrantes.issubset(preenchidos)


def interface_escalar_funcoes():
    disp_df = st.session_state['disp_df']
    df_funcoes = st.session_state['df_funcoes']
    FUNCOES = st.session_state['funcoes']
    datas_df = st.session_state['datas_df']
    integrantes = st.session_state['integrantes']

    if datas_df.empty:
        st.warning("⚠️ Nenhuma data cadastrada ainda. Adicione datas antes de criar a escala.")
        return

    datas_disponiveis = sorted(disp_df['Data'].unique())
    datas_escaladas = [esc['Data'] for esc in carregar_escala()]
    datas_para_escalar = [d for d in datas_disponiveis if d not in datas_escaladas]

    if not datas_para_escalar:
        st.warning("Todas as datas disponíveis já foram escaladas.")
        return

    data_escolhida = st.selectbox("Escolha a data para escalar:", datas_para_escalar)
    tipo_culto = datas_df.loc[datas_df['Data'] == data_escolhida, 'Tipo'].values[0]

    # 🔹 Status de disponibilidade
    preenchidos = set(disp_df[disp_df['Data'] == data_escolhida]['Nome'])
    faltando = [n for n in integrantes if n not in preenchidos]
    presentes = [n for n in integrantes if n in preenchidos]

    if not faltando:
        st.success("✅ Todos os integrantes já preencheram a disponibilidade!")
    else:
        st.warning("⚠️ Ainda existem integrantes que não preencheram a disponibilidade.")
        with st.expander("📋 Status de Disponibilidade"):
            for n in presentes:
                st.write(f"✅ {n}")
            for n in faltando:
                st.write(f"❌ {n}")

    # 🔹 Escala por função
    st.subheader("🎯 Escalar por Função")
    disponiveis = disp_df[(disp_df['Data'] == data_escolhida) & (disp_df['Disponivel'])]['Nome'].unique()
    if len(disponiveis) == 0:
        st.warning("Ninguém se disponibilizou para esta data ainda.")
        return

    escala_escolhidos = {}
    ja_escalados = []

    for funcao in FUNCOES:
        habilitados = df_funcoes[df_funcoes[funcao] == "ok"]["Nome"].tolist()
        candidatos = [n for n in disponiveis if n in habilitados]

        validos, desabilitados = [], []
        for n in candidatos:
            if funcao != "Ministração" and n in ja_escalados:
                desabilitados.append(n)
            else:
                validos.append(n)

        key_select = f"{funcao}_{data_escolhida}"
        escolhido = st.selectbox(
            f"{funcao}:",
            [""] + validos,
            key=key_select
        )

        if desabilitados:
            st.markdown(", ".join([f"❌ {nome} já escalado em outra função" for nome in desabilitados]))

        if escolhido:
            escala_escolhidos[funcao] = escolhido
            if funcao != "Ministração":
                ja_escalados.append(escolhido)

    if escala_escolhidos:
        st.subheader("📋 Pré-visualização da Escala do Dia")
        for funcao, nome in escala_escolhidos.items():
            st.write(f"{funcao}: {nome}")

        if st.button("Salvar Escala"):
            escala_temp = []
            for funcao, nome in escala_escolhidos.items():
                item = next((p for p in escala_temp if p["Nome"] == nome), None)
                if item:
                    item["Funcoes"].append(funcao)
                else:
                    escala_temp.append({"Nome": nome, "Funcoes": [funcao]})
            salvar_escala(data_escolhida, tipo_culto, escala_temp)
            st.success(f"✅ Escala de {data_escolhida} salva com sucesso!")
            trigger_refresh()

    # 🔹 Pré-visualização da Escala Completa
    escalas = carregar_escala()
    if escalas:
        st.subheader("🗓️ Pré-visualização da Escala Completa")
        Nome = sorted(set(p['Nome'] for esc in escalas for p in esc['Escala']))
        df = pd.DataFrame({"Nome": Nome})
        for esc in escalas:
            col = f"{esc['Data']} - {esc['Tipo']}"
            temp = {p['Nome']: ", ".join(p['Funcoes']) for p in esc['Escala']}
            df[col] = df['Nome'].map(temp).fillna("")

        df_display = df.copy()
        for col in df_display.columns[1:]:
            df_display[col] = df_display[col].apply(
                lambda x: ", ".join([FUNCAO_EMOJI_MAP.get(f.strip(), f.strip()) for f in x.split(',') if f.strip()]) if x else ""
            )

        st.dataframe(df_display, use_container_width=True)


def interface_escolher_louvores():
    st.subheader("🎶 Escolher Louvores por Data")
    escalas = carregar_escala()
    if not escalas:
        st.warning("Nenhuma escala criada ainda.")
        return

    datas_disponiveis = sorted([e['Data'] for e in escalas if not e.get('Louvores')])
    if not datas_disponiveis:
        st.info("Todos os louvores já foram escolhidos para as datas.")
        return

    if st.session_state.get('louvores_salvos'):
        st.success(st.session_state['louvores_salvos'])
        del st.session_state['louvores_salvos']

    data_selecionada = st.selectbox("Escolha a data:", datas_disponiveis)
    escala = next((e for e in escalas if e['Data'] == data_selecionada), None)
    if not escala:
        st.warning("Escala não encontrada para esta data.")
        return

    st.subheader("📋 Escala desta data")
    escala_df = pd.DataFrame([
        {"Nome": p['Nome'], "Funcoes": ", ".join([FUNCAO_EMOJI_MAP.get(f, f) for f in p['Funcoes']])}
        for p in escala['Escala']
    ])
    st.table(escala_df)

    louvores_cadastrados = carregar_louvores_lista()
    lista_louvores = [l['louvor'] for l in louvores_cadastrados]

    louvores_selecionados = st.multiselect(
        "Selecione os louvores para esta data:",
        options=lista_louvores,
        default=escala.get('Louvores', [])
    )

    if st.button("Salvar Louvores"):
        atualizar_louvores_escala(data_selecionada, louvores_selecionados)
        st.session_state['louvores_salvos'] = f"Louvores atualizados para {data_selecionada}!"
        st.rerun()

def download_escala_final():
    escalas = carregar_escala()
    if not escalas:
        st.info("Nenhuma escala salva ainda.")
        return

    # Ordena as escalas por data (dd/mm/yyyy)
    escalas_ordenadas = sorted(
        escalas,
        key=lambda e: datetime.datetime.strptime(e['Data'], "%d/%m/%Y")
    )

    st.subheader("🗓️ Escala Completa")
    nomes_unicos = sorted(set(p['Nome'] for esc in escalas_ordenadas for p in esc['Escala']))
    df = pd.DataFrame({"Nome": nomes_unicos})

    for esc in escalas_ordenadas:
        col = f"{esc['Data']} - {esc['Tipo']}"
        temp = {p['Nome']: ", ".join(p['Funcoes']) for p in esc['Escala']}
        df[col] = df['Nome'].map(temp).fillna("")

    # Exibição com emojis na tela
    df_display = df.copy()
    for col in df_display.columns[1:]:
        df_display[col] = df_display[col].apply(
            lambda x: ", ".join([FUNCAO_EMOJI_MAP.get(f.strip(), f.strip()) for f in x.split(',') if f.strip()]) if x else ""
        )
    st.dataframe(df_display, use_container_width=True)

    # Download Excel
    towrite = io.BytesIO()
    with pd.ExcelWriter(towrite, engine='xlsxwriter') as writer:
        df_display.to_excel(writer, index=False, sheet_name='Escala')
    st.download_button(
        label="📥 Baixar Escala Completa em Excel (.xlsx)",
        data=towrite.getvalue(),
        file_name="escala_completa.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Download CSV
    st.download_button(
        label="📥 Baixar Escala em CSV",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name="escala_completa.csv",
        mime="text/csv"
    )

    # Download PDF
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    style_normal = ParagraphStyle(name='Normal', fontSize=7, leading=12, wordWrap='CJK')
    elements = []

    elements.append(Paragraph("Escala Completa", styles["Title"]))
    elements.append(Paragraph(" ", style_normal))

    # Cabeçalho
    colunas = df.columns.tolist()
    data_table = [colunas]

    # Linhas da tabela
    for _, row in df.iterrows():
        linha = []
        for col in colunas:
            valor = row[col]
            if col != "Nome":
                valor = Paragraph(valor.replace(", ", "<br/>"), style_normal)
            linha.append(valor)
        data_table.append(linha)

    # Largura das colunas
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
        label="📥 Baixar Escala Completa em PDF",
        data=pdf_data,
        file_name="escala_completa.pdf",
        mime="application/pdf"
    )
