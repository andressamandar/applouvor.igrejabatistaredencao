from pymongo import MongoClient
import pandas as pd
import sys
import streamlit as st

# ==================== CONEXÃO COM MONGODB =====================
try:
    mongo_uri = st.secrets["MONGODB_URI"]
    db_name = st.secrets["PORTAL_LOUVOR"]
except Exception:
    print("ERRO CRÍTICO: MONGODB_URI ou PORTAL_LOUVOR não encontrados no secrets", file=sys.stderr)
    sys.exit(1)

try:
    client = MongoClient(mongo_uri)
    db = client[db_name]
except Exception as e:
    print(f"ERRO CRÍTICO: Falha ao conectar ao MongoDB: {e}", file=sys.stderr)
    sys.exit(1)

# ==================== COLLECTIONS =====================
datas_col = db["datas"]
disponibilidades_col = db["disponibilidades"]
funcoes_col = db["funcoes"]
escala_col = db["escala"]
louvores_col = db["louvores"]
integrantes_col = db["integrantes"]


# ==================== LOUVORES (CRUD) =====================
def salvar_louvor_bd(louvor_nome, link, tom):
    louvores_col.replace_one(
        {"louvor": louvor_nome},
        {"louvor": louvor_nome, "link": link, "tom": tom},
        upsert=True
    )

def atualizar_louvor_bd(nome_antigo, novo_nome, link, tom):
    louvores_col.update_one(
        {"louvor": nome_antigo},
        {"$set": {"louvor": novo_nome, "link": link, "tom": tom}}
    )

def excluir_louvor(louvor_nome):
    louvores_col.delete_one({"louvor": louvor_nome})

def carregar_louvores():
    """
    Retorna louvores com detalhes:
    [{louvor, tom, link}]
    """
    return list(louvores_col.find({}, {"_id": 0}))

def carregar_louvores_lista():
    """
    Mantido por compatibilidade (admin antigo)
    """
    return carregar_louvores()

def buscar_louvores_disponiveis():
    """
    Retorna apenas os nomes dos louvores
    (selectbox / multiselect)
    """
    return sorted(
        l["louvor"]
        for l in louvores_col.find({}, {"louvor": 1})
        if l.get("louvor")
    )

# ==================== DATAS =====================
def salvar_data(data_str, tipo):
    datas_col.insert_one({"Data": data_str, "Tipo": tipo})

def carregar_datas():
    return list(datas_col.find({}, {"_id": 0}))

def excluir_data(data_str):
    datas_col.delete_one({"Data": data_str})
    disponibilidades_col.delete_many({"Data": data_str})

# ==================== DISPONIBILIDADE =====================
def salvar_disponibilidade(nome, data_str, disponivel=True):
    disponibilidades_col.update_one(
        {"Nome": nome, "Data": data_str},
        {"$set": {"Disponivel": disponivel}},
        upsert=True
    )

def carregar_disponibilidade():
    return list(disponibilidades_col.find({}, {"_id": 0}))

# ==================== ESCALA =====================
def salvar_escala(data_str, tipo, escala_lista):
    escala_col.replace_one(
        {"Data": data_str},
        {
            "Data": data_str,
            "Tipo": tipo,
            "Escala": escala_lista,
            "louvores": []
        },
        upsert=True
    )

def carregar_escala():
    escalas = list(escala_col.find({}, {"_id": 0}))
    for e in escalas:
        e.setdefault("louvores", [])
    return escalas

def buscar_escala_por_data(data):
    return escala_col.find_one({"Data": data}, {"_id": 0})

# ==================== FUNÇÕES / INTEGRANTES =====================
def salvar_funcoes(nome, lista_funcoes):
    funcoes_col.replace_one(
        {"Nome": nome},
        {"Nome": nome, "Funcoes": lista_funcoes},
        upsert=True
    )

def carregar_integrantes():
    return list(integrantes_col.find({}, {"_id": 0}))

def carregar_funcoes():
    data = list(funcoes_col.find({}, {"_id": 0}))

    integrantes = sorted([d["Nome"] for d in data]) if data else []
    funcoes = sorted({f for d in data for f in d.get("Funcoes", [])})

    rows = []
    for d in data:
        row = {"Nome": d["Nome"]}
        for f in funcoes:
            row[f] = "ok" if f in d.get("Funcoes", []) else ""
        rows.append(row)

    df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["Nome"] + funcoes)
    return df, funcoes, integrantes

# ==================== MINISTRO =====================
def buscar_datas_ministro(nome_ministro):
    datas = []

    docs = escala_col.find({}, {"Data": 1, "Tipo": 1, "Escala": 1})

    for doc in docs:
        for pessoa in doc.get("Escala", []):
            nomes = pessoa.get("Nome")

            # Nome pode ser string ou lista
            if isinstance(nomes, list):
                condicao_nome = nome_ministro in nomes
            else:
                condicao_nome = nome_ministro == nomes

            if condicao_nome and "Ministração" in pessoa.get("Funcoes", []):
                datas.append({
                    "Data": doc.get("Data"),
                    "Culto": doc.get("Tipo", "")
                })

    return datas

def buscar_ministros():
    ministros = set()
    escalas = escala_col.find()

    for escala in escalas:
        for pessoa in escala.get("Escala", []):
            funcoes = pessoa.get("Funcoes", [])

            if "Ministração" in funcoes:
                nomes = pessoa.get("Nome")

                # 🔹 Se for lista, adiciona nome por nome
                if isinstance(nomes, list):
                    for nome in nomes:
                        ministros.add(nome)

                # 🔹 Se for string
                elif isinstance(nomes, str):
                    ministros.add(nomes)

    return sorted(ministros)

