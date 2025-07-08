import streamlit as st
import io
import pandas as pd
from data_manager import carregar_datas, carregar_disponibilidade, carregar_escala, carregar_funcoes, salvar_datas, salvar_escala
from session_manager import login_admin
from ui_louvores import interface_admin_louvores, interface_integrantes_louvores

# Gatilho de atualização
def trigger_refresh():
    st.session_state['refresh'] = not st.session_state.get('refresh', False)

def interface_admin():
    if not st.session_state.get('admin_logado', False):
        senha = st.text_input("Senha do Admin:", type="password")
        if st.button("Login"):
            if login_admin(senha):
                st.success("Login realizado com sucesso!")
                st.session_state['admin_logado'] = True
                trigger_refresh()
                return
            else:
                st.warning("Senha incorreta")
        return

    sub_menu = st.selectbox("Escolha uma opção de administração:", [
        "Gerenciar Datas",
        "Escalar Funções",
        "Louvores",
        "Download Escala Final"
    ])

    datas_df = carregar_datas()
    disp_df = carregar_disponibilidade()
    escala_df = carregar_escala()
    df_funcoes, FUNCOES, INTEGRANTES = carregar_funcoes()

    st.session_state['datas_df'] = datas_df
    st.session_state['disp_df'] = disp_df
    st.session_state['escala_df'] = escala_df
    st.session_state['df_funcoes'] = df_funcoes
    st.session_state['funcoes'] = FUNCOES
    st.session_state['integrantes'] = INTEGRANTES

    if sub_menu == "Gerenciar Datas":
        gerenciar_datas()
    elif sub_menu == "Escalar Funções":
        interface_escalar_funcoes()
    elif sub_menu == "Louvores":
        datas = datas_df['Data'].unique().tolist()
        interface_admin_louvores(datas)
    elif sub_menu == "Download Escala Final":
        download_escala_final()

def gerenciar_datas():
    datas_df = st.session_state['datas_df']
    st.subheader("Cadastro de Datas de Cultos")
    data_input = st.date_input("Escolha uma data:", min_value=pd.to_datetime('today').date())
    tipo = st.selectbox("Tipo de culto:", ["Quinta", "Domingo", "Outros"])

    if st.button("Adicionar data"):
        nova_data = {'Data': data_input.strftime("%d/%m/%Y"), 'Tipo': tipo}
        datas_df = pd.concat([datas_df, pd.DataFrame([nova_data])], ignore_index=True)
        datas_df.drop_duplicates(inplace=True)
        salvar_datas(datas_df)
        st.success(f"Data adicionada: {nova_data['Data']} com sucesso!")
        trigger_refresh()

    st.subheader("Datas cadastradas")
    st.dataframe(datas_df)

    st.subheader("Excluir data")
    data_para_excluir = st.selectbox("Selecione a data a excluir:", datas_df['Data'].unique())
    if st.button("Excluir data selecionada"):
        datas_df = datas_df[datas_df['Data'] != data_para_excluir]
        salvar_datas(datas_df)
        st.success(f"Data {data_para_excluir} excluída com sucesso!")
        trigger_refresh()

