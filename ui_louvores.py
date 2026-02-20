import pandas as pd
import streamlit as st

from mongo_manager import (
    carregar_louvores_lista,
    salvar_louvor_bd,
    atualizar_louvor_bd,
    excluir_louvor,
    carregar_escala
)

# ==================== LOADER ====================
def show_round_svg_loader(text="Carregando..."):
    svg = f"""
    <div style="display:flex;align-items:center;gap:10px">
      <div style="width:24px;height:24px">
        <svg width="24" height="24" viewBox="0 0 50 50">
          <circle cx="25" cy="25" r="20" stroke="#115a8a" stroke-width="4" fill="none" stroke-opacity="0.2"/>
          <path d="M25 5 A20 20 0 0 1 45 25" stroke="#115a8a" stroke-width="4" fill="none">
            <animateTransform attributeName="transform" type="rotate"
              from="0 25 25" to="360 25 25" dur="1s" repeatCount="indefinite"/>
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
            result = fn(*args)
    placeholder.empty()
    return result


# ==================== INTEGRANTES ====================
def interface_integrantes_louvores():
    st.title("🎶 Louvores por Escala")

    st.link_button(
        "📂 Drive",
        "https://drive.google.com/drive/folders/1ME4qbcuD7ZKzhC8OVAcuIfPoLaraooTF"
    )

    st.caption(
        "🔗 Partituras, cifras, mapa vocal, divisão de vozes e tonalidades"
    )

    escalas = load_with_spinner(carregar_escala, label="Carregando escalas...")
    louvores_cadastrados = load_with_spinner(carregar_louvores_lista, label="Carregando louvores...")

    mapa_louvores = {
        l.get("louvor"): {
            "link": l.get("link", ""),
            "tom": l.get("tom", "Não informado")
        }
        for l in louvores_cadastrados
    }

    if not escalas:
        st.warning("Nenhuma escala salva ainda.")
        return

    st.markdown("### 🎥 Vídeos dos louvores por Data")

    escalas_ordenadas = sorted(
        [e for e in escalas if _is_future_or_today(e.get("Data"))],
        key=lambda x: pd.to_datetime(x.get("Data", ""), dayfirst=True)
    )

    for esc in escalas_ordenadas:
        data_tipo = f"{esc.get('Data')} - {esc.get('Tipo', '')}"
        louvores = esc.get("louvores", [])

        with st.expander(f"**{data_tipo}**"):
            if not louvores:
                st.info("Nenhum louvor cadastrado para esta data.")
                continue

            cols = st.columns(3)
            for i, louvor in enumerate(louvores):
                info = mapa_louvores.get(louvor, {})
                with cols[i % 3]:
                    st.markdown(f"**{louvor}** — Tom: {info.get('tom', 'Não informado')}")
                    if info.get("link"):
                        st.video(info["link"], width=250)
                    else:
                        st.caption("🔗 Link não disponível")


# ==================== ADMIN (CRUD LOUVORES) ====================
def interface_admin_louvores():
    st.subheader("🎵 Gerenciar Louvores")

    louvores = load_with_spinner(carregar_louvores_lista, label="Carregando louvores...")

    nomes = [""] + [l["louvor"] for l in louvores]
    selecionado = st.selectbox("Selecione um louvor para editar ou excluir:", nomes)

    dados = next((l for l in louvores if l["louvor"] == selecionado), {})

    nome = st.text_input("Nome do louvor:", value=dados.get("louvor", ""))
    link = st.text_input("Link do YouTube:", value=dados.get("link", ""))
    tom = st.text_input("Tom:", value=dados.get("tom", ""))

    if selecionado:
        c1, c2 = st.columns(2)

        with c1:
            if st.button("💾 Atualizar"):
                atualizar_louvor_bd(selecionado, nome.strip(), link.strip(), tom.strip())
                st.success("Louvor atualizado com sucesso")
                st.rerun()

        with c2:
            if st.button("🗑️ Excluir"):
                excluir_louvor(selecionado)
                st.success("Louvor excluído com sucesso")
                st.rerun()

    else:
        if st.button("➕ Adicionar Louvor"):
            salvar_louvor_bd(nome.strip(), link.strip(), tom.strip())
            st.success("Louvor adicionado com sucesso")
            st.rerun()


# ==================== UTIL ====================
def _is_future_or_today(date_str):
    try:
        d = pd.to_datetime(date_str, dayfirst=True).date()
        return d >= pd.Timestamp.now().date()
    except Exception:
        return False