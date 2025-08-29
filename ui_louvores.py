import pandas as pd
import streamlit as st
from mongo_manager import (
    carregar_louvores_lista,
    salvar_louvor_bd,
    excluir_louvor,
    carregar_escala
)

# --- Interface de Administração ---
def interface_admin_louvores():
    st.subheader("🎵 Gerenciar Louvores")
    st.info("Aqui você pode adicionar, editar ou remover louvores do banco de dados.")

    tab_add, tab_view = st.tabs(["Adicionar/Editar Louvor", "Louvores Cadastrados"])

    # --- Aba para adicionar ou atualizar ---
    with tab_add:
        louvor_nome = st.text_input("Nome do Louvor:", key="louvor_nome_input")
        link_youtube = st.text_input("Link do YouTube:", key="link_youtube_input")
        tom_louvor = st.text_input("Qual o tom?", key="tom_louvor_input")

        if st.button("Salvar Louvor"):
            if louvor_nome.strip():
                salvar_louvor_bd(louvor_nome.strip(), link_youtube.strip(), tom_louvor.strip())
                st.success(f"louvor '{louvor_nome}' salvo com sucesso!")
                st.rerun()
            else:
                st.warning("O nome do louvor é obrigatório.")

    # --- Aba para listar e excluir ---
    with tab_view:
        louvores = carregar_louvores_lista() or []
        if louvores:
            df_louvores = pd.DataFrame(louvores)
            st.dataframe(df_louvores, use_container_width=True)

            louvor_para_excluir = st.selectbox(
                "Selecione um louvor para excluir:",
                options=[""] + [l.get("louvor", "") for l in louvores if l.get("louvor")]
            )

            if louvor_para_excluir and st.button("Excluir Louvor"):
                excluir_louvor(louvor_para_excluir)
                st.success(f"louvor '{louvor_para_excluir}' excluído com sucesso.")
                st.rerun()
        else:
            st.info("Nenhum louvor cadastrado ainda.")


def interface_integrantes_louvores():
    st.title("🎶 Louvores por Escala")

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

    st.markdown("### 🎥 Vídeos dos Louvores por Data")

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
    st.info("Aqui você pode adicionar, editar ou remover louvores do banco de dados.")

    tab_add, tab_view = st.tabs(["Adicionar/Editar Louvor", "louvores Cadastrados"])

    with tab_add:
        st.subheader("Adicionar ou Atualizar Louvor")
        louvor_nome = st.text_input("Nome do Louvor:", key="louvor_nome_input")
        link_youtube = st.text_input("Link do YouTube:", key="link_youtube_input")
        tom_louvor = st.text_input("Qual o tom?:", key="tom_louvor_input")

        if st.button("Salvar Louvor"):
            if louvor_nome:
                salvar_louvor_bd(louvor_nome, link_youtube, tom_louvor)
                st.success(f"Louvor '{louvor_nome}' salvo com sucesso!")
                st.rerun()
            else:
                st.warning("O nome do louvor é obrigatório.")

    with tab_view:
        st.subheader("louvores Cadastrados")
        louvores = carregar_louvores_lista()
        if louvores:
            df_louvores = pd.DataFrame(louvores)
            st.dataframe(df_louvores, use_container_width=True)

            louvor_para_excluir = st.selectbox(
                "Selecione um louvor para excluir:",
                options=[""] + [l['louvor'] for l in louvores]
            )

            if louvor_para_excluir and st.button("Excluir Louvor"):
                excluir_louvor(louvor_para_excluir)
                st.success(f"Louvor '{louvor_para_excluir}' excluído com sucesso.")
                st.rerun()
        else:
            st.info("Nenhum louvor cadastrado ainda.")
