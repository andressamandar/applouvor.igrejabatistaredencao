import streamlit as st
from mongo_manager import carregar_escala, carregar_louvores
import pandas as pd
import io
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from reportlab.platypus import LongTable
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import ParagraphStyle

# Mapa de emojis para as funções
FUNCAO_EMOJI_MAP = {
    "Ministração": "MinistraçãoⓂ️","Soprano": "Soprano🎤","Contralto": "Contralto🎤",
    "Tenor": "Tenor 🎤","Baritono": "Baritono 🎤","Teclado": "Teclado 🎹",
    "Violão": "Violão🎶","Cajon": "Cajon🥁","Bateria": "Bateria🥁", 
    "Guitarra": "Guitarra 🎸", "Baixo": "Baixo 🎸", "Projeção": "Projeção🖥️",
    "Sonoplastia": "Sonoplastia🔊"
}

def exibir_minha_escala():
    """Exibe a escala pessoal do integrante com função e louvores (nome + tom) e permite download."""
    st.title("📅 Minha Escala")
    
    escalas = carregar_escala()
    louvores_com_detalhes = carregar_louvores()

    # Dicionário para buscar tom do louvor
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
                "Louvores": louvores_detalhados
            })

    if not escala_pessoal:
        st.info(f"Você não está escalado(a) neste mês.")
        return

    # --- Exibição na tela igual antes ---
    st.subheader(f"🎤 Escala de {nome_selecionado}")
    for item in escala_pessoal:
        with st.expander(f"**🗓️ {item['Data']} - {item['Tipo']}**"):
            st.markdown(f"**Função:** {item['Funcoes']}")
            if item['Louvores']:
                st.markdown("**Louvores:**")
                for l in item['Louvores']:
                    st.markdown(f"- {l}")
            else:
                st.warning("Nenhum louvor cadastrado para esta data.")

    # --- Preparar tabela para download ---
    df_download = pd.DataFrame([{
        "Data": i["Data"],
        "Tipo": i["Tipo"],
        "Funcoes": i["Funcoes"],
        "Louvores": ", ".join(i["Louvores"])
    } for i in escala_pessoal])
    
            # --- Download PDF ---
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    style_normal = styles["Normal"]
    elements = []

    # Título
    elements.append(Paragraph(f"Escala de {nome_selecionado}", styles["Title"]))
    elements.append(Paragraph(" ", style_normal))  # espaço

    # Cabeçalho da tabela
    data = [["Data", "Tipo", "Funções", "Louvores"]]

    # Linhas da tabela
    for item in escala_pessoal:
        funcoes_sem_emoji = item["Funcoes"]

        # Louvores como Paragraph (quebra automática de linha)
        if item["Louvores"]:
            louvores_formatados = Paragraph("<br/>".join(item["Louvores"]), style_normal)
        else:
            louvores_formatados = Paragraph("—", style_normal)

        data.append([
            item["Data"],
            item["Tipo"],
            funcoes_sem_emoji,
            louvores_formatados
        ])

    # Criar tabela com larguras fixas para equilibrar
    table = Table(data, colWidths=[80, 80, 120, 180])

    # Estilo da tabela
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

    # Gerar PDF
    doc.build(elements)
    pdf_data = pdf_buffer.getvalue()

    st.download_button(
        label="📥 Baixar Minha Escala (PDF)",
        data=pdf_data,
        file_name=f"escala_{nome_selecionado}.pdf",
        mime="application/pdf"
    )

    # --- Download Excel ---
    towrite = io.BytesIO()
    with pd.ExcelWriter(towrite, engine='xlsxwriter') as writer:
        df_download.to_excel(writer, index=False, sheet_name='Minha Escala')
    st.download_button(
        label="📥 Baixar Minha Escala (Excel)",
        data=towrite.getvalue(),
        file_name=f"escala_{nome_selecionado}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # --- Download CSV ---
    st.download_button(
        label="📥 Baixar Minha Escala (CSV)",
        data=df_download.to_csv(index=False).encode('utf-8'),
        file_name=f"escala_{nome_selecionado}.csv",
        mime="text/csv"
    )



def exibir_escala_completa_integrantes():
    st.title("📋 Escala Completa")
    
    escalas = carregar_escala()
    if not escalas:
        st.info("Nenhuma escala salva ainda.")
        return

    nomes_unicos = sorted(list({p['Nome'] for esc in escalas for p in esc['Escala']}))
    
    df = pd.DataFrame({"Nome": nomes_unicos})
    for esc in escalas:
        coluna_nome = f"{esc['Data']} - {esc['Tipo']}"
        dict_funcoes = {p['Nome']: ", ".join(p['Funcoes']) for p in esc['Escala']}
        df[coluna_nome] = df['Nome'].map(dict_funcoes).fillna("")

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
    data = [colunas]

    # Linhas da tabela
    for _, row in df.iterrows():
        linha = []
        for col in colunas:
            valor = row[col]
            if col != "Nome":
                valor = Paragraph(valor.replace(", ", "<br/>"), style_normal)
            linha.append(valor)
        data.append(linha)

    # Largura das colunas
    col_widths = [70] + [90 for _ in range(len(colunas)-1)]

    # Usa LongTable para quebrar em múltiplas páginas
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
        label="📥 Baixar Escala Completa em PDF",
        data=pdf_data,
        file_name="escala_completa.pdf",
        mime="application/pdf"
    )

