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
                trigger_refresh()
                return
            else:
                st.warning("Senha incorreta")
        return

    sub_menu = st.selectbox("Escolha uma opção de administração:", [
    "Gerenciar Datas",
    "Escalar Funções",
    "Louvores",            # NOVO
    "Download Escala Final"
    ])


    datas_df = carregar_datas()
    disp_df = carregar_disponibilidade()
    escala_df = carregar_escala()
    df_funcoes, FUNCOES, INTEGRANTES = carregar_funcoes()

    # Salva no session_state para evitar re-leitura
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
        from ui_louvores import interface_admin_louvores
        datas = st.session_state.get('datas_df')['Data'].unique().tolist()
        interface_admin_louvores(datas)
    elif sub_menu == "Download Escala Final":
        download_escala_final()


def gerenciar_datas():
    datas_df = st.session_state['datas_df']
    st.subheader("Cadastro de Datas de Cultos")
    data_input = st.date_input("Escolha uma data:", min_value=pd.to_datetime('today').date())
    tipo = st.selectbox("Tipo de culto:", ["Quinta", "Domingo", "Outros"])

    if st.button("Adicionar data"):
        nova_data = {
            'Data': data_input.strftime("%d/%m/%Y"),  # Mostra formato brasileiro
            'Tipo': tipo
        }
        datas_df = datas_df.append(nova_data, ignore_index=True)
        datas_df.drop_duplicates(inplace=True)
        salvar_datas(datas_df)
        st.success(f"Data adicionada: {data_input.strftime('%d/%m/%Y')} com sucesso!")
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

    # Pega todas as datas disponíveis de disponibilidade
    datas_disponiveis = sorted(disp_df['Data'].unique())

    # Lista as datas que já possuem escala (colunas no escala_df além de 'Nome' com pelo menos uma célula preenchida)
    datas_com_escala = []
    for col in escala_df.columns:
        if col == "Nome":
            continue
        if escala_df[col].dropna().astype(str).str.strip().replace('', pd.NA).dropna().shape[0] > 0:
            datas_com_escala.append(col)

    # Remove as datas já escaladas das disponíveis
    datas_para_escalar = [d for d in datas_disponiveis if d not in datas_com_escala]

    if not datas_para_escalar:
        st.warning("Todas as datas disponíveis já foram escaladas.")
        return

    # Selectbox só com datas sem escala criada
    data_escolhida = st.selectbox("Escolha a data para escalar:", datas_para_escalar)

    # resto do seu código continua igual, usando 'data_escolhida'...


    disponiveis = disp_df[(disp_df['Data'] == data_escolhida) & (disp_df['Disponivel'] == True)]['Nome'].unique()

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
            nomes_str = ", ".join(nomes)
            st.markdown(f"**{funcao}:** {nomes_str}")
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

                # Verifica se a pessoa já está escalada nesse dia
                if col_name in escala_df.columns and nome in escala_df['Nome'].values:
                    linha_index = escala_df[escala_df['Nome'] == nome].index[0]
                    valor_atual = escala_df.at[linha_index, col_name]
                    funcoes_ja_escaladas = [f.strip() for f in str(valor_atual).split(",") if f.strip()]
                else:
                    funcoes_ja_escaladas = []

                # Verifica se há conflito (dupla função no mesmo dia, exceto Ministração)
                conflito = False
                if funcao != "Ministração" and any(f != "Ministração" for f in funcoes_ja_escaladas):
                    conflito = True

                # Verifica se já está escalado em outras datas
                datas_outras = []
                for col in escala_df.columns[1:]:  # Ignora coluna "Nome"
                    if col == col_name:
                        continue  # ignora o próprio dia atual
                    if nome in escala_df['Nome'].values:
                        linha = escala_df[escala_df['Nome'] == nome]
                        val = linha[col].values[0]
                        if isinstance(val, str) and val.strip():
                            datas_outras.append(col)

                # Monta a label do checkbox
                if conflito:
                    st.checkbox(f"{nome} ⚠️ (já escalado em: {', '.join(funcoes_ja_escaladas)})", key=key, value=False, disabled=True)
                else:
                    label = nome
                    if funcoes_ja_escaladas:
                        label += f" (já escalado em: {', '.join(funcoes_ja_escaladas)})"

                    val = st.checkbox(label, key=key)

                    # Exibe os dias em que a pessoa já está escalada em outras datas
                    if datas_outras:
                        st.caption(f"  📅 Dias em outras escalas: {', '.join(datas_outras)}")


                        if val:
                            if nome not in escala_df['Nome'].values:
                                nova_linha = pd.DataFrame([[nome]], columns=["Nome"])
                                escala_df = pd.concat([escala_df, nova_linha], ignore_index=True)

                            if col_name not in escala_df.columns:
                                escala_df[col_name] = ""

                            linha_index = escala_df[escala_df['Nome'] == nome].index[0]
                            valor_atual = escala_df.at[linha_index, col_name]
                            if pd.isna(valor_atual):
                                valor_atual = ""

                            if funcao not in valor_atual:
                                escala_df.at[linha_index, col_name] = valor_atual + f"{funcao}, "

                    else:
                        if nome in escala_df['Nome'].values and col_name in escala_df.columns:
                            linha_index = escala_df[escala_df['Nome'] == nome].index[0]
                            valor_atual = escala_df.at[linha_index, col_name]
                            if pd.isna(valor_atual):
                                valor_atual = ""
                            funcoes = [f.strip() for f in valor_atual.split(",") if f.strip() and f != funcao]
                            escala_df.at[linha_index, col_name] = ", ".join(funcoes) + (", " if funcoes else "")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Salvar Escala"):
            for col in escala_df.columns[1:]:
                escala_df[col] = escala_df[col].astype(str).str.rstrip(', ').replace('nan', '')
            salvar_escala(escala_df)
            st.success("Escala salva com sucesso!")
            trigger_refresh()

    with col2:
        if st.button("Limpar Escala"):
            escala_df = pd.DataFrame(columns=["Nome"])
            salvar_escala(escala_df)
            st.success("Escala limpa com sucesso!")
            trigger_refresh()


def download_escala_final():
    escala_df = st.session_state['escala_df']
    if escala_df.empty:
        st.info("A escala final ainda não foi criada.")
    else:
        st.dataframe(escala_df)

        # Download Excel
        towrite = io.BytesIO()
        with pd.ExcelWriter(towrite, engine='xlsxwriter') as writer:
            escala_df.to_excel(writer, index=False, sheet_name='Escala')
            writer.save()
            processed_data = towrite.getvalue()

        st.download_button(
            label="📥 Baixar Escala em Excel (.xlsx)",
            data=processed_data,
            file_name="escala_final.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Download CSV (opcional)
        st.download_button(
            label="📥 Baixar Escala em CSV",
            data=escala_df.to_csv(index=False).encode('utf-8'),
            file_name="escala_final.csv",
            mime="text/csv"
        )
