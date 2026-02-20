import streamlit as st
import time

# ==================== CONSTANTES =====================
SESSION_TIMEOUT = 3600  # 1 hora


# ==================== ADMIN =====================
def init_admin_session():
    if "admin_logado" not in st.session_state:
        st.session_state["admin_logado"] = False
    if "admin_login_time" not in st.session_state:
        st.session_state["admin_login_time"] = None


def check_login():
    """
    Verifica se a sessão do admin ainda é válida.
    Deve ser chamada APENAS na área Admin.
    """
    init_admin_session()

    if st.session_state["admin_logado"]:
        if time.time() - st.session_state["admin_login_time"] > SESSION_TIMEOUT:
            logout_admin()
            st.warning("Sessão expirada. Faça login novamente.")


def login_admin(senha_digitada: str) -> bool:
    senha_admin = st.secrets.get("admin", {}).get("senha")

    if not senha_admin:
        st.error("Senha do admin não configurada em st.secrets.")
        return False

    if senha_digitada == senha_admin:
        st.session_state["admin_logado"] = True
        st.session_state["admin_login_time"] = time.time()
        return True

    return False


def logout_admin():
    st.session_state["admin_logado"] = False
    st.session_state["admin_login_time"] = None


# ==================== MINISTRO =====================
def init_ministro_session():
    if "ministro_logado" not in st.session_state:
        st.session_state["ministro_logado"] = False
    if "ministro_nome" not in st.session_state:
        st.session_state["ministro_nome"] = None
    if "ministro_login_time" not in st.session_state:
        st.session_state["ministro_login_time"] = None


def login_ministro(nome_ministro: str):
    init_ministro_session()
    st.session_state["ministro_logado"] = True
    st.session_state["ministro_nome"] = nome_ministro
    st.session_state["ministro_login_time"] = time.time()


def check_ministro_session():
    """
    Verifica expiração da sessão do ministro.
    """
    init_ministro_session()

    if st.session_state["ministro_logado"]:
        if time.time() - st.session_state["ministro_login_time"] > SESSION_TIMEOUT:
            logout_ministro()
            st.warning("Sessão do ministro expirada.")


def logout_ministro():
    st.session_state["ministro_logado"] = False
    st.session_state["ministro_nome"] = None
    st.session_state["ministro_login_time"] = None