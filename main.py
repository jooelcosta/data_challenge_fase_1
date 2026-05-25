from config import API_BASE_URL, TABLES_CONFIG

import requests

def dados_api(table_key):
    url = f"{API_BASE_URL}{TABLES_CONFIG[table_key]['endpoint']}"
    params = {"itens": "2"}
    try:
        requisicao = requests.get(url, params, timeout=10)
        if requisicao.status_code == 200:
            print("Requisicao realizada com sucesso")
            try:
                conteudo = requisicao.json()
                print(conteudo.get("dados", "Chave 'dados' não encontrada"))
            except requests.exceptions.JSONDecodeError as e:
                print(f"Erro ao processar o JSON: {e}")
        else:
            print(f"Erro na requisição: {requisicao.status_code}")
            try:
                retorno_erro = requisicao.json()
                print(
                    "Detalhe erro:",
                    retorno_erro.get("detail", "Sem detalhes adicionais"),
                )
            except:
                print("Resposta de erro não é um JSON válido")
                print("Resposta de erro:", requisicao.text)
    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar a API: {e}")

def processa_tabela(table_key):
    print(f"Processando tabela: {TABLES_CONFIG[table_key]['table_name']}")
    dados_api(table_key)

def main():
    for table_key in TABLES_CONFIG.keys():
        processa_tabela(table_key)

if __name__ == "__main__":
    main()