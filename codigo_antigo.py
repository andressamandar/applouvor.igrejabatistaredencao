# import streamlit as st
# import pandas as pd
# import datetime
# import os
# import time
# from io import BytesIO

# # Arquivos CSV auxiliares
# ARQ_DATAS = "datas_cultos.csv"
# ARQ_DISPONIBILIDADE = "disponibilidade.csv"
# ARQ_ESCALA_FINAL = "escala_final.xlsx"
# ARQ_FUNCOES = "nomes_funções.xlsx"  # novo

# # Funções do ministério (extraídas da planilha)
# df_funcoes = pd.read_excel(ARQ_FUNCOES)
# FUNCOES = df_funcoes.columns[1:].tolist()
# INTEGRANTES = df_funcoes['Nomes'].dropna().tolist()

# # Inicializa arquivos
# def inicializa_csvs():
#     if not os.path.exists(ARQ_DATAS):
#         pd.DataFrame(columns=["Data", "Tipo"]).to_csv(ARQ_DATAS, index=False)
#     if not os.path.exists(ARQ_DISPONIBILIDADE):
#         pd.DataFrame(columns=["Nome", "Data", "Disponivel"]).to_csv(ARQ_DISPONIBILIDADE, index=False)
#     if not os.path.exists(ARQ_ESCALA_FINAL):
#         pd.DataFrame(columns=["Nome"]).to_csv(ARQ_ESCALA_FINAL, index=False)

# inicializa_csvs()

# # Carrega dados
# datas_df = pd.read_csv(ARQ_DATAS)
# disp_df = pd.read_csv(ARQ_DISPONIBILIDADE)
# escala_df = pd.read_csv(ARQ_ESCALA_FINAL)

# # Sessão com expiração
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

# check_login()

# # Sidebar
# st.sidebar.title("Menu")
# menu = st.sidebar.radio("Ir para:", ["Disponibilidade", "Admin"])

# if menu == "Disponibilidade":
#     st.title("Disponibilidade para os Cultos")
#     st.markdown("Marque abaixo os dias em que você **NÃO poderá participar**:")

#     nome = st.selectbox("Selecione seu nome:", INTEGRANTES)

#     disponibilidade_total = st.checkbox("Estou disponível para todos os cultos")

#     checkboxes = {}

#     if nome:
#         if not disponibilidade_total:
#             for i, row in datas_df.iterrows():
#                 data = row['Data']
#                 key = f"indisp_{data}"
#                 checkboxes[data] = st.checkbox(f"Não estarei disponível em {data}", key=key)

#         if st.button("Salvar Disponibilidade"):
#             disp_df = disp_df[disp_df['Nome'] != nome]

#             for i, row in datas_df.iterrows():
#                 data = row['Data']
#                 if disponibilidade_total:
#                     disponivel = True
#                 else:
#                     disponivel = not checkboxes.get(row['Data'], False)

#                 nova_linha = pd.DataFrame([[nome, data, disponivel]], columns=["Nome", "Data", "Disponivel"])
#                 disp_df = pd.concat([disp_df, nova_linha], ignore_index=True)

#             disp_df.to_csv(ARQ_DISPONIBILIDADE, index=False)
#             st.success("Disponibilidade registrada com sucesso!")
#             st.stop()


# elif menu == "Admin":
#     st.title("Acesso Admin")

#     if not st.session_state['admin_logado']:
#         senha = st.text_input("Senha do Admin:", type="password")
#         if senha == "admin.ibr":
#             st.session_state['admin_logado'] = True
#             st.session_state['admin_login_time'] = time.time()
#             st.success("Login realizado com sucesso!")
#         else:
#             st.warning("Senha incorreta")

#     if st.session_state['admin_logado']:
#         sub_menu = st.selectbox("Escolha uma opção de administração:", [
#             "Gerenciar Datas",
#             "Escalar Funções",
#             "Download Escala Final"
#         ])

#         if sub_menu == "Gerenciar Datas":
#             st.subheader("Cadastro de Datas de Cultos")
#             data_input = st.date_input("Escolha uma data:", min_value=datetime.date.today())
#             tipo = st.selectbox("Tipo de culto:", ["Quinta", "Domingo"])

#             if st.button("Adicionar data"):
#                 nova_data = pd.DataFrame([[data_input.strftime("%d/%m/%Y"), tipo]], columns=["Data", "Tipo"])
#                 datas_df = pd.concat([datas_df, nova_data], ignore_index=True)
#                 datas_df.drop_duplicates(inplace=True)
#                 datas_df.to_csv(ARQ_DATAS, index=False)
#                 st.success("Data adicionada com sucesso!")
#                 st.stop()

#             st.subheader("Datas cadastradas")
#             st.dataframe(datas_df)

#             st.subheader("Excluir data")
#             data_para_excluir = st.selectbox("Selecione a data a excluir:", datas_df['Data'].unique())
#             if st.button("Excluir data selecionada"):
#                 datas_df = datas_df[datas_df['Data'] != data_para_excluir]
#                 datas_df.to_csv(ARQ_DATAS, index=False)
#                 st.success(f"Data {data_para_excluir} excluída com sucesso!")
#                 st.stop()

#         elif sub_menu == "Escalar Funções":
#             st.subheader("Escalar Funções por Data")
#             data_escolhida = st.selectbox("Escolha a data para escalar:", datas_df['Data'].unique())
#             disponiveis = disp_df[(disp_df['Data'] == data_escolhida) & (disp_df['Disponivel'] == True)]['Nome'].unique()

