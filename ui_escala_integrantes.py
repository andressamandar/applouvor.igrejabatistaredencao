import streamlit as st
from mongo_manager import carregar_escala, carregar_louvores
import pandas as pd
import io
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
import datetime

FUNCAO_EMOJI_MAP = {
    "Ministração": "MinistraçãoⓂ️",
    "Soprano": "Soprano🎤",
    "Contralto": "Contralto🎤",
    "Tenor": "Tenor🎤",
    "Baritono": "Baritono🎤",
    "Teclado": "Teclado🎹",
    "Violão": "Violão🎶",
    "Cajon": "Cajon🥁",
    "Bateria": "Bateria🥁",
    "Guitarra": "Guitarra🎸",
    "Baixo": "Baixo🎸",
    "Projeção": "Projeção🖥️",
    "Sonoplastia": "Sonoplastia🔊"
}

# ================== HELPERS ==================
def show_round_svg_loader(text="Carregando..."):
    svg = f"""
    <div style="display:flex;align-items:center;gap:10px">
      <div style="width:24px;height:24px">
        <svg width="24" height="24" viewBox="0 0 50 50">
          <circle cx="25" cy="25" r="20" stroke="#115a8a" stroke-width="4" fill="none" stroke-opacity="0.2"/>
          <path d="M25 5 A20 20 0 0 1 45 25" stroke="#115a8a" stroke-width="4" fill="none">
            <animateTransform attributeName="transform" type="rotate"
                from="0 25 25" to="360 25 25" dur="1s" repeatCount="indefinite"/>
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
            result = fn(*args)
    placeholder.empty()
    return result

def parse_date_str(data_str):
    try:
        return datetime.datetime.strptime(data_str, "%d/%m/%Y").date()
    except Exception:
        return None

def normalizar_nomes(nomes):
    if isinstance(nomes, list):
        return nomes
    if isinstance(nomes, str):
        return [nomes]
    return []




# ================== FUNÇÃO AUXILIAR PARA PDF ==================
def gerar_pdf_escala(df, titulo="Escala"):
    buffer = io.BytesIO()
    # Usamos landscape (deitado) porque escalas costumam ter muitas colunas
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    elements = []
    styles = getSampleStyleSheet()
    
    elements.append(Paragraph(titulo, styles['Title']))
    elements.append(Spacer(1, 12))

    # Converter DataFrame para lista para a tabela do ReportLab
    data = [df.columns.to_list()] + df.values.tolist()
    
    # Ajuste automático de largura de colunas (aproximado)
    num_cols = len(df.columns)
    col_width = (doc.width) / num_cols

    t = Table(data, colWidths=[col_width] * num_cols)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(t)
    doc.build(elements)
    return buffer.getvalue()

# ================== MINHA ESCALA ==================
def exibir_minha_escala():
    st.title("📅 Minha Escala")

    escalas = load_with_spinner(carregar_escala, label="Carregando sua escala...")
    louvores = load_with_spinner(carregar_louvores, label="Carregando louvores...")
    louvor_para_tom = {l["louvor"]: l.get("tom") for l in louvores or []}

    if not escalas:
        st.info("Nenhuma escala salva ainda.")
        return

    nomes_unicos = sorted({
        nome for esc in escalas for p in esc.get("Escala", [])
        for nome in normalizar_nomes(p.get("Nome"))
    })

    nome_selecionado = st.selectbox("Selecione seu nome:", ["Selecione seu nome"] + nomes_unicos)
    if nome_selecionado == "Selecione seu nome": return

    escala_pessoal = []
    for esc in escalas:
        participacoes = [p for p in esc.get("Escala", []) if nome_selecionado in normalizar_nomes(p.get("Nome"))]
        if participacoes:
            funcoes = sorted({f for p in participacoes for f in p.get("Funcoes", [])})
            louvores_data = sorted(set(esc.get("louvores", [])))
            escala_pessoal.append({
                "Data": esc.get("Data"),
                "Tipo": esc.get("Tipo"),
                "Funções": ", ".join(funcoes),
                "Louvores": "\n".join([f"{l} ({louvor_para_tom.get(l, 'N/A')})" for l in louvores_data])
            })

    hoje = datetime.date.today()
    escala_pessoal = [e for e in escala_pessoal if parse_date_str(e["Data"]) and parse_date_str(e["Data"]) >= hoje]

    if not escala_pessoal:
        st.info("Nenhuma data futura encontrada.")
        return

    escala_pessoal.sort(key=lambda x: parse_date_str(x["Data"]))
    
    # Visualização na tela
    for item in escala_pessoal:
        with st.expander(f"🗓️ {item['Data']} - {item['Tipo']}"):
            st.write(f"**Funções:** {item['Funções']}")
            st.write(f"**Louvores:** {item['Louvores']}")

    # --- BOTÃO DOWNLOAD PDF (MINHA ESCALA) ---
    df_pessoal = pd.DataFrame(escala_pessoal)
    pdf_data = gerar_pdf_escala(df_pessoal, titulo=f"Escala Pessoal - {nome_selecionado}")
    st.download_button(
        label="📥 Baixar Minha Escala em PDF",
        data=pdf_data,
        file_name=f"escala_{nome_selecionado.replace(' ', '_')}.pdf",
        mime="application/pdf"
    )

# ================== ESCALA COMPLETA ==================
def exibir_escala_completa_integrantes():
    st.title("📋 Escala Completa")
    escalas = load_with_spinner(carregar_escala, label="Carregando escalas...")
    if not escalas: return

    for esc in escalas:
        esc["Data_obj"] = parse_date_str(esc.get("Data"))

    meses = sorted({e["Data_obj"].strftime("%m/%Y") for e in escalas if e["Data_obj"]})
    mes_atual = datetime.date.today().strftime("%m/%Y")
    index_padrao = meses.index(mes_atual) if mes_atual in meses else 0
    mes = st.selectbox("Selecione o mês:", meses, index=index_padrao)

    escalas_mes = [e for e in escalas if e["Data_obj"] and e["Data_obj"].strftime("%m/%Y") == mes]
    escalas_mes.sort(key=lambda e: e["Data_obj"])

    nomes = sorted({n for e in escalas_mes for p in e.get("Escala", []) for n in normalizar_nomes(p.get("Nome"))})
    df = pd.DataFrame({"Nome": nomes})

    for e in escalas_mes:
        col = f"{e['Data']} - {e['Tipo']}"
        mapa = {}
        for p in e.get("Escala", []):
            funcoes = ", ".join(p.get("Funcoes", []))
            for nome in normalizar_nomes(p.get("Nome")):
                mapa[nome] = f"{mapa.get(nome, '')}, {funcoes}".strip(", ")
        df[col] = df["Nome"].map(mapa).fillna("")

    # Aplicar emojis para visualização na tela
    df_visual = df.copy()
    for col in df_visual.columns[1:]:
        df_visual[col] = df_visual[col].apply(
            lambda x: ", ".join(FUNCAO_EMOJI_MAP.get(f.strip(), f.strip()) for f in x.split(",") if f.strip())
        )

    st.dataframe(df_visual, use_container_width=True, hide_index=True,
                 column_config={"Nome": st.column_config.TextColumn("Nome", pinned=True)})

    # --- BOTÃO DOWNLOAD PDF (ESCALA COMPLETA) ---
    # Geramos o PDF a partir do DF original (sem emojis se preferir algo mais limpo, ou df_visual se quiser emojis)
    pdf_completo = gerar_pdf_escala(df_visual, titulo=f"Escala Geral - {mes}")
    st.download_button(
        label="📥 Baixar Escala Mensal em PDF",
        data=pdf_completo,
        file_name=f"escala_geral_{mes.replace('/', '_')}.pdf",
        mime="application/pdf"
    )

# ================== INTERFACE ==================
def interface_integrantes():
    tab1, tab2 = st.tabs(["Minha Escala", "Escala Completa"])
    with tab1:
        exibir_minha_escala()
    with tab2:
        exibir_escala_completa_integrantes()