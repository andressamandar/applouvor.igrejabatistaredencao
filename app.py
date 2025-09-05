import streamlit as st
import os
from mongo_manager import carregar_funcoes
from session_manager import check_login
from ui_disponibilidade import interface_disponibilidade
from ui_louvores import interface_integrantes_louvores
from ui_admin import interface_admin
from ui_escala_integrantes import interface_integrantes

st.set_page_config(
    page_title="Ministério de Louvor Rendeção",
    page_icon="🎵",
    layout="wide"
)

def aplicar_estilo():
    css_file_path = os.path.join(os.path.dirname(__file__), "style.css")
    if os.path.exists(css_file_path):
        with open(css_file_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"Erro: O arquivo CSS '{css_file_path}' não foi encontrado. Verifique o caminho.")

def main():
    aplicar_estilo()
    
    if 'funcoes_carregadas' not in st.session_state:
        df_funcoes, FUNCOES, INTEGRANTES = carregar_funcoes()
        st.session_state['df_funcoes'] = df_funcoes
        st.session_state['funcoes'] = FUNCOES
        st.session_state['integrantes'] = INTEGRANTES
        st.session_state['funcoes_carregadas'] = True

    check_login()

    st.sidebar.image("logo.png", width=200)
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
            interface_integrantes()

    elif menu == "Admin":
        st.markdown("<h1 style='color:#115a8a;'> 🔒 Área do Administrador", unsafe_allow_html=True)
        admin_opcao = st.selectbox("Selecione a opção desejada:", ["Liderança"])

        if admin_opcao == "Liderança":
            interface_admin()

if __name__ == "__main__":
    main()

if st.session_state.get("refresh"):
    st.session_state["refresh"] = False
    st.rerun()