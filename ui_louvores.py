import streamlit as st
import json
import os
import pandas as pd



ARQ_LOUVORES = "louvores.json"


def carregar_louvores():
    st.markdown("<p style='font-size:16px;'>🎼 Acesse o drive para verificar partituras, mapa vocal, divisão de vozes e cifras.</p>", unsafe_allow_html=True)

    st.markdown(
        """
        <a href="https://drive.google.com/drive/u/0/folders/1ME4qbcuD7ZKzhC8OVAcuIfPoLaraooTF" target="_blank">
            <button style='background-color:#115a8a; color:white; padding:10px 20px; border:none; border-radius:8px; cursor:pointer; font-size:16px;'>
                Acessar o Drive 🎵
            </button>
        </a>
        """,
        unsafe_allow_html=True
    )
    

    if os.path.exists(ARQ_LOUVORES):
        with open(ARQ_LOUVORES, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {}



def salvar_louvores(data):
    with open(ARQ_LOUVORES, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        

def interface_admin_louvores(datas):
   
    st.subheader("Gerenciar Louvores por Data")

    louvores = carregar_louvores()

    for data in datas:
        with st.expander(f"Data: {data}", expanded=False):
            if data not in st.session_state:
                st.session_state[data] = louvores.get(data, [])
            links = st.session_state[data]

            for i in range(len(links)):
                links[i] = st.text_input(f"Link do YouTube #{i+1}", value=links[i], key=f"{data}_link_{i}")

            if st.button(f"+ Adicionar louvor para {data}"):
                links.append("")
                st.session_state[data] = links
                st.session_state["refresh"] = True

            if st.button(f"Salvar louvores {data}"):
                links_filtrados = [l.strip() for l in links if l.strip()]
                louvores[data] = links_filtrados
                salvar_louvores(louvores)
                st.success(f"Louvores para {data} salvos com sucesso!")
                if data in st.session_state:
                    del st.session_state[data]
                st.session_state["refresh"] = True

def interface_integrantes_louvores():
    st.markdown("<h1 style='color:#115a8a;'> Louvores por Escala", unsafe_allow_html=True)
    st.markdown("Selecione a data da sua escala e confira quais serão os louvores:")
    
    louvores = carregar_louvores()

    if not louvores:
        st.info("Ainda não há louvores do mês adicionados pela liderança.")
        return

    datas = sorted(louvores.keys(), key=lambda d: pd.to_datetime(d, dayfirst=True))  # Ordena datas

    for data in datas:
        with st.expander(f"Louvores do dia {data}", expanded=False):
            links = louvores.get(data, [])
            if not links:
                st.write("Nenhum vídeo cadastrado para esta data.")
            else:
                for link in links:
                    # Extrai o ID do vídeo do YouTube do link completo
                    video_id = None
                    if "youtube.com/watch?v=" in link:
                        video_id = link.split("v=")[-1].split("&")[0]
                    elif "youtu.be/" in link:
                        video_id = link.split(".be/")[-1].split("?")[0]

                    if video_id:
                        embed_url = f"https://www.youtube.com/embed/{video_id}"
                        html_code = f'''
                        <iframe width="320" height="180" src="{embed_url}" frameborder="0" allowfullscreen></iframe>
                        '''
                        st.markdown(html_code, unsafe_allow_html=True)
                    else:
                        st.write(f"Link inválido ou não suportado: {link}")
