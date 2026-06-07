# %%
import pandas as pd
from loguru import logger
from services.api import baixar_dados_paginados, baixar_dados_paginados_Id
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DB_URL")

# Cria o engine e a sessão
engine = create_engine(DATABASE_URL, connect_args={"sslmode": "require"})
Session = sessionmaker(bind=engine)


def query_postgres():
    query = "SELECT id FROM deputados"
    df_ids = pd.read_sql(query, engine)

    return df_ids["id"].tolist()


def salvar_dados_postgres(df, tabela: str   ):

    if df.empty:
        logger.warning("DataFrame vazio. Não há dados para salvar.")
        return
    try:
        ano = int(df["ano"].iloc[0])
        mes = int(df["mes"].iloc[0])

        # Busca registros já existentes no banco para o mesmo período
        with engine.connect() as conn:
            existentes = pd.read_sql(
                text(
                    f'SELECT "codDocumento", "idDeputado", "valorDocumento" '
                    f'FROM {tabela} WHERE ano = {ano} AND mes = {mes}'
                ),
                conn
            )

        # Remove do df os registros que já existem no banco
        if not existentes.empty:
            antes = len(df)
            df = df.merge(
                existentes,
                on=["codDocumento", "idDeputado", "valorDocumento"],
                how="left",
                indicator=True
            )
            df = df[df["_merge"] == "left_only"].drop(columns=["_merge"])
            logger.info(f"{antes - len(df)} registros ignorados (já existem no banco).")
 
        if df.empty:
            logger.info("Nenhum registro novo para inserir.")
            return
 
        # Insere apenas os registros novos
        df.to_sql(name=tabela, con=engine, if_exists="append", index=False)
        logger.success(f"{len(df)} registros novos salvos em '{tabela}'!")
 
    except Exception as e:
        logger.error(f"Erro ao salvar dados: {e}")


def bronze(data_inicio: str, data_fim: str):
    ids = query_postgres()
    sucessos = 0
    falhas = 0

    for id_deputado in ids:
        try:
            data = baixar_dados_paginados_Id(
                endpoint="deputados",
                id=id_deputado,
                complemento="despesas",
                data_inicio=data_inicio,
                data_fim=data_fim,
            )
            sucessos += 1
        except Exception as e:
            logger.warning(f"Deputado {id_deputado} - Erro ao baixar dados: {e}")
            falhas += 1
            continue
    logger.info(f"Download concluído: {sucessos} sucessos, {falhas} falhas.")
    return data


def silver(data_inicio: str, data_fim: str):

    # linha necessária de execução apenas em produção
    bronze(data_inicio=data_inicio, data_fim=data_fim)

    pasta = "./jsons/despesas"

    if not os.path.exists(pasta) or not os.listdir(pasta):
        logger.warning("Nenhum arquivo de despesas encontrado.")
        return pd.DataFrame()

    arquivos = os.listdir(pasta)

    dados_acumulados = []

    for arq in arquivos:
        caminho_arquivo = os.path.join(pasta, arq)
        df = pd.read_json(caminho_arquivo)

        if df.empty:  # ← ignora arquivos sem dados
            continue

        try:
            # Tenta extrair o ID do deputado caso esteja no nome do arquivo
            id_deputado = int(arq.split("_")[1])
            df["idDeputado"] = str(id_deputado)
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
    salvar_dados_postgres(df, tabela="despesas")
    logger.success("Pipeline Despesas concluído com sucesso!")


if __name__ == "__main__":
    import argparse
    from datetime import date

    parser = argparse.ArgumentParser()
    parser.add_argument("--data-inicio", type=str, default="2024-01-01")
    parser.add_argument("--data-fim", type=str, default=str(date.today()))
    args = parser.parse_args()

    gold(data_inicio=args.data_inicio, data_fim=args.data_fim)
# %%
