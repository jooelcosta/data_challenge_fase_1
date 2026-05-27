# %%
import pandas as pd
from loguru import logger
from services.api import baixar_dados_paginados
import os

def bronze():    
    data = baixar_dados_paginados(endpoint="proposicoes")
    return data

def silver():     

    # Só deve ativar essa linha se ainda não tinha json na pasta
    bronze()

    pasta = './jsons/proposicoes'
    arquivos = os.listdir(pasta)

    dados_acumulados = []

    for arq in arquivos:
        caminho_arquivo = os.path.join(pasta, arq)
        df = pd.read_json(caminho_arquivo) 
        dados_acumulados.append(df)

    df = pd.concat(dados_acumulados, ignore_index=True)    
    return df     


def gold():
    df = silver()
    df.to_excel('proposicoes.xlsx')
    logger.success("Pipeline concluído com sucesso!")


if __name__ == "__main__":    
    gold()


# %%
