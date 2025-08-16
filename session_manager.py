import streamlit as st
import time
import os
from dotenv import load_dotenv

# Carrega variáveis do .env local
load_dotenv()

def check_login():
    if 'admin_logado' not in st.session_state:
        st.session_state['admin_logado'] = False
    if 'admin_login_time' not in st.session_state:
        st.session_state['admin_login_time'] = None

    if st.session_state['admin_logado']:
        # Sessão expira após 1 hora
        if time.time() - st.session_state['admin_login_time'] > 3600:
            st.session_state['admin_logado'] = False
            st.session_state['admin_login_time'] = None
            st.warning("Sessão expirada. Faça login novamente.")

def login_admin(senha_digitada):
    """
    Compara a senha digitada com a variável de ambiente ADMIN_PASSWORD.
    """
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
    if not ADMIN_PASSWORD:
        st.error("ERRO: ADMIN_PASSWORD não definida no .env ou no sistema.")
        return False

    if senha_digitada == ADMIN_PASSWORD:
        st.session_state['admin_logado'] = True
        st.session_state['admin_login_time'] = time.time()
        return True
    else:
        return False
