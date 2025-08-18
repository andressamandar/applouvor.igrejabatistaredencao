
import streamlit as st
from mongo_manager import salvar_disponibilidade, carregar_datas, carregar_disponibilidade, carregar_integrantes
import pandas as pd

def interface_disponibilidade():
    st.title("📅 Disponibilidade para Cultos")

    # --- NOVO: Exibir mensagem de sucesso persistente após o rerun ---
    if 'success_message_disp' in st.session_state and st.session_state['success_message_disp']:
        st.success(st.session_state['success_message_disp'])
        # Limpa a mensagem para que ela não seja exibida novamente em reruns subsequentes
        st.session_state['success_message_disp'] = ""
    # --- FIM NOVO ---

    integrantes = carregar_integrantes()
    # Adicionado tratamento para o caso de 'Nome' estar com 'n' minúsculo
    nomes = [item['nome'] if 'nome' in item else item.get('Nome') for item in integrantes if 'nome' in item or 'Nome' in item]
    nomes = [n for n in nomes if n is not None] # Remove None entries if any

    # --- INÍCIO DA MUDANÇA PARA RESET DO SELECTBOX (do passo anterior) ---
    # 1. Inicializa a variável de sessão que controlará o selectbox
    if 'selected_integrante_nome_disp' not in st.session_state:
        st.session_state['selected_integrante_nome_disp'] = ""

    # 2. Usa a variável de sessão para definir o valor do selectbox
    #    'index' é usado para definir qual opção está selecionada.
    #    Encontra o índice do valor atual na lista de opções.
    try:
        current_index = ([""] + nomes).index(st.session_state['selected_integrante_nome_disp'])
    except ValueError:
        # Fallback if the name is not found (e.g., deleted from DB), reset to empty
        current_index = 0
        st.session_state['selected_integrante_nome_disp'] = ""

    nome = st.selectbox(
        "Selecione seu nome:",
        [""] + nomes,
        key="integrante_nome_selectbox_disp", # Uma chave única para este selectbox
        index=current_index # Define o valor inicial/atual
    )

    # 3. Atualiza a variável de sessão com o nome selecionado pelo usuário
    #    Isso é importante para que o estado persista através das re-execuções
    st.session_state['selected_integrante_nome_disp'] = nome
    # --- FIM DA MUDANÇA PARA RESET DO SELECTBOX ---

    # Usamos st.session_state['selected_integrante_nome_disp'] para toda a lógica seguinte
    if not st.session_state['selected_integrante_nome_disp']:
        st.warning("Selecione seu nome para continuar.")
        return

    # Carrega as datas disponíveis
    datas = carregar_datas()
    if not datas:
        st.warning("Nenhuma data cadastrada. O administrador precisa adicionar datas.")
        return

    # Carrega disponibilidades anteriores
    disponibilidade_existente = carregar_disponibilidade()
    disponiveis_usuario = {
        item["Data"]: item["Disponivel"]
        for item in disponibilidade_existente if item["Nome"] == st.session_state['selected_integrante_nome_disp']
    }

    st.markdown("---")
    st.markdown("### Marque os dias que você estará disponível:")

    respostas = {}
    for item in datas:
        data_str = item['Data']
        tipo = item.get('Tipo', '')
        # Chave da checkbox deve ser única para cada data E para cada integrante
        chave = f"disp_{data_str}_{st.session_state['selected_integrante_nome_disp']}"
        # Se não houver registro anterior, inicia marcado (True)
        default = disponiveis_usuario.get(data_str, True)
        respostas[data_str] = st.checkbox(f"{data_str} - {tipo}", key=chave, value=default)

    # Verifica se o usuário já tem alguma disponibilidade salva
    # Uma forma mais robusta é verificar se existe *alguma* entrada para este nome, não apenas se foi True.
    disponibilidades_do_usuario = [
        item for item in disponibilidade_existente if item["Nome"] == st.session_state['selected_integrante_nome_disp']
    ]
    ja_salvo_anteriormente = len(disponibilidades_do_usuario) > 0


    if st.button("Salvar disponibilidade"):
        if ja_salvo_anteriormente:
            st.warning("Sua disponibilidade já foi salva para estas datas. Para fazer alterações, por favor, procure o líder de louvor.")
        else:
            for data_str, disp in respostas.items():
                salvar_disponibilidade(st.session_state['selected_integrante_nome_disp'], data_str, disp)
            
            # --- MUDANÇA AQUI: Armazena a mensagem de sucesso na sessão ANTES do rerun ---
            st.session_state['success_message_disp'] = "✅ Disponibilidades salvas com sucesso!"
            # --- FIM MUDANÇA ---
            
            # --- RESET DO SELECTBOX E RERUN (do passo anterior) ---
            st.session_state['selected_integrante_nome_disp'] = ""
            st.rerun() # Força o Streamlit a reexecutar o script
            # --- FIM RESET ---


def todos_preencheram_disponibilidade(data_escolhida, integrantes, disp_df):
    """
    Verifica se todos os integrantes já preencheram disponibilidade para a data escolhida.
    """
    nomes_integrantes = set(integrantes)
    preenchidos = set(disp_df[disp_df['Data'] == data_escolhida]['Nome'])
    return nomes_integrantes.issubset(preenchidos)