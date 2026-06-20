import streamlit as st
import pandas as pd
import datetime
import io

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

from mongo_manager import (
    carregar_escala,
    carregar_escala_midia,
    carregar_funcoes_midia,
    carregar_louvores,
    carregar_tarefas_midia,
    atualizar_status_tarefa_midia,
    assumir_tarefa_midia,
    carregar_integrantes_midia,
    carregar_datas_midia,
    excluir_integrante_midia,
    salvar_disponibilidade_midia,
    carregar_disponibilidade_midia,
    salvar_integrante_midia
)

# ================= UTIL =================
def normalizar_nomes(nomes):
    if isinstance(nomes, list):
        return nomes
    if isinstance(nomes, str):
        return [nomes]
    return []

# ================= INTERFACE =================
def interface_midia_integrantes():

    st.markdown("### 👥 Área dos Integrantes")

    nomes = carregar_integrantes_midia()

    if not nomes:
        st.warning("⚠️ Nenhum integrante cadastrado na mídia.")
        return

    # 🔥 selectbox padrão profissional
    nome = st.selectbox(
        "Selecione seu nome",
        [""] + nomes,
        format_func=lambda x: "Selecione seu nome" if x == "" else x,
        key="global_nome"
    )

    if not nome:
        st.info("👆 Selecione seu nome para continuar")
        return

    tab1, tab2, tab3, tab4 = st.tabs([
        "📆 Disponibilidade",
        "📅 Minha escala",
        "📊 Escala completa",
        "📋 Tarefas"
    ])

    with tab1:
        disponibilidade_midia(nome)

    with tab2:
        minha_escala(nome)

    with tab3:
        escala_completa()

    with tab4:
        tarefas_integrante(nome)

# ================= DISPONIBILIDADE =================
def disponibilidade_midia(nome):
    st.subheader("📆 Minha disponibilidade")

    datas = carregar_datas_midia() or []
    escala_louvor = carregar_escala() or []
    disponibilidades = carregar_disponibilidade_midia() or []

    ja_preenchido = any(d["Nome"] == nome for d in disponibilidades)

    if ja_preenchido:
        st.success("✅ Disponibilidade já salva, caso precise de alterações informar a liderança")

    alteracoes = []

    for d in datas:
        data_str = d["Data"]
        tipo = d.get("Tipo", "")

        
        label = f"{data_str} - {tipo}" if tipo else data_str
     

        bloqueado = any(
            nome in normalizar_nomes(p.get("Nome"))
            for esc in escala_louvor if esc.get("Data") == data_str
            for p in esc.get("Escala", [])
        )

        registro = next(
            (x for x in disponibilidades if x["Nome"] == nome and x["Data"] == data_str),
            None
        )

        disponivel = True if not registro else registro.get("Disponivel", True)

        if ja_preenchido:
            st.checkbox(label, value=disponivel, disabled=True)
            continue

        if bloqueado:
            st.checkbox(f"{label} (Louvor)", value=True, disabled=True)
            alteracoes.append((data_str, False))
        else:
            marcado = st.checkbox(label, value=disponivel)
            alteracoes.append((data_str, marcado))

    if not ja_preenchido:
        if st.button("💾 Salvar disponibilidade", use_container_width=True):
            for data_str, marcado in alteracoes:
                salvar_disponibilidade_midia(nome, data_str, marcado)

            st.success("✅ Disponibilidade salva com sucesso!")
            st.rerun()
            