def interface_integrantes():
    """Função principal que gerencia as abas da interface de integrantes."""
    
    tab1, tab2 = st.tabs(["Minha Escala", "Escala Completa"])

    with tab1:
        exibir_minha_escala()
    
    with tab2:
        exibir_escala_completa_integrantes()



# # Mapa de emojis para as funções
# FUNCAO_EMOJI_MAP = {
#     "Ministração": "MinistraçãoⓂ️","Soprano": "Soprano🎤","Contralto": "Contralto🎤",
#     "Tenor": "Tenor 🎤","Baritono": "Baritono 🎤","Teclado": "Teclado 🎹",
#     "Violão": "Violão🎶","Cajon": "Cajon🥁","Bateria": "Bateria🥁", 
#     "Guitarra": "Guitarra 🎸", "Baixo": "Baixo 🎸", "Projeção": "Projeção🖥️",
#     "Sonoplastia": "Sonoplastia🔊"
# }

# def exibir_minha_escala():
#     """Exibe a escala pessoal do integrante com função e louvores (nome + tom) e permite download."""
#     st.title("📅 Minha Escala")
    
#     escalas = carregar_escala()
#     louvores_com_detalhes = carregar_louvores()

#     # Dicionário para buscar tom do louvor
#     louvor_para_tom = {louvor.get('louvor'): louvor.get('tom') for louvor in louvores_com_detalhes}

#     if not escalas:
#         st.info("Nenhuma escala salva ainda.")
#         return

#     nomes_unicos = sorted({m.get('Nome') for e in escalas for m in e.get('Escala', [])})
#     if not nomes_unicos:
#         st.info("Nenhum integrante encontrado na escala.")
#         return

#     opcoes_nomes = ["Selecione seu nome"] + nomes_unicos
#     nome_selecionado = st.selectbox("Selecione seu nome:", opcoes_nomes, index=0)
#     if nome_selecionado == "Selecione seu nome":
#         st.info("Por favor, selecione seu nome para ver sua escala.")
#         return

#     escala_pessoal = []
#     for escala in escalas:
#         data = escala.get('Data')
#         tipo = escala.get('Tipo')
#         louvores_data = escala.get('louvores', [])

#         participante = next((m for m in escala.get('Escala', []) if m.get('Nome') == nome_selecionado), None)

#         if participante:
#             funcoes = participante.get('Funcoes', [])
#             funcoes_str = ", ".join(funcoes) if funcoes else "Sem função definida"

