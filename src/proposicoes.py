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


def salvar_dados_postgres(df, tabela: str, chave_primaria: str):

    if df.empty:
        logger.warning("DataFrame vazio. Não há dados para salvar.")
        return
    try:
        df.to_sql(name=f"_temp_{tabela}", con=engine, if_exists="replace", index=False)

        colunas = ", ".join([f'"{col}"' for col in df.columns])
        update = ", ".join(
            [
                f'"{col}" = EXCLUDED."{col}"'
                for col in df.columns
                if col != chave_primaria
            ]
        )

        with engine.begin() as conn:
            conn.execute(f"""
                INSERT INTO {tabela} ({colunas})
                SELECT {colunas} FROM _temp_{tabela}
                ON CONFLICT ({chave_primaria}) DO UPDATE SET {update};
                
                DROP TABLE _temp_{tabela};
            """)

        logger.success(f"{len(df)} registros salvos com sucesso na tabela {tabela}!")

    except Exception as e:
        logger.error(f"Erro ao salvar dados: {e}")


def bronze(data_inicio: str, data_fim: str):
    data = baixar_dados_paginados(
        endpoint="proposicoes", data_inicio=data_inicio, data_fim=data_fim
    )
    return data


def silver(data_inicio: str, data_fim: str):

    # linha necessária de execução apenas em produção
    bronze(data_inicio=data_inicio, data_fim=data_fim)

    pasta = "./jsons/proposicoes"
    arquivos = os.listdir(pasta)

    dados_acumulados = []

    for arq in arquivos:
        caminho_arquivo = os.path.join(pasta, arq)
        df = pd.read_json(caminho_arquivo)
        dados_acumulados.append(df)

    df = pd.concat(dados_acumulados, ignore_index=True)

    # Deduplicação pela chave primária
    df = df.drop_duplicates(subset=["id"], keep="last")

    # Validação: campos obrigatórios
    df = df.dropna(subset=["id", "ementa"])

    # Conversão de datas e filtro de range válido (ex: a partir de 1988)
    df["dataApresentacao"] = pd.to_datetime(df["dataApresentacao"], errors="coerce")
    df = df.dropna(subset=["dataApresentacao"])
    df = df[df["dataApresentacao"] >= "1988-01-01"]

    return df


def gold(data_inicio: str, data_fim: str):
    df = silver(data_inicio=data_inicio, data_fim=data_fim)
    salvar_dados_postgres(df, tabela="proposicoes", chave_primaria="id")
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