def interface_escalar_funcoes():
    disp_df = st.session_state['disp_df']
    escala_df = st.session_state['escala_df']
    df_funcoes = st.session_state['df_funcoes']
    FUNCOES = st.session_state['funcoes']

    datas_disponiveis = sorted(disp_df['Data'].unique())
    datas_com_escala = [
        col for col in escala_df.columns if col != "Nome" and
        escala_df[col].dropna().astype(str).str.strip().replace('', pd.NA).dropna().shape[0] > 0
    ]
    datas_para_escalar = [d for d in datas_disponiveis if d not in datas_com_escala]

    if not datas_para_escalar:
        st.warning("Todas as datas disponíveis já foram escaladas.")
        return

    data_escolhida = st.selectbox("Escolha a data para escalar:", datas_para_escalar)
    disponiveis = disp_df[(disp_df['Data'] == data_escolhida) & (disp_df['Disponivel'])]['Nome'].unique()

    if len(disponiveis) == 0:
        st.warning("Ninguém se disponibilizou para esta data ainda.")
        return

    if 'Nome' not in escala_df.columns:
        escala_df['Nome'] = []

    st.markdown("### ✅ Resumo das Escalas (pré-visualização)")
    resumo_funcoes = {}
    for funcao in FUNCOES:
        for nome in disponiveis:
            key = f"{funcao}_{data_escolhida}_{nome}"
            if st.session_state.get(key):
                resumo_funcoes.setdefault(funcao, []).append(nome)

    if resumo_funcoes:
        for funcao, nomes in resumo_funcoes.items():
            st.markdown(f"**{funcao}:** {', '.join(nomes)}")
    else:
        st.info("Nenhuma função escalada ainda.")

    st.markdown("---")

    for funcao in FUNCOES:
        with st.expander(f"{funcao}"):
            habilitados = df_funcoes[df_funcoes[funcao] == "ok"]['Nomes'].dropna().tolist()
            candidatos = [n for n in disponiveis if n in habilitados]

            for nome in candidatos:
                col_name = data_escolhida
                key = f"{funcao}_{data_escolhida}_{nome}"

                # Garante que a linha e a coluna existem
                if nome not in escala_df['Nome'].values:
                    escala_df = pd.concat([escala_df, pd.DataFrame([[nome]], columns=["Nome"])]).reset_index(drop=True)
                if col_name not in escala_df.columns:
                    escala_df[col_name] = ""

                linha_index = escala_df[escala_df['Nome'] == nome].index[0]

                # Correção segura para evitar erro de tipo
                valor_bruto = escala_df.at[linha_index, col_name]
                atual = str(valor_bruto) if pd.notna(valor_bruto) else ""
                funcoes_ja_escaladas = [f.strip() for f in atual.split(",") if f.strip()]

                conflito = funcao != "Ministração" and any(f != "Ministração" for f in funcoes_ja_escaladas)

                datas_outras = []
                for col in escala_df.columns[1:]:
                    if col == col_name:
                        continue
                    if nome in escala_df['Nome'].values:
                        linha = escala_df[escala_df['Nome'] == nome]
                        val = linha[col].values[0]
                        if isinstance(val, str) and val.strip():
                            datas_outras.append(col)

                label = nome + (f" (já escalado em: {', '.join(funcoes_ja_escaladas)})" if funcoes_ja_escaladas else "")
                if conflito:
                    st.checkbox(f"{label} ⚠️", key=key, value=False, disabled=True)
                    continue

                val = st.checkbox(label, key=key)
                if datas_outras:
                    st.caption(f"\u2003\u2003📅 Dias em outras escalas: {', '.join(datas_outras)}")

                if val:
                    if funcao not in atual:
                        escala_df.at[linha_index, col_name] = atual + f"{funcao}, "

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Salvar Escala", key="btn_salvar"):
            for col in escala_df.columns[1:]:
                escala_df[col] = escala_df[col].astype(str).str.rstrip(', ').replace('nan', '')
            salvar_escala(escala_df)
            st.session_state['escala_df'] = escala_df
            st.session_state['escala_salva'] = True

        if st.session_state.get('escala_salva'):
            st.success("✅ Escala salva com sucesso!")
            st.session_state['escala_salva'] = False

    with col2:
        if st.button("Limpar Escala", key="btn_limpar"):
            escala_df = pd.DataFrame(columns=["Nome"])
            salvar_escala(escala_df)
            st.session_state['escala_df'] = escala_df
            st.success("🪑 Escala limpa com sucesso!")
            trigger_refresh()


def download_escala_final():
    escala_df = st.session_state['escala_df']

    if escala_df.empty:
        st.info("A escala final ainda não foi criada.")
        return

    # Remove colunas indesejadas como "Unnamed: 1"
    escala_df = escala_df.loc[:, ~escala_df.columns.str.contains('^Unnamed')]

    st.dataframe(escala_df)

    towrite = io.BytesIO()
    with pd.ExcelWriter(towrite, engine='xlsxwriter') as writer:
        escala_df.to_excel(writer, index=False, sheet_name='Escala')
    processed_data = towrite.getvalue()

    st.download_button(
        label="📅 Baixar Escala em Excel (.xlsx)",
        data=processed_data,
        file_name="escala_final.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.download_button(
        label="📅 Baixar Escala em CSV",
        data=escala_df.to_csv(index=False).encode('utf-8'),
        file_name="escala_final.csv",
        mime="text/csv"
    )
