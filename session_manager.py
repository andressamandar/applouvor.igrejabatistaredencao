import streamlit as st
import time
# A linha abaixo foi removida, pois a senha não está mais no arquivo config.py
# from config import ADMIN_SENHA 

def check_login():
    if 'admin_logado' not in st.session_state:
        st.session_state['admin_logado'] = False
    if 'admin_login_time' not in st.session_state:
        st.session_state['admin_login_time'] = None

    if st.session_state['admin_logado']:
        if time.time() - st.session_state['admin_login_time'] > 3600:
            st.session_state['admin_logado'] = False
            st.session_state['admin_login_time'] = None
            st.warning("Sessão expirada. Faça login novamente.")

def login_admin(senha):
    # A senha do admin agora é lida diretamente do Streamlit Secrets
    if senha == st.secrets["ADMIN_SENHA"]:
        st.session_state['admin_logado'] = True
        st.session_state['admin_login_time'] = time.time()
        return True
    else:
        return False

# import streamlit as st
# import time
# from config import ADMIN_SENHA

# def check_login():
#     if 'admin_logado' not in st.session_state:
#         st.session_state['admin_logado'] = False
#     if 'admin_login_time' not in st.session_state:
#         st.session_state['admin_login_time'] = None

#     if st.session_state['admin_logado']:
#         if time.time() - st.session_state['admin_login_time'] > 3600:
#             st.session_state['admin_logado'] = False
#             st.session_state['admin_login_time'] = None
#             st.warning("Sessão expirada. Faça login novamente.")

# def login_admin(senha):
#     if senha == ADMIN_SENHA:
#         st.session_state['admin_logado'] = True
#         st.session_state['admin_login_time'] = time.time()
#         return True
#     else:
#         return False
