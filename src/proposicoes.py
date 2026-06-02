# %%
import pandas as pd
from loguru import logger
from services.api import baixar_dados_paginados
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DB_URL")
    
# Cria o engine e a sessão
engine = create_engine(DATABASE_URL, connect_args={"sslmode": "require"})
Session = sessionmaker(bind=engine)

def salvar_dados_postgres(df):

    try:

        df.to_sql(
            name="proposicoes",
            con=engine,
            if_exists="append",
            index=False
        )

        print("Dados salvos com sucesso!")

    except Exception as e:

        print(f"Erro ao salvar dados: {e}")   


def bronze():    
    data = baixar_dados_paginados(endpoint="proposicoes")
    return data

def silver():     

    # linha necessária de execução apenas em produção
    bronze()

    pasta = './jsons/proposicoes'
    arquivos = os.listdir(pasta)

    dados_acumulados = []

    for arq in arquivos:
        caminho_arquivo = os.path.join(pasta, arq)
        df = pd.read_json(caminho_arquivo) 
        dados_acumulados.append(df)

    df = pd.concat(dados_acumulados, ignore_index=True)   

    # Deduplicação pela chave primária
    df = df.drop_duplicates(subset=['id'], keep='last')
    
    # Validação: campos obrigatórios
    df = df.dropna(subset=['id', 'ementa'])
    
    # Conversão de datas e filtro de range válido (ex: a partir de 1988)
    df['dataApresentacao'] = pd.to_datetime(df['dataApresentacao'], errors='coerce')
    df = df.dropna(subset=['dataApresentacao'])
    df = df[df['dataApresentacao'] >= '1988-01-01']

    return df     


def gold():
    df = silver()
    salvar_dados_postgres(df)
    logger.success("Pipeline concluído com sucesso!")


if __name__ == "__main__":    
    gold()


# %%
