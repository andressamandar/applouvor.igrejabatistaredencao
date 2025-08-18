from pymongo import MongoClient
import pandas as pd
import sys
import streamlit as st

# ==================== CONEXÃO COM MONGODB =====================
try:
    mongo_uri = st.secrets["MONGODB_URI"]
    db_name = st.secrets["PORTAL_LOUVOR"]
except Exception as e:
    print("ERRO CRÍTICO: Variáveis MONGODB_URI ou PORTAL_LOUVOR não encontradas em st.secrets", file=sys.stderr)
    sys.exit(1)

# Conectar ao MongoDB
try:
    client = MongoClient(mongo_uri)
    db = client[db_name]
    print(f"DEBUG: Conexão com MongoDB estabelecida para o banco de dados: {db.name}")
except Exception as e:
    print(f"ERRO CRÍTICO: Falha ao conectar ao MongoDB. Detalhes: {e}", file=sys.stderr)
    sys.exit(1)

# Collections
datas_col = db["datas"]
disponibilidades_col = db["disponibilidades"]
funcoes_col = db["funcoes"]
escala_col = db["escala"]
louvores_col = db["louvores"]
integrantes_col = db["integrantes"]

# ==================== LOUVORES =====================
def salvar_louvor_bd(louvor_nome, link, tom):
    louvores_col.replace_one(
        {"louvor": louvor_nome},
        {"louvor": louvor_nome, "link": link, "tom": tom},
        upsert=True
    )
    print(f"DEBUG: Louvor '{louvor_nome}' salvo/atualizado.")

def excluir_louvor(louvor_nome):
    louvores_col.delete_one({"louvor": louvor_nome})
    print(f"DEBUG: Louvor '{louvor_nome}' excluído.")

def salvar_data(data_str, tipo):
    datas_col.insert_one({"Data": data_str, "Tipo": tipo})

def carregar_datas():
    return list(datas_col.find({}, {"_id": 0}))

def excluir_data(data_str):
    datas_col.delete_one({"Data": data_str})
    disponibilidades_col.delete_many({"Data": data_str})
    print(f"DEBUG: Data {data_str} e suas disponibilidades relacionadas excluídas.")

# ==================== DISPONIBILIDADE =====================
def salvar_disponibilidade(nome, data_str, disponivel=True):
    disponibilidades_col.update_one(
        {"Nome": nome, "Data": data_str},
        {"$set": {"Disponivel": disponivel}},
        upsert=True
    )
    print(f"DEBUG: Disponibilidade salva para {nome} em {data_str}: {disponivel}")

def carregar_disponibilidade():
    registros = list(disponibilidades_col.find({}, {"_id": 0}))
    print("DEBUG: Registros carregados:", registros)
    return registros

# ==================== ESCALA =====================
def salvar_escala(data_str, tipo, escala_lista):
    documento = {"Data": data_str, "Tipo": tipo, "Escala": escala_lista, "louvores": []}
    escala_col.replace_one({"Data": data_str}, documento, upsert=True)
    print(f"DEBUG: Escala salva para {data_str} sem louvores.")

def carregar_escala():
    return list(escala_col.find({}, {"_id": 0}))

def atualizar_louvores_escala(data_str, louvores):
    escala_col.update_one(
        {"Data": data_str},
        {"$set": {"louvores": louvores}},
        upsert=False
    )
    print(f"DEBUG: Louvores atualizados para {data_str}: {louvores}")

# ==================== LOUVORES =====================
def carregar_louvores_lista():
    return list(louvores_col.find({}, {"_id": 0}))

def salvar_louvor(data_str, louvores):
    if not data_str or not isinstance(louvores, list):
        print(f"ERRO: Dados inválidos ao salvar louvor. Data: {data_str}, Louvores: {louvores}")
        return
    louvores_col.replace_one(
        {"Data": data_str},
        {"Data": data_str, "Louvores": louvores},
        upsert=True
    )
    print(f"DEBUG: Louvor salvo para {data_str}.")

def carregar_louvores_por_escala(data_str):
    doc = escala_col.find_one({"Data": data_str}, {"_id": 0, "louvores": 1})
    return doc.get("louvores", []) if doc else []

def carregar_louvores():
    return list(louvores_col.find({}, {"_id": 0}))

def carregar_louvor_por_data(data_str):
    doc = louvores_col.find_one({"Data": data_str}, {"_id": 0})
    return doc["Louvores"] if doc and "Louvores" in doc else []

# ==================== FUNÇÕES DOS INTEGRANTES =====================
def salvar_funcoes(nome, lista_funcoes):
    funcoes_col.replace_one(
        {"Nome": nome},
        {"Nome": nome, "Funcoes": lista_funcoes},
        upsert=True
    )
    print(f"DEBUG: Funções salvas para {nome}.")

def carregar_integrantes():
    return list(integrantes_col.find({}, {"_id": 0}))

def carregar_funcoes():
    data = list(funcoes_col.find({}, {"_id": 0}))
    INTEGRANTES = sorted([d["Nome"] for d in data]) if data else []
    all_funcoes_list = []
    for item in data:
        if "Funcoes" in item and isinstance(item["Funcoes"], list):
            all_funcoes_list.extend(item["Funcoes"])
    FUNCOES = sorted(list(set(all_funcoes_list))) if all_funcoes_list else []

    rows_list = []
    for integrante_doc in data:
        nome = integrante_doc.get("Nome")
        funcoes = integrante_doc.get("Funcoes", [])
        row_data = {'Nome': nome}
        for func in FUNCOES:
            row_data[func] = "ok" if func in funcoes else ""
        rows_list.append(row_data)

    df_funcoes_pivot = pd.DataFrame(rows_list)
    if df_funcoes_pivot.empty:
        df_funcoes_pivot = pd.DataFrame(columns=['Nome'] + FUNCOES)

    return df_funcoes_pivot, FUNCOES, INTEGRANTES