# ================= MINHA ESCALA =================
def minha_escala(nome):
    st.subheader("📅 Minha escala")

    escala_louvor = carregar_escala() or []
    escala_midia = carregar_escala_midia() or []
    louvores_db = carregar_louvores() or []

    # 🔥 mapa de tom
    louvor_para_tom = {l["louvor"]: l.get("tom", "N/A") for l in louvores_db}

    def parse_data(data_str):
        try:
            return datetime.datetime.strptime(data_str, "%d/%m/%Y")
        except:
            return None

    registros_louvor = []
    registros_midia = []

    # ===== LOUVOR =====
    for esc in escala_louvor:
        for p in esc.get("Escala", []):
            if nome in normalizar_nomes(p.get("Nome")):

                louvores_formatados = "\n".join([
                    f"{l} ({louvor_para_tom.get(l, 'N/A')})"
                    for l in esc.get("louvores", [])
                ])

                registros_louvor.append({
                    "Data": esc.get("Data"),
                    "Data_obj": parse_data(esc.get("Data")),
                    "Funcoes": ", ".join(p.get("Funcoes", [])),
                    "Louvores": louvores_formatados
                })

    # ===== MIDIA =====
    for esc in escala_midia:
        for p in esc.get("Escala", []):
            if nome in normalizar_nomes(p.get("Nome")):
                registros_midia.append({
                    "Data": esc.get("Data"),
                    "Data_obj": parse_data(esc.get("Data")),
                    "Funcoes": ", ".join(p.get("Funcoes", []))
                })

    if not registros_louvor and not registros_midia:
        st.info("Você não está escalado ainda.")
        return

    # ===== FILTRO POR MÊS =====
    todos_registros = registros_louvor + registros_midia

    meses = sorted({
        r["Data_obj"].strftime("%m/%Y")
        for r in todos_registros if r["Data_obj"]
    })

    mes_atual = datetime.datetime.today().strftime("%m/%Y")

    mes = st.selectbox(
        "Selecione o mês",
        meses,
        index=meses.index(mes_atual) if mes_atual in meses else 0
    )

    registros_louvor = [
        r for r in registros_louvor
        if r["Data_obj"] and r["Data_obj"].strftime("%m/%Y") == mes
    ]

    registros_midia = [
        r for r in registros_midia
        if r["Data_obj"] and r["Data_obj"].strftime("%m/%Y") == mes
    ]

    # ===== TELA (NÃO MUDA) =====
    registros_tela = []

    for r in registros_louvor:
        registros_tela.append({
            "Data": r["Data"],
            "Ministerio": "Louvor",
            "Funcoes": r["Funcoes"]
        })

    for r in registros_midia:
        registros_tela.append({
            "Data": r["Data"],
            "Ministerio": "Mídia",
            "Funcoes": r["Funcoes"]
        })

    registros_tela = sorted(registros_tela, key=lambda x: parse_data(x["Data"]))

    df = pd.DataFrame(registros_tela)
    st.dataframe(df, use_container_width=True)

    # ================= PDF =================
    if st.button("📄 Baixar PDF"):

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()

        elementos = []

        # ===== LOUVOR =====
        if registros_louvor:
            dados_louvor = [["Data", "Funções", "Louvores (Tom)"]]

            for r in registros_louvor:
                dados_louvor.append([
                    r["Data"],
                    r["Funcoes"],
                    r["Louvores"]
                ])

            tabela_louvor = Table(dados_louvor)
            tabela_louvor.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.lightblue),
                ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
                ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ]))

            elementos.append(Paragraph(f"Escala de Louvor - {nome} ({mes})", styles["Title"]))
            elementos.append(tabela_louvor)

        # ===== MIDIA =====
        if registros_midia:
            dados_midia = [["Data", "Funções"]]

            for r in registros_midia:
                dados_midia.append([
                    r["Data"],
                    r["Funcoes"]
                ])

            tabela_midia = Table(dados_midia)
            tabela_midia.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.lightgreen),
                ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
                ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ]))

            elementos.append(Paragraph(" ", styles["Normal"]))
            elementos.append(Paragraph(f"Escala de Mídia - {nome} ({mes})", styles["Title"]))
            elementos.append(tabela_midia)

        doc.build(elementos)

        st.download_button(
            "📥 Download PDF",
            data=buffer.getvalue(),
            file_name=f"escala_{nome}_{mes}.pdf",
            mime="application/pdf"
        )
