import requests
from loguru import logger
import pandas as pd
from pathlib import Path
import json

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"


def baixar_dados_paginados(endpoint: str, data_inicio: str, data_fim: str):

    url = f"{BASE_URL}/{endpoint}"

    headers = {
        "accept": "application/json",
    }

    def conexao(page: int):

        params = {
            "pagina": page,
            "itens": 100,
            "dataInicio": data_inicio,
            "dataFim": data_fim,
        }

        response = requests.get(
            # f"{url}?pagina={page}&itens=100",
            url=url,
            params=params,
            headers=headers,
            timeout=30,
        )

        response.raise_for_status()
        return response.json()

    try:

        primeira_pagina = conexao(1)

        if not primeira_pagina.get("dados"):
            logger.info(f"Nenhum dado encontrado em '{endpoint}' para o período.")
            return
 
        # Verifica se existe link 'last' com total de páginas
        links = primeira_pagina.get("links", [])
        ultima_url = links[-1]["href"]
        total_pages_match = (
            pd.Series([ultima_url]).str.extract(r"pagina=(\d+)")[0].iloc[0]
        )
 
        # CORREÇÃO: se só há 1 página, str.extract pode pegar pagina=1 do self
        # Verifica se o link final é realmente diferente do self
        total_pages = int(total_pages_match) if not pd.isna(total_pages_match) else 1
 
        logger.info(f"Total de páginas: {total_pages}")

        pasta_saida = Path(f"./jsons/{endpoint}")
        pasta_saida.mkdir(parents=True, exist_ok=True)

        for page in range(1, total_pages + 1):
            # for page in range(2):

            logger.info(f"Baixando página {page}...")

            response = conexao(page)

            dados = response.get("dados", [])

            logger.info(f"Página {page}: {len(dados)} registros.")

            caminho_arquivo = pasta_saida / f"{endpoint}_pagina_{page}.json"

            with open(caminho_arquivo, "w", encoding="utf-8") as f:

                json.dump(dados, f, ensure_ascii=False, indent=4)

            logger.success(f"Arquivo salvo: {caminho_arquivo}")

        logger.info("Coleta finalizada.")

    except Exception as e:
        logger.critical(f"Erro crítico ao coletar dados: {e}")


def baixar_dados_paginados_Id(
    endpoint: str, id: int, complemento: str, data_inicio: str, data_fim: str
):

    url = f"{BASE_URL}/{endpoint}/{id}/{complemento}"

    headers = {
        "accept": "application/json",
    }

    def conexao(page: int):

        ano = data_inicio[:4]
        mes = data_inicio[5:7]

        params = {
            "pagina": page,
            "itens": 15,
            "ano": ano,
            "mes": mes,
        }

        response = requests.get(
            url=url,
            params=params,
            headers=headers,
            timeout=30
        )

        response.raise_for_status()
        return response.json()

    try:

        primeira_pagina = conexao(1)

        if not primeira_pagina.get("dados"):
            logger.info(f"Deputado {id}: sem despesas no período.")
            return
 
        links = primeira_pagina.get("links", [])
        ultima_url = links[-1]["href"]
        total_pages_match = (
            pd.Series([ultima_url]).str.extract(r"pagina=(\d+)")[0].iloc[0]
        )
        total_pages = int(total_pages_match) if not pd.isna(total_pages_match) else 1
 
        logger.info(f"Deputado {id}: {total_pages} página(s).")

        pasta_saida = Path(f"./jsons/{complemento}")
        pasta_saida.mkdir(parents=True, exist_ok=True)

        for page in range(1, total_pages + 1):
            # for page in range(1,2):

            logger.info(f"Baixando página {page}...")

            response = conexao(page)

            dados = response.get("dados", [])

            logger.info(f"Página {page}: {len(dados)} registros.")

            caminho_arquivo = (
                pasta_saida / f"{endpoint}_{id}_{complemento}_pagina_{page}.json"
            )

            with open(caminho_arquivo, "w", encoding="utf-8") as f:

                json.dump(dados, f, ensure_ascii=False, indent=4)

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
