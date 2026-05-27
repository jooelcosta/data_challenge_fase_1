import requests
from loguru import logger
import pandas as pd
from pathlib import Path
import json

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"


def baixar_dados_paginados(endpoint: str):

    url = f"{BASE_URL}/{endpoint}"

    headers = {
        "accept": "application/json",
    }

    def conexao(page: int):

        response = requests.get(
            f"{url}?pagina={page}&itens=100",
            headers=headers
        )

        response.raise_for_status()
        return response.json()

    try:

        primeira_pagina = conexao(1)

        ultima_url = primeira_pagina['links'][-1]['href']

        total_pages = (
            pd.Series([ultima_url])
            .str.extract(r'pagina=(\d+)')[0]
            .iloc[0]
        )

        total_pages = int(total_pages)

        logger.info(f"Total de páginas: {total_pages}")

        pasta_saida = Path(f"./jsons/{endpoint}")
        pasta_saida.mkdir(parents=True, exist_ok=True)

        for page in range(1, total_pages + 1):
        #for page in range(1,2):

            logger.info(f"Baixando página {page}...")

            response = conexao(page)

            dados = response.get("dados", [])

            logger.info(f"Página {page}: {len(dados)} registros.")

            caminho_arquivo = pasta_saida / f"{endpoint}_pagina_{page}.json"

            with open(caminho_arquivo, "w", encoding="utf-8") as f:

                json.dump(
                    dados,
                    f,
                    ensure_ascii=False,
                    indent=4
                )

            logger.success(f"Arquivo salvo: {caminho_arquivo}")

        logger.info("Coleta finalizada.")

    except Exception as e:
        logger.critical(f"Erro crítico ao coletar dados: {e}")


def baixar_dados_paginados_Id(endpoint: str, id: int, complemento: str):

    url = f"{BASE_URL}/{endpoint}/{id}/{complemento}"

    headers = {
        "accept": "application/json",
    }

    def conexao(page: int):

        response = requests.get(
            f"{url}?pagina={page}&itens=100",
            headers=headers
        )

        response.raise_for_status()
        return response.json()

    try:

        primeira_pagina = conexao(1)

        ultima_url = primeira_pagina['links'][-1]['href']

        total_pages = (
            pd.Series([ultima_url])
            .str.extract(r'pagina=(\d+)')[0]
            .iloc[0]
        )

        total_pages = int(total_pages)

        logger.info(f"Total de páginas: {total_pages}")

        pasta_saida = Path(f"./jsons/{complemento}")
        pasta_saida.mkdir(parents=True, exist_ok=True)

        for page in range(1, total_pages + 1):
        #for page in range(1,2):

            logger.info(f"Baixando página {page}...")

            response = conexao(page)

            dados = response.get("dados", [])

            logger.info(f"Página {page}: {len(dados)} registros.")

            caminho_arquivo = pasta_saida / f"{endpoint}_pagina_{page}.json"

            with open(caminho_arquivo, "w", encoding="utf-8") as f:

                json.dump(
                    dados,
                    f,
                    ensure_ascii=False,
                    indent=4
                )

            logger.success(f"Arquivo salvo: {caminho_arquivo}")

        logger.info("Coleta finalizada.")

    except Exception as e:
        logger.critical(f"Erro crítico ao coletar dados: {e}")


# if __name__ == "__main__":

#     baixar_dados_paginados("deputados")

        # resultado = [
    #     {
    #         "Id_Centro_Custo": item.get("id"),
    #         #"Id_Interno": item.get("internalId"),
    #         "Nome_Centro_Custo": item.get("name"),
    #         #"Cnpj": item.get("cnpj"),
    #         #"Id_Empresa": item.get("idCompany"),
    #     }
    #     for item in data
    # ]