# ================= ESCALA COMPLETA =================
def escala_completa():
    st.subheader("📊 Escala completa")

    escalas = carregar_escala_midia() or []

    if not escalas:
        st.info("Nenhuma escala cadastrada.")
        return

    nomes = sorted({
        nome
        for e in escalas
        for p in e.get("Escala", [])
        for nome in normalizar_nomes(p.get("Nome"))
    })

    df = pd.DataFrame({"Nome": nomes})

    for e in escalas:
        tipo = e.get("Tipo") or e.get("tipo") or ""
        data = e.get("Data")

        col = f"{tipo} - {data}" if tipo else data

        mapa = {}

        for p in e.get("Escala", []):
            for nome in normalizar_nomes(p.get("Nome")):
                mapa[nome] = ", ".join(p.get("Funcoes", []))

        df[col] = df["Nome"].map(mapa).fillna("")

    # 🔥 FIXAR NOME
    df_exibicao = df.set_index("Nome")
    st.dataframe(df_exibicao, use_container_width=True)

    # ================= PDF DIRETO =================
    from reportlab.lib.pagesizes import A4, landscape

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))

    styles = getSampleStyleSheet()
    elementos = []

    elementos.append(Paragraph("Escala Completa - Mídia", styles["Title"]))

    df_pdf = df.copy().astype(str)
    dados = [df_pdf.columns.tolist()] + df_pdf.values.tolist()

    total_colunas = len(df_pdf.columns)
    largura_total = 800
    col_widths = [largura_total / total_colunas] * total_colunas

    tabela = Table(dados, colWidths=col_widths, repeatRows=1)

    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("FONTSIZE", (0,0), (-1,-1), 7),
        ("LEFTPADDING", (0,0), (-1,-1), 4),
        ("RIGHTPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING", (0,0), (-1,-1), 2),
        ("BOTTOMPADDING", (0,0), (-1,-1), 2),
    ]))

    elementos.append(tabela)

    doc.build(elementos)

    # 🔥 BOTÃO ÚNICO
    st.download_button(
        "📄 Baixar escala completa (PDF)",
        data=buffer.getvalue(),
        file_name="escala_completa_midia.pdf",
        mime="application/pdf",
        use_container_width=True
    )
# ================= TAREFAS =================
def tarefas_integrante(nome):
    st.subheader("📋 Tarefas")

    tarefas = carregar_tarefas_midia() or []

    tarefas_disponiveis = []
    tarefas_andamento = []

    for t in tarefas:
        titulo = t.get("titulo")
        status = t.get("status", "A Fazer")
        responsavel = t.get("responsavel")

        # ❌ IGNORA CONCLUÍDAS
        if status == "Concluído":
            continue

        if responsavel:
            tarefas_andamento.append(t)
        else:
            tarefas_disponiveis.append(t)

    # ================= DISPONÍVEIS =================
    st.markdown("### Tarefas disponíveis")

    if not tarefas_disponiveis:
        st.info("Nenhuma tarefa disponível")
    else:
        for t in tarefas_disponiveis:
            titulo = t.get("titulo")

            col1, col2 = st.columns([4, 1])

            with col1:
                with st.expander(f"📋 {titulo}"):

                    st.write(
                        f"**Ministério:** {t.get('ministerio','')}"
                    )

                    st.write(
                        f"**Solicitante:** {t.get('solicitante','')}"
                    )

                    st.write(
                        f"**Descrição:** {t.get('descricao','')}"
                    )
                    
                    tamanhos = t.get("tamanhos", [])

                    if tamanhos:
                        st.write(
                            f"**Formatos solicitados:** {', '.join(tamanhos)}"
                        )
                    else:
                        st.write(
                            "**Formatos solicitados:** Não informado"
                        )

                    st.write(
                        f"**Sugestão:** {t.get('sugestao','')}"
                    )

                    st.write(
                        f"**Data do Evento:** {t.get('data_evento','')}"
                    )

                    st.write(
                        f"**Horário:** {t.get('horario','')}"
                    )

                    st.write(
                        f"**Data de Entrega:** {t.get('data_entrega','')}"
                    )

                    if st.button(
                        "Assumir",
                        key=f"{titulo}_assumir"
                    ):
                        assumir_tarefa_midia(
                            titulo,
                            nome
                        )
                        st.rerun()

    # ================= EM ANDAMENTO =================
    st.markdown("### Tarefas em andamento")

    if not tarefas_andamento:
        st.info("Nenhuma tarefa em andamento")
    else:
        for t in tarefas_andamento:
            titulo = t.get("titulo")
            responsavel = t.get("responsavel")

            col1, col2 = st.columns([4, 1])

            with col1:
                st.write(f"**{titulo}**")
                st.caption(f"👤 {responsavel}")

            with col2:
                if responsavel == nome:
                    if st.button("Concluir", key=f"{titulo}_done"):
                        atualizar_status_tarefa_midia(titulo, "Concluído")
                        st.rerun()