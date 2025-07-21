import streamlit as st
from data_manager import carregar_datas, carregar_disponibilidade, salvar_disponibilidade
import pandas as pd


def aplicar_estilo():
    st.markdown("""
        <style>
        /* Cor principal */
        :root {
            --cor-principal: #115a8a;
        }

        /* Fundo branco e fonte moderna */
        body, .stApp {
            background-color: #f9f9f9;
            font-family: 'Segoe UI', sans-serif;
        }

        /* Botões personalizados */
        .stButton>button {
            background-color: var(--cor-principal);
            color: white;
            border-radius: 8px;
            padding: 8px 16px;
            border: none;
            transition: background-color 0.3s ease;
        }

        .stButton>button:hover {
            background-color: #0e4e79;
        }

        /* Títulos coloridos */
        h1, h2, h3 {
            color: var(--cor-principal);
        }

        /* Expander com cor */
        details summary {
            color: var(--cor-principal);
            font-weight: 600;
        }

        /* Checkboxes com margem */
        label.css-18ni7ap {
            margin-left: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

def interface_disponibilidade():
    aplicar_estilo()  # Chama o estilo global, se ainda não chamou no app principal

    datas_df = carregar_datas()
    disp_df = carregar_disponibilidade()

    
    st.markdown("<h1 style='color:#115a8a;'> Disponibilidade", unsafe_allow_html=True)
    st.markdown("Marque abaixo os dias em que você **NÃO poderá participar**:")


    lista_nomes = ["Selecione seu nome"] + st.session_state.get('integrantes', [])
    nome = st.selectbox("Selecione seu nome:", lista_nomes)

    if nome == "Selecione seu nome":
        st.warning("Por favor, selecione seu nome.")
        return


    # Verifica se já registrou disponibilidade
    if nome and nome in disp_df['Nome'].unique():
        st.warning("Usuário já registrou disponibilidade. Para alterar, fale com o Líder do louvor.")
        return

    disponibilidade_total = st.checkbox("Estou disponível para todos os cultos")

    checkboxes = {}

    if nome:
        if not disponibilidade_total:
            with st.expander("Selecionar dias NÃO DISPONÍVEIS"):
                for i, row in datas_df.iterrows():
                    data = row['Data']
                    key = f"indisp_{data}"
                    checkboxes[data] = st.checkbox(f"❌ Não estarei disponível em {data}", key=key)

        if st.button("Salvar Disponibilidade"):
            for i, row in datas_df.iterrows():
                data = row['Data']
                disponivel = True if disponibilidade_total else not checkboxes.get(data, False)
                nova_linha = {'Nome': nome, 'Data': data, 'Disponivel': disponivel}
                disp_df = pd.concat([disp_df, pd.DataFrame([nova_linha])], ignore_index=True)

            salvar_disponibilidade(disp_df)
            st.success("Disponibilidade registrada com sucesso!")
            st.session_state['refresh'] = not st.session_state.get('refresh', False)
