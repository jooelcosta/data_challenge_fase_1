# %%
import pandas as pd
from loguru import logger
from services.api import baixar_dados_paginados, baixar_dados_paginados_Id
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DB_URL")

# Cria o engine e a sessão
engine = create_engine(DATABASE_URL, connect_args={"sslmode": "require"})
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

        df.to_sql(name="despesas", con=engine, if_exists="append", index=False)

        print("Dados salvos com sucesso!")

    except Exception as e:

        print(f"Erro ao salvar dados: {e}")


def bronze(data_inicio: str, data_fim: str):
    ids = query_postgres()

    for id_deputado in ids:

        data = baixar_dados_paginados_Id(
            endpoint="deputados",
            id=id_deputado,
            complemento="despesas",
            data_inicio=data_inicio,
            data_fim=data_fim,
        )
    return data


def silver(data_inicio: str, data_fim: str):

    # linha necessária de execução apenas em produção
    bronze(data_inicio=data_inicio, data_fim=data_fim)

    pasta = "./jsons/despesas"
    arquivos = os.listdir(pasta)

    dados_acumulados = []

    for arq in arquivos:
        caminho_arquivo = os.path.join(pasta, arq)
        df = pd.read_json(caminho_arquivo)

        try:
            # Tenta extrair o ID do deputado caso esteja no nome do arquivo
            id_deputado = int(arq.split("_")[1])
            df["idDeputado"] = id_deputado
        except:
            pass

        dados_acumulados.append(df)

    df = pd.concat(dados_acumulados, ignore_index=True)
    # Deduplicação geral de registros
    df = df.drop_duplicates()

    # Conversão para numérico e filtro de valores monetários positivos
    df["valorLiquido"] = pd.to_numeric(df["valorLiquido"], errors="coerce")
    df = df[df["valorLiquido"] > 0]

    # Conversão de datas e filtro de range válido (ex: apenas a partir de 2023)
    df["dataDocumento"] = pd.to_datetime(df["dataDocumento"], errors="coerce")
    df = df.dropna(subset=["dataDocumento"])
    df = df[df["dataDocumento"] >= "2023-01-01"]

    return df


def gold(data_inicio: str, data_fim: str):
    df = silver(data_inicio=data_inicio, data_fim=data_fim)
    salvar_dados_postgres(df)
    logger.success("Pipeline concluído com sucesso!")


if __name__ == "__main__":
    import argparse
    from datetime import date

    parser = argparse.ArgumentParser()
    parser.add_argument("--data-inicio", type=str, default="2024-01-01")
    parser.add_argument("--data-fim", type=str, default=str(date.today()))
    args = parser.parse_args()

    gold(data_inicio=args.data_inicio, data_fim=args.data_fim)
# %%