#             louvores_detalhados = [
#                 f"{l} (Tom: {louvor_para_tom.get(l, 'N/A')})" for l in louvores_data
#             ]

#             escala_pessoal.append({
#                 "Data": data,
#                 "Tipo": tipo,
#                 "Funcoes": funcoes_str,
#                 "Louvores": louvores_detalhados
#             })

#     if not escala_pessoal:
#         st.info(f"Você não está escalado(a) neste mês.")
#         return

#     # --- Exibição na tela igual antes ---
#     st.subheader(f"🎤 Escala de {nome_selecionado}")
#     for item in escala_pessoal:
#         with st.expander(f"**🗓️ {item['Data']} - {item['Tipo']}**"):
#             st.markdown(f"**Função:** {item['Funcoes']}")
#             if item['Louvores']:
#                 st.markdown("**Louvores:**")
#                 for l in item['Louvores']:
#                     st.markdown(f"- {l}")
#             else:
#                 st.warning("Nenhum louvor cadastrado para esta data.")

#     # --- Preparar tabela para download ---
#     df_download = pd.DataFrame([{
#         "Data": i["Data"],
#         "Tipo": i["Tipo"],
#         "Funcoes": i["Funcoes"],
#         "Louvores": ", ".join(i["Louvores"])
#     } for i in escala_pessoal])

#     # --- Download Excel ---
#     towrite = io.BytesIO()
#     with pd.ExcelWriter(towrite, engine='xlsxwriter') as writer:
#         df_download.to_excel(writer, index=False, sheet_name='Minha Escala')
#     st.download_button(
#         label="📥 Baixar Minha Escala (Excel)",
#         data=towrite.getvalue(),
#         file_name=f"escala_{nome_selecionado}.xlsx",
#         mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#     )

#     # --- Download CSV ---
#     st.download_button(
#         label="📥 Baixar Minha Escala (CSV)",
#         data=df_download.to_csv(index=False).encode('utf-8'),
#         file_name=f"escala_{nome_selecionado}.csv",
#         mime="text/csv"
#     )


# def exibir_escala_completa_integrantes():
#     """Exibe a escala completa para todos os integrantes e permite download."""
#     st.title("📋 Escala Completa")
    
#     escalas = carregar_escala()
#     if not escalas:
#         st.info("Nenhuma escala salva ainda.")
#         return

#     nomes_unicos = sorted(list({p['Nome'] for esc in escalas for p in esc['Escala']}))
    
#     # Cria o DataFrame para a escala
#     df = pd.DataFrame({"Nome": nomes_unicos})
#     for esc in escalas:
#         coluna_nome = f"{esc['Data']} - {esc['Tipo']}"
#         dict_funcoes = {p['Nome']: ", ".join(p['Funcoes']) for p in esc['Escala']}
#         df[coluna_nome] = df['Nome'].map(dict_funcoes).fillna("")

#     # Aplica os emojis na exibição
#     df_display = df.copy()
#     for col in df_display.columns[1:]:
#         df_display[col] = df_display[col].apply(
#             lambda x: ", ".join([FUNCAO_EMOJI_MAP.get(f.strip(), f.strip()) for f in x.split(',') if f.strip()]) if x else ""
#         )

#     st.dataframe(df_display, use_container_width=True)

#     # --- Botões de download ---
#     towrite = io.BytesIO()
#     with pd.ExcelWriter(towrite, engine='xlsxwriter') as writer:
#         df_display.to_excel(writer, index=False, sheet_name='Escala')
#     excel_data = towrite.getvalue()

#     st.download_button(
#         label="📥 Baixar Escala Completa em Excel (.xlsx)",
#         data=excel_data,
#         file_name="escala_completa.xlsx",
#         mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#     )


# def interface_integrantes():
#     """Função principal que gerencia as abas da interface de integrantes."""
    
#     tab1, tab2 = st.tabs(["Minha Escala", "Escala Completa"])

#     with tab1:
#         exibir_minha_escala()
    
#     with tab2:
#         exibir_escala_completa_integrantes()