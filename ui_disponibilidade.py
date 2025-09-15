import streamlit as st
import pandas as pd
from mongo_manager import (
    salvar_disponibilidade,
    carregar_datas,
    carregar_disponibilidade,
    carregar_integrantes,
    carregar_escala
)

def interface_disponibilidade():
    st.title("📅 Disponibilidade")

    # --- Mensagem de sucesso persistente após o rerun ---
    if 'success_message_disp' in st.session_state and st.session_state['success_message_disp']:
        st.success(st.session_state['success_message_disp'])
        st.session_state['success_message_disp'] = ""
    # -----------------------------------------------------

    integrantes = carregar_integrantes()
    nomes = [item['nome'] if 'nome' in item else item.get('Nome') 
             for item in integrantes if 'nome' in item or 'Nome' in item]
    nomes = [n for n in nomes if n is not None]

    # Controle do selectbox de integrante
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

    # Carrega todas as datas cadastradas
    datas = carregar_datas()
    if not datas:
        st.warning("Nenhuma data cadastrada. O administrador precisa adicionar datas.")
        return

    # Carrega disponibilidades anteriores do integrante
    disponibilidade_existente = carregar_disponibilidade()
    disponiveis_usuario = {
        item["Data"]: item["Disponivel"]
        for item in disponibilidade_existente if item["Nome"] == st.session_state['selected_integrante_nome_disp']
    }

    # Carrega escalas já montadas
    escalas = carregar_escala() or []

    # Pega todas as datas que já estão na collection escala
    datas_com_escala = set()
    for e in escalas:
        if "Data" in e:   # segurança contra docs diferentes
            datas_com_escala.add(e["Data"])

    # --- FILTRO: remove datas que já estão na escala ---
    datas_filtradas = [item for item in datas if item["Data"] not in datas_com_escala]
    # ---------------------------------------------------

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
        default = disponiveis_usuario.get(data_str, True)  # mantém se já tiver marcado antes
        respostas[data_str] = st.checkbox(f"{data_str} - {tipo}", key=chave, value=default)

    if st.button("Salvar disponibilidade"):
        for data_str, disp in respostas.items():
            salvar_disponibilidade(st.session_state['selected_integrante_nome_disp'], data_str, disp)

        st.session_state['success_message_disp'] = "✅ Disponibilidades salvas com sucesso!"
        st.session_state['selected_integrante_nome_disp'] = ""
        st.rerun()
