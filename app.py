import streamlit as st
from data_manager import inicializa_csvs, carregar_funcoes
from session_manager import check_login
from ui_disponibilidade import interface_disponibilidade
from ui_admin import interface_admin
from ui_louvores import interface_integrantes_louvores
from ui_escala_integrantes import interface_escala_do_mes

# Configurações da página (nome da aba, ícone, layout)
st.set_page_config(
    page_title="Escala de Louvor",
    page_icon="🎵",
    layout="wide"
)

def aplicar_estilo():
    st.markdown("""
        <style>
        :root {
            --cor-principal: #115a8a;
        }
        body, .stApp {
            background-color: #f9f9f9;
            font-family: 'Segoe UI', sans-serif;
        }
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
        h1, h2, h3 {
            color: var(--cor-principal);
        }
        details summary {
            color: var(--cor-principal);
            font-weight: 600;
        }
        label.css-18ni7ap {
            margin-left: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

def main():
    aplicar_estilo()
    inicializa_csvs()

    # Carrega funções e integrantes apenas uma vez
    if 'funcoes_carregadas' not in st.session_state:
        df_funcoes, FUNCOES, INTEGRANTES = carregar_funcoes()
        st.session_state['df_funcoes'] = df_funcoes
        st.session_state['funcoes'] = FUNCOES
        st.session_state['integrantes'] = INTEGRANTES
        st.session_state['funcoes_carregadas'] = True

    check_login()

    # Menu lateral
    st.sidebar.title("☰ Menu")
    menu = st.sidebar.radio("Ir para:", ["Integrantes", "Admin"])

    if menu == "Integrantes":
        st.title("👥 Área dos Integrantes")
        tabs = st.tabs(["📆 Disponibilidade", "🎶 Louvores por Escala", "🗓️ Escala do Mês"])

        with tabs[0]:
            interface_disponibilidade()

        with tabs[1]:
            interface_integrantes_louvores()

        with tabs[2]:
            interface_escala_do_mes()

    elif menu == "Admin":
        st.title("🔒 Área do Administrador")
        admin_opcao = st.selectbox("Selecione a opção desejada:", ["Liderança"])

        if admin_opcao == "Liderança":
            interface_admin()


# Executa o app
if __name__ == "__main__":
    main()

# Recarrega a tela se necessário
if st.session_state.get("refresh"):
    st.session_state["refresh"] = False
    st.rerun()



# import streamlit as st
# from data_manager import inicializa_csvs, carregar_funcoes
# from session_manager import check_login
# from ui_disponibilidade import interface_disponibilidade
# from ui_admin import interface_admin
# from ui_louvores import interface_integrantes_louvores

# # Configurações da página (nome da aba, ícone, layout)
# st.set_page_config(
#     page_title="Escala de Louvor",
#     page_icon="🎵",
#     layout="wide"
# )

# def aplicar_estilo():
#     st.markdown("""
#         <style>
#         :root {
#             --cor-principal: #115a8a;
#         }
#         body, .stApp {
#             background-color: #f9f9f9;
#             font-family: 'Segoe UI', sans-serif;
#         }
#         .stButton>button {
#             background-color: var(--cor-principal);
#             color: white;
#             border-radius: 8px;
#             padding: 8px 16px;
#             border: none;
#             transition: background-color 0.3s ease;
#         }
#         .stButton>button:hover {
#             background-color: #0e4e79;
#         }
#         h1, h2, h3 {
#             color: var(--cor-principal);
#         }
#         details summary {
#             color: var(--cor-principal);
#             font-weight: 600;
#         }
#         label.css-18ni7ap {
#             margin-left: 10px;
#         }
#         </style>
#     """, unsafe_allow_html=True)

# def main():
#     aplicar_estilo()
#     inicializa_csvs()

#     # Carrega funções e integrantes apenas uma vez
#     if 'funcoes_carregadas' not in st.session_state:
#         df_funcoes, FUNCOES, INTEGRANTES = carregar_funcoes()
#         st.session_state['df_funcoes'] = df_funcoes
#         st.session_state['funcoes'] = FUNCOES
#         st.session_state['integrantes'] = INTEGRANTES
#         st.session_state['funcoes_carregadas'] = True

#     check_login()

#     # Menu lateral
#     st.sidebar.title("☰ Menu")
#     menu = st.sidebar.radio("Ir para:", ["Integrantes", "Admin"])

#     if menu == "Integrantes":
#         st.title("👥 Área dos Integrantes")
#         tabs = st.tabs(["📆 Disponibilidade", "🎶 Louvores por Escala"])

#         with tabs[0]:
#             interface_disponibilidade()

#         with tabs[1]:
#             interface_integrantes_louvores()

#     elif menu == "Admin":
#         # Se desejar colocar sub-tabs no Admin
#         admin_tabs = st.tabs(["Gerenciar", "Louvores"])

#         with admin_tabs[0]:
#             interface_admin()

#         with admin_tabs[1]:
#             # Importe e chame a interface de louvores no admin
#             from ui_louvores import interface_admin_louvores
#             datas = st.session_state.get('datas_df')['Data'].unique().tolist() if 'datas_df' in st.session_state else []
#             interface_admin_louvores(datas)

# # Executa o app
# if __name__ == "__main__":
#     main()

# # Recarrega a tela se necessário
# if st.session_state.get("refresh"):
#     st.session_state["refresh"] = False
#     st.experimental_rerun()