def carregar_datas_ministro(nome_ministro):
    datas = []
    docs = escala_col.find({}, {"Data": 1, "Tipo": 1, "Escala": 1})

    for doc in docs:
        for p in doc.get("Escala", []):
            if p.get("Nome") == nome_ministro and "Ministração" in p.get("Funcoes", []):
                datas.append({
                    "Data": doc["Data"],
                    "Culto": doc.get("Tipo", "")
                })
    return datas

# ==================== LOUVORES NA ESCALA =====================
def salvar_louvores_ministro(data, ministro, louvores):
    """
    Ministro salva os louvores da data
    """
    escala_col.update_one(
        {"Data": data},
        {"$set": {"louvores": louvores}}
    )

def atualizar_louvores_escala(data, louvores):
    """
    Admin atualiza louvores da escala
    """
    escala_col.update_one(
        {"Data": data},
        {"$set": {"louvores": louvores}}
    )

from datetime import datetime

def verificar_louvor_ja_escolhido(data_atual, louvor):
    """
    Retorna avisos apenas se o louvor estiver em OUTRAS datas
    do MESMO MÊS e ANO.
    """
    avisos = []

    try:
        data_ref = datetime.strptime(data_atual, "%d/%m/%Y")
        mes_ref = data_ref.month
        ano_ref = data_ref.year
    except:
        return avisos

    docs = escala_col.find(
        {
            "louvores": louvor,
            "Data": {"$ne": data_atual}
        },
        {"Data": 1, "_id": 0}
    )

    datas_conflito = []

    for d in docs:
        try:
            data_doc = datetime.strptime(d["Data"], "%d/%m/%Y")
            if data_doc.month == mes_ref and data_doc.year == ano_ref:
                datas_conflito.append(d["Data"])
        except:
            continue

    if datas_conflito:
        datas_txt = ", ".join(datas_conflito)
        avisos.append(
            f"⚠️ O louvor **{louvor}** já está escalado neste mês em: {datas_txt}"
        )

    return avisos

# ==================== MIDIA =====================

# -------- DATAS --------
def salvar_data_midia(data_str, tipo):
    db["midia_datas"].insert_one({"Data": data_str, "Tipo": tipo})

def carregar_datas_midia():
    return list(db["midia_datas"].find({}, {"_id": 0}))

def excluir_data_midia(data_str):
    db["midia_datas"].delete_one({"Data": data_str})
    db["midia_disponibilidades"].delete_many({"Data": data_str})


# -------- DISPONIBILIDADE --------
def salvar_disponibilidade_midia(nome, data_str, disponivel=True):
    db["midia_disponibilidades"].update_one(
        {"Nome": nome, "Data": data_str},
        {"$set": {"Disponivel": disponivel}},
        upsert=True
    )

def carregar_disponibilidade_midia():
    return list(db["midia_disponibilidades"].find({}, {"_id": 0}))


# -------- ESCALA --------
def salvar_escala_midia(data_str, tipo, escala_lista):
    db["midia_escala"].replace_one(
        {"Data": data_str},
        {
            "Data": data_str,
            "Tipo": tipo,
            "Escala": escala_lista
        },
        upsert=True
    )

def carregar_escala_midia():
    return list(db["midia_escala"].find({}, {"_id": 0}))


# -------- FUNÇÕES --------
def carregar_funcoes_midia():
    data = list(db["midia_funcoes"].find({}, {"_id": 0}))

    integrantes = sorted([
    d.get("Nome") or d.get("nome")
    for d in data
    if d.get("Nome") or d.get("nome")
    ]) if data else []
    funcoes = sorted({f for d in data for f in d.get("Funcoes", [])})

    return data, funcoes, integrantes


# -------- TAREFAS --------
def criar_tarefa_midia(titulo, responsavel=None):
    db["midia_tarefas"].insert_one({
        "titulo": titulo,
        "responsavel": None,
        "status": "A Fazer"
    })

def carregar_tarefas_midia():
    return list(db["midia_tarefas"].find({}, {"_id": 0}))

def atualizar_status_tarefa_midia(titulo, status):
    db["midia_tarefas"].update_one(
        {"titulo": titulo},
        {"$set": {"status": status}}
    )
    

def carregar_integrantes_midia():
    data = list(db["midia_funcoes"].find({}, {"_id": 0}))

    return sorted([
        d.get("Nome")
        for d in data
        if d.get("Nome")
    ])
    
def assumir_tarefa_midia(titulo, nome):
    db["midia_tarefas"].update_one(
        {"titulo": titulo},
        {"$set": {"responsavel": nome, "status": "Fazendo"}}
    )
    
# ================= INTEGRANTES MIDIA =================

def salvar_integrante_midia(nome, funcoes):
    db["midia_funcoes"].update_one(
        {"nome": nome},
        {"$set": {
            "nome": nome,   # 🔥 PADRÃO DEFINITIVO
            "funcoes": funcoes
        }},
        upsert=True
    )

def carregar_integrantes_midia():
    dados = list(db["midia_funcoes"].find({}, {"_id": 0}))

    nomes = []
    for i in dados:
        nome = i.get("nome") or i.get("Nome")
        if nome:
            nomes.append(nome)

    return sorted(nomes)

def excluir_integrante_midia(nome):
    db["midia_funcoes"].delete_one({"nome": nome})