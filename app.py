import streamlit as st
import os

from mongo_manager import carregar_funcoes
from session_manager import check_login

from ui_disponibilidade import interface_disponibilidade
from ui_louvores import interface_integrantes_louvores
from ui_admin import interface_admin
from ui_escala_integrantes import interface_integrantes
from ui_ministro import interface_ministro
import textwrap


# ==================== CONFIG STREAMLIT =====================
st.set_page_config(
    page_title="Ministério de Louvor Redenção",
    page_icon="🎵",
    layout="wide"
)


# ==================== ESTILO =====================
def aplicar_estilo():
    css_file_path = os.path.join(os.path.dirname(__file__), "style.css")
    if os.path.exists(css_file_path):
        with open(css_file_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# ==================== PÁGINA INICIAL =====================

def pagina_inicial():
    st.markdown("<h1 style='text-align:center;'>Igreja Batista Redenção</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center;'>Portal de Escalas</p>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='text-align:center;'>Selecione o Ministério que deseja acessar:</p>",
        unsafe_allow_html=True
    )

    st.write("")  # pequeno espaçamento
    st.write("")

    # Cria colunas para centralizar
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if st.button("🎶 Ministério de Louvor", use_container_width=True):
            st.session_state["modulo"] = "louvor"
            st.rerun()

        st.write("")  # espaço entre botões

        if st.button("📹 Ministério de Mídia", use_container_width=True):
            st.session_state["modulo"] = "midia"
            st.rerun()
# ==================== APP =====================
def main():
    aplicar_estilo()

    # Estado inicial
    if "modulo" not in st.session_state:
        st.session_state["modulo"] = "home"

    # ==================== HOME =====================
    if st.session_state["modulo"] == "home":
        pagina_inicial()
        return

    # ==================== MÍDIA =====================
    if st.session_state["modulo"] == "midia":
        st.markdown("## 📹 Ministério de Mídia")
        st.info("🚧 Página em construção")

        if st.button("⬅ Voltar para o início"):
            st.session_state["modulo"] = "home"
            st.rerun()
        return

    # ==================== MINISTÉRIO DE LOUVOR =====================
    if st.session_state["modulo"] == "louvor":

        # Cache de funções / integrantes
        if "funcoes_carregadas" not in st.session_state:
            df_funcoes, FUNCOES, INTEGRANTES = carregar_funcoes()
            st.session_state["df_funcoes"] = df_funcoes
            st.session_state["funcoes"] = FUNCOES
            st.session_state["integrantes"] = INTEGRANTES
            st.session_state["funcoes_carregadas"] = True

        if st.button("⬅ Voltar para o início"):
            st.session_state["modulo"] = "home"
            st.rerun()

        # Sidebar
        if os.path.exists("logo.png"):
            st.sidebar.image("logo.png", width=200)

        st.sidebar.title("☰ Menu")

        menu = st.sidebar.radio(
            "Ir para:",
            ["Integrantes", "Ministro", "Admin"]
        )

        # ==================== FLUXO ATUAL (INALTERADO) =====================
        if menu == "Integrantes":
            st.markdown(
                "<h1 style='color:#115a8a;'>👥 Área dos Integrantes</h1>",
                unsafe_allow_html=True
            )

            tabs = st.tabs(
                ["📆 Disponibilidade", "🎶 Louvores por Escala", "🗓️ Escala do Mês"]
            )

            with tabs[0]:
                interface_disponibilidade()

            with tabs[1]:
                interface_integrantes_louvores()

            with tabs[2]:
                interface_integrantes()

        elif menu == "Ministro":
            interface_ministro()

        elif menu == "Admin":
            check_login()

            st.markdown(
                "<h1 style='color:#115a8a;'>🔒 Área do Administrador</h1>",
                unsafe_allow_html=True
            )

            admin_opcao = st.selectbox(
                "Selecione a opção desejada:",
                ["Liderança"]
            )

            if admin_opcao == "Liderança":
                interface_admin()


# ==================== EXECUÇÃO =====================
if __name__ == "__main__":
    main()

# Refresh controlado
if st.session_state.get("refresh"):
    st.session_state["refresh"] = False
    st.rerun()