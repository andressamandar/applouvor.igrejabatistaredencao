from datetime import datetime
import streamlit as st
import pandas as pd
from mongo_manager import (
    salvar_disponibilidade,
    carregar_datas,
    carregar_disponibilidade,
    carregar_integrantes,
    carregar_escala
)

def parse_date_str(data_str):
    try:
        return datetime.strptime(data_str, '%d/%m/%Y').date()
    except Exception:
        return None

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
            result = fn(*args, **kwargs) if False else fn(*args)  # keep signature simple
    placeholder.empty()
    return result

def interface_disponibilidade():
    st.title("📅 Disponibilidade")

    if 'success_message_disp' in st.session_state and st.session_state['success_message_disp']:
        st.success(st.session_state['success_message_disp'])
        st.session_state['success_message_disp'] = ""

    integrantes = load_with_spinner(carregar_integrantes, label="Carregando integrantes...")
    nomes = [item['nome'] if 'nome' in item else item.get('Nome') 
             for item in integrantes if 'nome' in item or 'Nome' in item]
    nomes = [n for n in nomes if n is not None]

    if 'selected_integrante_nome_disp' not in st.session_state:
        st.session_state['selected_integrante_nome_disp'] = ""

    try:
        current_index = ([""] + nomes).index(st.session_state['selected_integrante_nome_disp'])
    except ValueError:
        current_index = 0
        st.session_state['selected_integrante_nome_disp'] = ""

    nome = st.selectbox(
        "Selecione seu nome:",
        [""] + nomes,
        key="integrante_nome_selectbox_disp",
        index=current_index
    )
    st.session_state['selected_integrante_nome_disp'] = nome

    if not st.session_state['selected_integrante_nome_disp']:
        st.warning("Selecione seu nome para continuar.")
        return

    # Carrega todas as datas cadastradas (com loader)
    datas = load_with_spinner(carregar_datas, label="Carregando datas...")
    if not datas:
        st.warning("Nenhuma data cadastrada. O administrador precisa adicionar datas.")
        return

    disponibilidade_existente = load_with_spinner(carregar_disponibilidade, label="Carregando disponibilidades...")
    disponiveis_usuario = {
        item["Data"]: item["Disponivel"]
        for item in disponibilidade_existente if item["Nome"] == st.session_state['selected_integrante_nome_disp']
    }

    escalas = load_with_spinner(carregar_escala, label="Carregando escalas...")
    datas_com_escala = {item["Data"] for item in escalas}

    # --- FILTRO: só esconde as datas que já têm escala montada, E esconde datas já passadas ---
    hoje = datetime.today().date()
    datas_filtradas = [
        item for item in datas
        if item["Data"] not in datas_com_escala and parse_date_str(item["Data"]) and parse_date_str(item["Data"]) >= hoje
    ]

    # Ordena cronologicamente
    try:
        datas_filtradas.sort(key=lambda x: datetime.strptime(x['Data'], '%d/%m/%Y'))
    except (ValueError, TypeError):
        st.warning("Erro ao ordenar as datas. Verifique o formato DD/MM/AAAA.")

    datas_do_usuario = set(disponiveis_usuario.keys())
    datas_a_preencher = set([item['Data'] for item in datas_filtradas])

    if datas_a_preencher.issubset(datas_do_usuario) and len(datas_a_preencher) > 0:
        st.warning("Disponibilidade já foi salva. Para alterações verifique com o líder.")
        return

    if not datas_filtradas:
        st.info("Nenhuma data disponível para preencher disponibilidade.")
        return

    st.markdown("---")
    st.markdown("### Desmarque os dias que você NÃO estará disponível:")

    respostas = {}
    for item in datas_filtradas:
        data_str = item['Data']
        tipo = item.get('Tipo', '')
        chave = f"disp_{data_str}_{st.session_state['selected_integrante_nome_disp']}"
        default = disponiveis_usuario.get(data_str, True)
        respostas[data_str] = st.checkbox(f"{data_str} - {tipo}", key=chave, value=default)

    if st.button("Salvar disponibilidade"):
        for data_str, disp in respostas.items():
            salvar_disponibilidade(st.session_state['selected_integrante_nome_disp'], data_str, disp)

        st.session_state['success_message_disp'] = "✅ Disponibilidades salvas com sucesso!"
        st.session_state['selected_integrante_nome_disp'] = ""
        st.rerun()

