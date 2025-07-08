import pandas as pd
import os
from config import ARQ_DATAS, ARQ_DISPONIBILIDADE, ARQ_ESCALA_FINAL, ARQ_FUNCOES

def inicializa_csvs():
    if not os.path.exists(ARQ_DATAS):
        pd.DataFrame(columns=["Data", "Tipo"]).to_csv(ARQ_DATAS, index=False)
    if not os.path.exists(ARQ_DISPONIBILIDADE):
        pd.DataFrame(columns=["Nome", "Data", "Disponivel"]).to_csv(ARQ_DISPONIBILIDADE, index=False)
    if not os.path.exists(ARQ_ESCALA_FINAL):
        pd.DataFrame(columns=["Nome"]).to_csv(ARQ_ESCALA_FINAL, index=False)

def carregar_datas():
    return pd.read_csv(ARQ_DATAS)

def carregar_disponibilidade():
    return pd.read_csv(ARQ_DISPONIBILIDADE)

def carregar_escala():
    return pd.read_csv(ARQ_ESCALA_FINAL)

def carregar_funcoes():
    df_funcoes = pd.read_excel(ARQ_FUNCOES)
    funcoes = df_funcoes.columns[1:].tolist()
    integrantes = df_funcoes['Nomes'].dropna().tolist()
    return df_funcoes, funcoes, integrantes

def salvar_datas(df):
    df.to_csv(ARQ_DATAS, index=False)

def salvar_disponibilidade(df):
    df.to_csv(ARQ_DISPONIBILIDADE, index=False)

def salvar_escala(df):
    df.to_csv(ARQ_ESCALA_FINAL, index=False)
