import pandas as pd
import streamlit as st
from mongo_manager import (
    atualizar_louvor_bd,
    carregar_louvores_lista,
    salvar_louvor_bd,
    excluir_louvor,
    carregar_escala
)

def interface_integrantes_louvores():
    st.title("🎶 louvores por Escala")

    # --- Botão Drive + descrição ---
    st.link_button(
        "📂 Drive",
        "https://drive.google.com/drive/folders/1ME4qbcuD7ZKzhC8OVAcuIfPoLaraooTF"
    )
    st.caption(
        "🔗 Link do DRIVE para acessar **partituras, cifras, mapa vocal, divisão de vozes, planilha tonalidades**"
    )

    escalas = carregar_escala() or []
    louvores_cadastrados = carregar_louvores_lista() or []

    # Mapa completo: louvor -> {link, tom}
    mapa_louvores = {
        l.get("louvor"): {"link": l.get("link", ""), "tom": l.get("tom", "Não informado")}
        for l in louvores_cadastrados
    }

    if not escalas:
        st.warning("Nenhuma escala salva ainda.")
        return

    st.markdown("### 🎥 Vídeos dos louvores por Data")

    # Ordena escalas por data
    escalas_ordenadas = sorted(
        escalas, key=lambda x: pd.to_datetime(x.get("Data", ""), dayfirst=True)
    )

    for esc in escalas_ordenadas:
        data_tipo = f"{esc.get('Data', 'Data não informada')} - {esc.get('Tipo', '')}"
        louvores = esc.get("louvores", [])

        with st.expander(f"**{data_tipo}**"):
            if louvores:
                # Dividir em linhas de 3 colunas cada (galeria)
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

def interface_integrantes_louvores():
    st.title("🎶 louvores por Escala")

    # --- Botão Drive + descrição ---
    st.link_button(
        "📂 Drive",
        "https://drive.google.com/drive/folders/1ME4qbcuD7ZKzhC8OVAcuIfPoLaraooTF"
    )
    st.caption(
        "🔗 Link do DRIVE para acessar **partituras, cifras, mapa vocal, divisão de vozes, planilha tonalidades**"
    )

    escalas = carregar_escala() or []
    louvores_cadastrados = carregar_louvores_lista() or []

    # Mapa completo: louvor -> {link, tom}
    mapa_louvores = {
        l.get("louvor"): {"link": l.get("link", ""), "tom": l.get("tom", "Não informado")}
        for l in louvores_cadastrados
    }

    if not escalas:
        st.warning("Nenhuma escala salva ainda.")
        return

    st.markdown("### 🎥 Vídeos dos louvores por Data")

    # Ordena escalas por data
    escalas_ordenadas = sorted(
        escalas, key=lambda x: pd.to_datetime(x.get("Data", ""), dayfirst=True)
    )

    for esc in escalas_ordenadas:
        data_tipo = f"{esc.get('Data', 'Data não informada')} - {esc.get('Tipo', '')}"
        louvores = esc.get("louvores", [])

        with st.expander(f"**{data_tipo}**"):
            if louvores:
                # Dividir em linhas de 3 colunas cada (galeria)
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

def interface_integrantes_louvores():
    st.title("🎶 louvores por Escala")

    # --- Botão Drive + descrição ---
    st.link_button(
        "📂 Drive",
        "https://drive.google.com/drive/folders/1ME4qbcuD7ZKzhC8OVAcuIfPoLaraooTF"
    )
    st.caption(
        "🔗 Link do DRIVE para acessar **partituras, cifras, mapa vocal, divisão de vozes, planilha tonalidades**"
    )

    escalas = carregar_escala() or []
    louvores_cadastrados = carregar_louvores_lista() or []

    # Mapa completo: louvor -> {link, tom}
    mapa_louvores = {
        l.get("louvor"): {"link": l.get("link", ""), "tom": l.get("tom", "Não informado")}
        for l in louvores_cadastrados
    }

    if not escalas:
        st.warning("Nenhuma escala salva ainda.")
        return

    st.markdown("### 🎥 Vídeos dos louvores por Data")

    # Ordena escalas por data
    escalas_ordenadas = sorted(
        escalas, key=lambda x: pd.to_datetime(x.get("Data", ""), dayfirst=True)
    )

    for esc in escalas_ordenadas:
        data_tipo = f"{esc.get('Data', 'Data não informada')} - {esc.get('Tipo', '')}"
        louvores = esc.get("louvores", [])

        with st.expander(f"**{data_tipo}**"):
            if louvores:
                # Dividir em linhas de 3 colunas cada (galeria)
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

def interface_admin_louvores():
    st.subheader("🎵 Gerenciar louvores")
    st.info("Aqui você pode adicionar, atualizar ou remover louvores do banco de dados.")

    # Inicializa as chaves do session_state
    if 'louvor_selecionado' not in st.session_state:
        st.session_state.louvor_selecionado = ""
    if 'sucesso_msg' not in st.session_state:
        st.session_state.sucesso_msg = ""
    
    louvores = carregar_louvores_lista() or []

    # Exibe a lista suspensa para seleção
    louvor_selecionado = st.selectbox(
        "Selecione um louvor para editar/excluir ou deixe em branco para adicionar novo:",
        options=[""] + [l['louvor'] for l in louvores],
        index=0
    )
    
    # Exibe a mensagem de sucesso se ela estiver no session_state e depois a limpa
    if st.session_state.sucesso_msg:
        st.success(st.session_state.sucesso_msg)
        st.session_state.sucesso_msg = ""
    
    # Preenche os campos com os dados do louvor selecionado
    louvor_nome = ""
    link_youtube = ""
    tom_louvor = ""

    if louvor_selecionado:
        l = next((x for x in louvores if x['louvor'] == louvor_selecionado), {})
        louvor_nome = l.get("louvor", "")
        link_youtube = l.get("link", "")
        tom_louvor = l.get("tom", "")
    
    # Define os campos de entrada de texto com os valores preenchidos ou vazios
    louvor_nome_input = st.text_input("Nome do Louvor:", value=louvor_nome)
    link_youtube_input = st.text_input("Link do YouTube:", value=link_youtube)
    tom_louvor_input = st.text_input("Qual o tom?:", value=tom_louvor)

    # Define as ações dos botões
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
    
    # Exibir tabela atualizada
    louvores = carregar_louvores_lista() or []
    if louvores:
        st.subheader("louvores Cadastrados")
        df_louvores = pd.DataFrame(louvores)
        st.dataframe(df_louvores, use_container_width=True)