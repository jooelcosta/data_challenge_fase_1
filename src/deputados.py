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
            name="deputados",
            con=engine,
            if_exists="append",
            index=False
        )

        print("Dados salvos com sucesso!")

    except Exception as e:

        print(f"Erro ao salvar dados: {e}")   


def bronze():    
    data = baixar_dados_paginados(endpoint="deputados")
    return data

def silver():    

    # linha necessária de execução apenas em produção
    bronze()

    pasta = './jsons/deputados'
    arquivos = os.listdir(pasta)

    dados_acumulados = []

    for arq in arquivos:
        caminho_arquivo = os.path.join(pasta, arq)
        df = pd.read_json(caminho_arquivo) 
        dados_acumulados.append(df)

    df = pd.concat(dados_acumulados, ignore_index=True) 

    # Deduplicação pela chave primária
    df = df.drop_duplicates(subset=['id'], keep='last')
    
    # Validação: remover nulos em campos obrigatórios
    df = df.dropna(subset=['id', 'nome'])

    timestamp = pd.Timestamp.now()
    df['created_at'] = timestamp
       
    return df     

def gold():
    df = silver()
    salvar_dados_postgres(df)
    logger.success("Pipeline concluído com sucesso!")


if __name__ == "__main__":    
    gold()


# %%
