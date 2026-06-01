# %%
import pandas as pd
from loguru import logger
from services.api import baixar_dados_paginados, baixar_dados_paginados_Id
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")

DATABASE_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)
    
# Cria o engine e a sessão
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def query_postgres():
    query = """
    SELECT id
    FROM deputados
    """

    df_ids = pd.read_sql(query, engine)

    return df_ids["id"].tolist()

def salvar_dados_postgres(df):

    try:

        df.to_sql(
            name="despesas",
            con=engine,
            if_exists="append",
            index=False
        )

        print("Dados salvos com sucesso!")

    except Exception as e:

        print(f"Erro ao salvar dados: {e}")   


def bronze():    
    ids = query_postgres()

    for id_deputado in ids:

        data = baixar_dados_paginados_Id(
            endpoint="deputados",
            id=id_deputado,
            complemento="despesas"
        )
    return data

def silver():     

    # linha necessária de execução apenas em produção
    bronze()

    pasta = './jsons/despesas'
    arquivos = os.listdir(pasta)

    dados_acumulados = []

    for arq in arquivos:
        caminho_arquivo = os.path.join(pasta, arq)
        df = pd.read_json(caminho_arquivo) 

        try:
            # Tenta extrair o ID do deputado caso esteja no nome do arquivo
            id_deputado = int(arq.split('_')[1])
            df['idDeputado'] = id_deputado
        except:
            pass

        dados_acumulados.append(df)

    df = pd.concat(dados_acumulados, ignore_index=True)  
    # Deduplicação geral de registros
    df = df.drop_duplicates()
    
    # Conversão para numérico e filtro de valores monetários positivos
    df['valorLiquido'] = pd.to_numeric(df['valorLiquido'], errors='coerce')
    df = df[df['valorLiquido'] > 0]
    
    # Conversão de datas e filtro de range válido (ex: apenas a partir de 2023)
    df['dataDocumento'] = pd.to_datetime(df['dataDocumento'], errors='coerce')
    df = df.dropna(subset=['dataDocumento'])
    df = df[df['dataDocumento'] >= '2023-01-01']
      
    return df     


def gold():
    df = silver()
    salvar_dados_postgres(df)
    logger.success("Pipeline concluído com sucesso!")


if __name__ == "__main__":    
    gold()


# %%
