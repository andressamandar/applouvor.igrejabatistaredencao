
import streamlit as st
from data_manager import inicializa_csvs, carregar_funcoes
from session_manager import check_login
from ui_disponibilidade import interface_disponibilidade
from ui_admin import interface_admin
from ui_louvores import interface_integrantes_louvores
from ui_escala_integrantes import interface_escala_do_mes

# Configurações da página (nome da aba, ícone, layout)
st.set_page_config(
    page_title="Ministério de Louvor Rendeção",
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
        /* Estilos adicionais para melhorar a estética */
        .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
            font-size: 1rem; /* Aumenta o tamanho da fonte das abas */
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px; /* Espaçamento entre as abas */
        }
        .stTabs [data-baseweb="tab-list"] button {
            background-color: #e0e0e0;
            border-radius: 5px 5px 0 0;
            padding: 10px 15px;
            color: var(--cor-principal);
            font-weight: bold;
        }
        .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
            background-color: var(--cor-principal);
            color: white;
            border-bottom: 3px solid #0a3a5e;
        }
        .stDateInput > label, .stTextInput > label, .stSelectbox > label, .stMultiselect > label {
            font-weight: bold;
            color: var(--cor-principal);
        }
        .stDataFrame {
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
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

    # Adicionando o logo na barra lateral
    st.sidebar.image("logo.png", width=200)  # Ajuste a largura conforme necessário

    # Menu lateral
    st.sidebar.title("☰ Menu")
    menu = st.sidebar.radio("Ir para:", ["Integrantes", "Admin"])

    if menu == "Integrantes":
        st.markdown("<h1 style='color:#115a8a;'>👥 Área dos Integrantes</h1>", unsafe_allow_html=True)
        tabs = st.tabs(["📆 Disponibilidade", "🎶 Louvores por Escala", "🗓️ Escala do Mês"])


        with tabs[0]:
            interface_disponibilidade()

        with tabs[1]:
            interface_integrantes_louvores()

        with tabs[2]:
            interface_escala_do_mes()

    elif menu == "Admin":
        st.markdown("<h1 style='color:#115a8a;'> 🔒 Área do Administrador", unsafe_allow_html=True)
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
