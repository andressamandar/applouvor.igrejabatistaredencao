import streamlit as st
from mongo_manager import carregar_escala, carregar_datas, carregar_louvores, carregar_funcoes
import pandas as pd
import io

# Mapa de emojis para as funções
FUNCAO_EMOJI_MAP = {
    "Violão": "Violão🎶",
    "Teclado": "Teclado 🎹",
    "Cajon": "Cajon🥁",
    "Bateria": "Bateria🥁",
    "Guitarra": "Guitarra 🎸",
    "Baixo": "Baixo 🎸",
    "Soprano": "Soprano🎤",
    "Contralto": "Contralto🎤",
    "Tenor": "Tenor 🎤",
    "Baritono": "Baritono 🎤",
    "Ministração": "MinistraçãoⓂ️",
    "Sonoplastia": "Sonoplastia🔊",
    "Projeção": "Projeção🖥️",
}

def exibir_minha_escala():
    """Exibe a escala pessoal do integrante com função e louvores (nome + tom)."""
    st.title("📅 Minha Escala")
    
    escalas = carregar_escala()
    louvores_com_detalhes = carregar_louvores()

    # Dicionário para buscar tom do louvor
    louvor_para_tom = {louvor.get('louvor'): louvor.get('tom') for louvor in louvores_com_detalhes}

    if not escalas:
        st.info("Nenhuma escala salva ainda.")
        return

    nomes_unicos = sorted({m.get('Nome') for e in escalas for m in e.get('Escala', [])})
    if not nomes_unicos:
        st.info("Nenhum integrante encontrado na escala.")
        return

    # --- Adiciona opção inicial ---
    opcoes_nomes = ["Selecione seu nome"] + nomes_unicos
    nome_selecionado = st.selectbox("Selecione seu nome:", opcoes_nomes, index=0)

    # Se o usuário não escolheu um nome válido, mostra aviso e retorna
    if nome_selecionado == "Selecione seu nome":
        st.info("Por favor, selecione seu nome para ver sua escala.")
        return

    escala_pessoal = []
    for escala in escalas:
        data = escala.get('Data')
        tipo = escala.get('Tipo')
        louvores_data = escala.get('louvores', [])

        participacao_do_integrante = next((m for m in escala.get('Escala', []) if m.get('Nome') == nome_selecionado), None)

        if participacao_do_integrante:
            funcoes = participacao_do_integrante.get('Funcoes', [])
            funcoes_str = ", ".join(funcoes) if funcoes else "Sem função definida"

            # Criando lista com apenas nome do louvor e tom
            louvores_detalhados = [
                f"{louvor_nome} (Tom: {louvor_para_tom.get(louvor_nome, 'N/A')})"
                for louvor_nome in louvores_data
            ]

            escala_pessoal.append({
                "Data": data,
                "Tipo": tipo,
                "Funcoes": funcoes_str,
                "Louvores": louvores_detalhados
            })

    if not escala_pessoal:
        st.info(f"Você não está escalado(a) neste mês.")
    else:
        st.subheader(f"🎤 Escala de {nome_selecionado}")
        for item in escala_pessoal:
            with st.expander(f"**🗓️ {item['Data']} - {item['Tipo']}**"):
                st.markdown(f"**Função:** {item['Funcoes']}")
                if item['Louvores']:
                    st.markdown("**Louvores:**")
                    for louvor in item['Louvores']:
                        st.markdown(f"- {louvor}")
                else:
                    st.warning("Nenhum louvor cadastrado para esta data.")



def exibir_escala_completa_integrantes():
    """Exibe a escala completa para todos os integrantes, de forma simplificada."""
    st.title("📋 Escala Completa")
    
    escalas = carregar_escala()
    if not escalas:
        st.info("Nenhuma escala salva ainda.")
        return

    nomes_unicos = sorted(list({p['Nome'] for esc in escalas for p in esc['Escala']}))
    
    # Cria o DataFrame para a escala
    df = pd.DataFrame({"Nome": nomes_unicos})
    for esc in escalas:
        coluna_nome = f"{esc['Data']} - {esc['Tipo']}"
        dict_funcoes = {p['Nome']: ", ".join(p['Funcoes']) for p in esc['Escala']}
        df[coluna_nome] = df['Nome'].map(dict_funcoes).fillna("")

    # Aplica os emojis na exibição
    df_display = df.copy()
    for col in df_display.columns[1:]:
        df_display[col] = df_display[col].apply(
            lambda x: ", ".join([FUNCAO_EMOJI_MAP.get(f.strip(), f.strip()) for f in x.split(',') if f.strip()]) if x else ""
        )

    st.dataframe(df_display, use_container_width=True)


def interface_integrantes():
    """Função principal que gerencia as abas da interface de integrantes."""
    
    tab1, tab2 = st.tabs(["Minha Escala", "Escala Completa"])

    with tab1:
        exibir_minha_escala()
    
    with tab2:
        exibir_escala_completa_integrantes()