#             if len(disponiveis) == 0:
#                 st.warning("Ninguém se disponibilizou para esta data ainda.")
#             else:
#                 if 'Nome' not in escala_df.columns:
#                     escala_df['Nome'] = []

#                 st.markdown("### ✅ Resumo das Escalas (pré-visualização)")
#                 resumo_funcoes = {}

#                 for funcao in FUNCOES:
#                     for nome in disponiveis:
#                         key = f"{funcao}_{data_escolhida}_{nome}"
#                         if st.session_state.get(key):
#                             if funcao not in resumo_funcoes:
#                                 resumo_funcoes[funcao] = []
#                             resumo_funcoes[funcao].append(nome)

#                 if resumo_funcoes:
#                     for funcao, nomes in resumo_funcoes.items():
#                         nomes_str = ", ".join(nomes)
#                         st.markdown(f"**{funcao}:** {nomes_str}")
#                 else:
#                     st.info("Nenhuma função escalada ainda.")

#                 st.markdown("---")

#                 for funcao in FUNCOES:
#                     with st.expander(f"{funcao}"):
#                         habilitados = df_funcoes[df_funcoes[funcao] == "ok"]['Nomes'].dropna().tolist()
#                         candidatos = [n for n in disponiveis if n in habilitados]
#                         for nome in candidatos:
#                             col_name = f"{data_escolhida}"
#                             key = f"{funcao}_{data_escolhida}_{nome}"

#                             # Recupera o valor atual da pessoa na escala (se existir)
#                             if col_name in escala_df.columns and nome in escala_df['Nome'].values:
#                                 linha_index = escala_df[escala_df['Nome'] == nome].index[0]
#                                 valor_atual = escala_df.at[linha_index, col_name]
#                                 funcoes_ja_escaladas = [f.strip() for f in str(valor_atual).split(",") if f.strip()]
#                             else:
#                                 funcoes_ja_escaladas = []

#                             # Verifica se já foi escalado para função incompatível
#                             conflito = False
#                             if funcao != "Ministração" and any(
#                                 f != "Ministração" for f in funcoes_ja_escaladas
#                             ):
#                                 conflito = True

#                             if conflito:
#                                 st.checkbox(f"{nome} ⚠️ (já escalado em: {', '.join(funcoes_ja_escaladas)})", key=key, value=False, disabled=True)
#                             else:
#                                 val = st.checkbox(f"{nome}", key=key)
#                                 if val:
#                                     if nome not in escala_df['Nome'].values:
#                                         nova_linha = pd.DataFrame([[nome]], columns=["Nome"])
#                                         escala_df = pd.concat([escala_df, nova_linha], ignore_index=True)

#                                     if col_name not in escala_df.columns:
#                                         escala_df[col_name] = ""

#                                     linha_index = escala_df[escala_df['Nome'] == nome].index[0]
#                                     valor_atual = escala_df.at[linha_index, col_name]
#                                     if pd.isna(valor_atual):
#                                         valor_atual = ""

#                                     if funcao not in valor_atual:
#                                         escala_df.at[linha_index, col_name] = valor_atual + f"{funcao}, "

#                             if val:
#                                 if nome not in escala_df['Nome'].values:
#                                     nova_linha = pd.DataFrame([[nome]], columns=["Nome"])
#                                     escala_df = pd.concat([escala_df, nova_linha], ignore_index=True)

#                                 if col_name not in escala_df.columns:
#                                     escala_df[col_name] = ""

#                                 linha_index = escala_df[escala_df['Nome'] == nome].index[0]
#                                 valor_atual = escala_df.at[linha_index, col_name]
#                                 if pd.isna(valor_atual):
#                                     valor_atual = ""

#                                 if funcao not in valor_atual:
#                                     escala_df.at[linha_index, col_name] = valor_atual + f"{funcao}, "

#                 if st.button("Salvar Escala"):
#                     for col in escala_df.columns[1:]:
#                         escala_df[col] = escala_df[col].astype(str).str.rstrip(', ').replace('nan', '')
#                     escala_df.to_csv(ARQ_ESCALA_FINAL, index=False)
#                     st.success("Escala salva com sucesso!")
#                     st.stop()

#                 if st.button("Limpar Escala"):
#                     escala_df = pd.DataFrame(columns=["Nome"])
#                     escala_df.to_csv(ARQ_ESCALA_FINAL, index=False)
#                     st.success("Escala limpa com sucesso!")
#                     st.stop()


#         elif sub_menu == "Download Escala Final":
#             st.subheader("Baixar Escala Final em Excel")
            
#             if os.path.exists(ARQ_ESCALA_FINAL):
#                 df_excel = pd.read_csv(ARQ_ESCALA_FINAL)

#                 # Remove colunas "Unnamed"
#                 df_excel = df_excel.loc[:, ~df_excel.columns.str.contains("^Unnamed")]

#                 # Exibe no app
#                 st.dataframe(df_excel)

#                 # Converte para Excel (.xlsx)
#                 output = BytesIO()
#                 with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
#                     df_excel.to_excel(writer, index=False, sheet_name='Escala')
#                 excel_data = output.getvalue()

#                 st.download_button(
#                     label="📥 Baixar Escala em Excel",
#                     data=excel_data,
#                     file_name="escala_final.xlsx",
#                     mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#                 )
#             else:
#                 st.info("A escala final ainda não foi criada.")