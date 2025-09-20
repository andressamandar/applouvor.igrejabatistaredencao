import streamlit as st
from mongo_manager import carregar_escala, carregar_louvores
import pandas as pd
import io
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, LongTable
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import datetime

FUNCAO_EMOJI_MAP = {
    "Ministração": "MinistraçãoⓂ️","Soprano": "Soprano🎤","Contralto": "Contralto🎤",
    "Tenor": "Tenor 🎤","Baritono": "Baritono 🎤","Teclado": "Teclado 🎹",
    "Violão": "Violão🎶","Cajon": "Cajon🥁","Bateria": "Bateria🥁", 
    "Guitarra": "Guitarra 🎸", "Baixo": "Baixo 🎸", "Projeção": "Projeção🖥️",
    "Sonoplastia": "Sonoplastia🔊"
}

def show_round_svg_loader(text="Carregando..."):
    svg = f"""
    <div style="display:flex;align-items:center;gap:10px">
      <div style="width:24px;height:24px">
        <svg width="24" height="24" viewBox="0 0 50 50">
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

def load_with_spinner(fn, *args, label="Carregando..."):
    placeholder = st.empty()
    with placeholder.container():
        with st.spinner(label):
            show_round_svg_loader(label)
            result = fn(*args, **kwargs) if False else fn(*args)
    placeholder.empty()
    return result

def parse_date_str(data_str):
    try:
        return datetime.datetime.strptime(data_str, "%d/%m/%Y").date()
    except Exception:
        return None

def exibir_minha_escala():
    st.title("📅 Minha Escala")
    
    escalas = load_with_spinner(carregar_escala, label="Carregando sua escala...")
    louvores_com_detalhes = load_with_spinner(carregar_louvores, label="Carregando louvores...")

    louvor_para_tom = {louvor.get('louvor'): louvor.get('tom') for louvor in louvores_com_detalhes}

    if not escalas:
        st.info("Nenhuma escala salva ainda.")
        return

    nomes_unicos = sorted({m.get('Nome') for e in escalas for m in e.get('Escala', [])})
    if not nomes_unicos:
        st.info("Nenhum integrante encontrado na escala.")
        return

    opcoes_nomes = ["Selecione seu nome"] + nomes_unicos
    nome_selecionado = st.selectbox("Selecione seu nome:", opcoes_nomes, index=0)
    if nome_selecionado == "Selecione seu nome":
        st.info("Por favor, selecione seu nome para ver sua escala.")
        return

    escala_pessoal = []
    for escala in escalas:
        data = escala.get('Data')
        tipo = escala.get('Tipo')
        louvores_data = escala.get('louvores', [])

        participante = next((m for m in escala.get('Escala', []) if m.get('Nome') == nome_selecionado), None)

        if participante:
            funcoes = participante.get('Funcoes', [])
            funcoes_str = ", ".join(funcoes) if funcoes else "Sem função definida"

            louvores_detalhados = [
                f"{l} (Tom: {louvor_para_tom.get(l, 'N/A')})" for l in louvores_data
            ]

            escala_pessoal.append({
                "Data": data,
                "Tipo": tipo,
                "Funcoes": funcoes_str,
                "louvores": louvores_detalhados
            })

    if not escala_pessoal:
        st.info(f"Você não está escalado(a) neste mês.")
        return

    # Ordenar por data
    escala_pessoal.sort(key=lambda x: datetime.datetime.strptime(x['Data'], "%d/%m/%Y"))

    # Filtrar apenas datas FUTURAS (ou hoje)
    hoje = datetime.date.today()
    escala_pessoal = [i for i in escala_pessoal if parse_date_str(i['Data']) and parse_date_str(i['Data']) >= hoje]

    if not escala_pessoal:
        st.info("Nenhuma data futura encontrada na sua escala.")
        return

    st.subheader(f"🎤 Escala de {nome_selecionado}")
    for item in escala_pessoal:
        with st.expander(f"**🗓️ {item['Data']} - {item['Tipo']}**"):
            st.markdown(f"**Função:** {item['Funcoes']}")
            if item['louvores']:
                st.markdown("**louvores:**")
                for l in item['louvores']:
                    st.markdown(f"- {l}")
            else:
                st.warning("Nenhum louvor cadastrado para esta data.")

    df_download = pd.DataFrame([{
        "Data": i["Data"],
        "Tipo": i["Tipo"],
        "Funcoes": i["Funcoes"],
        "louvores": ", ".join(i["louvores"])
    } for i in escala_pessoal])

    # PDF / Excel / CSV downloads
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    style_normal = styles["Normal"]
    elements = []

    elements.append(Paragraph(f"Escala de {nome_selecionado}", styles["Title"]))
    elements.append(Paragraph(" ", style_normal))

    data_pdf = [["Data", "Tipo", "Funções", "louvores"]]
    for item in escala_pessoal:
        louvores_formatados = Paragraph("<br/>".join(item["louvores"]), style_normal) if item["louvores"] else Paragraph("—", style_normal)
        data_pdf.append([item["Data"], item["Tipo"], item["Funcoes"], louvores_formatados])

    table = Table(data_pdf, colWidths=[80, 80, 120, 180])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightblue),
        ("TEXTCOLOR", (0,0), (-1,0), colors.black),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("BOTTOMPADDING", (0,0), (-1,0), 6),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
    ]))

    elements.append(table)
    doc.build(elements)
    pdf_data = pdf_buffer.getvalue()

    st.download_button(
        label="📥 Baixar Minha Escala (PDF)",
        data=pdf_data,
        file_name=f"escala_{nome_selecionado}.pdf",
        mime="application/pdf"
    )

    towrite = io.BytesIO()
    with pd.ExcelWriter(towrite, engine='xlsxwriter') as writer:
        df_download.to_excel(writer, index=False, sheet_name='Minha Escala')
    st.download_button(
        label="📥 Baixar Minha Escala (Excel)",
        data=towrite.getvalue(),
        file_name=f"escala_{nome_selecionado}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.download_button(
        label="📥 Baixar Minha Escala (CSV)",
        data=df_download.to_csv(index=False).encode('utf-8'),
        file_name=f"escala_{nome_selecionado}.csv",
        mime="text/csv"
    )

def exibir_escala_completa_integrantes():
    st.title("📋 Escala Completa")
    
    escalas = load_with_spinner(carregar_escala, label="Carregando escalas (completo)...")
    if not escalas:
        st.info("Nenhuma escala salva ainda.")
        return

    # lista de meses (manter histórico)
    meses_disponiveis = sorted({
        datetime.datetime.strptime(e['Data'], "%d/%m/%Y").strftime("%m/%Y")
        for e in escalas
    })
    mes_atual = datetime.datetime.today().strftime("%m/%Y")
    index_padrao = meses_disponiveis.index(mes_atual) if mes_atual in meses_disponiveis else 0
    mes_escolhido = st.selectbox("📅 Selecione o mês:", meses_disponiveis, index=index_padrao)

    escalas_filtradas = [
        e for e in escalas
        if datetime.datetime.strptime(e['Data'], "%d/%m/%Y").strftime("%m/%Y") == mes_escolhido
    ]

    nomes_unicos = sorted(list({p['Nome'] for esc in escalas_filtradas for p in esc['Escala']}))

    escalas_ordenadas = sorted(
        escalas_filtradas,
        key=lambda e: datetime.datetime.strptime(e['Data'], "%d/%m/%Y")
    )

    df = pd.DataFrame({"Nome": nomes_unicos})
    for esc in escalas_ordenadas:
        coluna_nome = f"{esc['Data']} - {esc['Tipo']}"
        dict_funcoes = {p['Nome']: ", ".join(p['Funcoes']) for p in esc['Escala']}
        df[coluna_nome] = df['Nome'].map(dict_funcoes).fillna("")

    df_display = df.copy()
    for col in df_display.columns[1:]:
        df_display[col] = df_display[col].apply(
            lambda x: ", ".join([FUNCAO_EMOJI_MAP.get(f.strip(), f.strip()) for f in x.split(',') if f.strip()]) if x else ""
        )
    st.dataframe(df_display, use_container_width=True)

    # downloads
    towrite = io.BytesIO()
    with pd.ExcelWriter(towrite, engine='xlsxwriter') as writer:
        df_display.to_excel(writer, index=False, sheet_name='Escala')
    st.download_button(
        label="📥 Baixar Escala em Excel (.xlsx)",
        data=towrite.getvalue(),
        file_name=f"escala_{mes_escolhido}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    style_normal = ParagraphStyle(name='Normal', fontSize=7, leading=12, wordWrap='CJK')
    elements = []

    elements.append(Paragraph(f"Escala Completa - {mes_escolhido}", styles["Title"]))
    elements.append(Paragraph(" ", style_normal))

    colunas = df.columns.tolist()
    data = [colunas]

    for _, row in df.iterrows():
        linha = []
        for col in colunas:
            valor = row[col]
            if col != "Nome":
                valor = Paragraph(valor.replace(", ", "<br/>"), style_normal)
            linha.append(valor)
        data.append(linha)

    col_widths = [70] + [90 for _ in range(len(colunas)-1)]

    table = LongTable(data, colWidths=col_widths, repeatRows=1)

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

def interface_integrantes():
    tab1, tab2 = st.tabs(["Minha Escala", "Escala Completa"])

    with tab1:
        exibir_minha_escala()
    
    with tab2:
        exibir_escala_completa_integrantes()
