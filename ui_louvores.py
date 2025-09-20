import pandas as pd
import streamlit as st
from mongo_manager import (
    atualizar_louvor_bd,
    carregar_louvores_lista,
    salvar_louvor_bd,
    excluir_louvor,
    carregar_escala
)

def show_round_svg_loader(text="Carregando..."):
    svg = f"""
    <div style="display:flex;align-items:center;gap:10px">
      <div style="width:24px;height:24px">
        <svg width="24" height="24" viewBox="0 0 50 50">
          <circle cx="25" cy="25" r="20" stroke="#115a8a" stroke-width="4" fill="none" stroke-opacity="0.2"/>
          <path d="M25 5 A20 20 0 0 1 45 25" stroke="#115a8a" stroke-width="4" fill="none">
            <animateTransform attributeName="transform" attributeType="XML" type="rotate" from="0 25 25" to="360 25 25" dur="1s" repeatCount="indefinite"/>
          </path>
        </svg>
      </div>
      <div style="font-size:14px;color:#333;">{text}</div>
    </div>
    """
    st.markdown(svg, unsafe_allow_html=True)

def load_with_spinner(fn, *args, label="Carregando..."):
    placeholder = st.empty()
    with placeholder.container():
        with st.spinner(label):
            show_round_svg_loader(label)
            result = fn(*args, **kwargs) if False else fn(*args)
    placeholder.empty()
    return result

def interface_integrantes_louvores():
    st.title("🎶 louvores por Escala")

    st.link_button(
        "📂 Drive",
        "https://drive.google.com/drive/folders/1ME4qbcuD7ZKzhC8OVAcuIfPoLaraooTF"
    )
    st.caption(
        "🔗 Link do DRIVE para acessar **partituras, cifras, mapa vocal, divisão de vozes, planilha tonalidades**"
    )

    escalas = load_with_spinner(carregar_escala, label="Carregando escalas...")
    louvores_cadastrados = load_with_spinner(carregar_louvores_lista, label="Carregando louvores...")

    mapa_louvores = {
        l.get("louvor"): {"link": l.get("link", ""), "tom": l.get("tom", "Não informado")}
        for l in louvores_cadastrados
    }

    if not escalas:
        st.warning("Nenhuma escala salva ainda.")
        return

    st.markdown("### 🎥 Vídeos dos louvores por Data")

    # ordenar e FILTRAR para exibir só datas FUTURAS (ou hoje), exatamente como solicitado
    escalas_ordenadas = sorted(
        [e for e in escalas if _is_future_or_today(e.get("Data"))],
        key=lambda x: pd.to_datetime(x.get("Data", ""), dayfirst=True)
    )

    for esc in escalas_ordenadas:
        data_tipo = f"{esc.get('Data', 'Data não informada')} - {esc.get('Tipo', '')}"
        louvores = esc.get("louvores", [])

        with st.expander(f"**{data_tipo}**"):
            if louvores:
                n_cols = 3
                for i in range(0, len(louvores), n_cols):
                    cols = st.columns(n_cols)
                    for j, l in enumerate(louvores[i:i + n_cols]):
                        col = cols[j]
                        info = mapa_louvores.get(l, {"link": "", "tom": "Não informado"})
                        link = info.get("link")
                        tom = info.get("tom")
                        with col:
                            st.markdown(f"**{l}** — Tom: {tom}")
                            if link:
                                st.video(link, width=250)
                            else:
                                st.markdown("🔗 Link não disponível")
            else:
                st.info("Nenhum louvor cadastrado para esta data.")

# helper fora das funções para checar data (formato dd/mm/YYYY)
def _is_future_or_today(date_str):
    try:
        d = pd.to_datetime(date_str, dayfirst=True).date()
        return d >= pd.Timestamp.now().date()
    except Exception:
        return False

# ------------------------- PARTES DO ADMIN (CRUD de louvores) -------------------------
def interface_admin_louvores():
    st.subheader("🎵 Gerenciar louvores")
    st.info("Aqui você pode adicionar, atualizar ou remover louvores do banco de dados.")

    if 'louvor_selecionado' not in st.session_state:
        st.session_state.louvor_selecionado = ""
    if 'sucesso_msg' not in st.session_state:
        st.session_state.sucesso_msg = ""
    
    louvores = load_with_spinner(carregar_louvores_lista, label="Carregando louvores...")
    louvor_selecionado = st.selectbox(
        "Selecione um louvor para editar/excluir ou deixe em branco para adicionar novo:",
        options=[""] + [l['louvor'] for l in louvores],
        index=0
    )
    
    if st.session_state.sucesso_msg:
        st.success(st.session_state.sucesso_msg)
        st.session_state.sucesso_msg = ""
    
    louvor_nome = ""
    link_youtube = ""
    tom_louvor = ""

    if louvor_selecionado:
        l = next((x for x in louvores if x['louvor'] == louvor_selecionado), {})
        louvor_nome = l.get("louvor", "")
        link_youtube = l.get("link", "")
        tom_louvor = l.get("tom", "")
    
    louvor_nome_input = st.text_input("Nome do Louvor:", value=louvor_nome)
    link_youtube_input = st.text_input("Link do YouTube:", value=link_youtube)
    tom_louvor_input = st.text_input("Qual o tom?:", value=tom_louvor)

    if louvor_selecionado:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Atualizar Louvor"):
                if louvor_nome_input.strip():
                    atualizar_louvor_bd(
                        nome_antigo=louvor_selecionado,
                        novo_nome=louvor_nome_input.strip(),
                        link=link_youtube_input.strip(),
                        tom=tom_louvor_input.strip()
                    )
                    st.session_state.sucesso_msg = f"Louvor '{louvor_nome_input}' atualizado com sucesso!"
                    st.rerun()

        with col2:
            if st.button("🗑️ Excluir Louvor"):
                excluir_louvor(louvor_selecionado)
                st.session_state.sucesso_msg = f"Louvor '{louvor_selecionado}' excluído com sucesso."
                st.rerun()

    else:
        if st.button("💾 Adicionar Louvor"):
            if louvor_nome_input.strip():
                salvar_louvor_bd(louvor_nome_input.strip(), link_youtube_input.strip(), tom_louvor_input.strip())
                st.session_state.sucesso_msg = f"Louvor '{louvor_nome_input}' adicionado com sucesso!"
                st.rerun()
    
    louvores = load_with_spinner(carregar_louvores_lista, label="Atualizando lista de louvores...")
    if louvores:
        st.subheader("louvores Cadastrados")
        df_louvores = pd.DataFrame(louvores)
        st.dataframe(df_louvores, use_container_width=True)

