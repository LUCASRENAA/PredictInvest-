import argparse
import subprocess
import investpy as inv
import requests
import os
from datetime import datetime


def formatar_data():
    """Formata a data atual."""
    return datetime.now().strftime("%d-%m-%Y %H %M %S")


def executar_script(script_name):
    """Executa um script Python."""
    subprocess.call(["python3", script_name])


def previsao_dividendos():
    executar_script("previsao_dividendos.py")


def pegar_indicadores():
    executar_script("pegar_indicadores.py")


def algoritmos():
    executar_script("algoritmos.py")


def get_brazilian_stocks():
    """Obtém todas as ações do Brasil."""
    return inv.stocks.get_stocks(country='brazil')


def get_access_token(username, password):
    """Autentica na API e obtém o token de acesso."""
    url = 'http://127.0.0.1:8000/api/token/'
    response = requests.post(url, json={"username": username, "password": password})
    return response.json().get('access') if response.status_code == 200 else None


def create_ticket(access_token, ticket, name):
    """Envia um POST para criar um ticket."""
    url = 'http://127.0.0.1:8000/ticket/'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    body = {"ticket": ticket, "name": name}
    return requests.post(url, headers=headers, json=body)


def processar_stocks_sem_token(brazilian_stocks):
    """Processa as ações e salva em um arquivo CSV quando não há token."""
    for _, stock in brazilian_stocks.iterrows():
        ticket = stock['symbol']
        os.system(f"echo {ticket},, >> acoes_all.csv")


def atualizar_web():
    """Atualiza as ações no sistema web."""
    brazilian_stocks = get_brazilian_stocks()
    username, password = "admin", "admin"

    access_token = get_access_token(username, password)
    if access_token:
        print("Token de Acesso:", access_token)
        for _, stock in brazilian_stocks.iterrows():
            name, ticket = stock['name'], stock['symbol']
            response = create_ticket(access_token, ticket, name)

            if response.status_code == 201:
                print(f"Ticket criado para {name}")
            elif response.status_code == 401:
                print("Token expirado ou inválido. Renovando token...")
                access_token = get_access_token(username, password)
                if access_token:
                    print("Token renovado:", access_token)
                    response = create_ticket(access_token, ticket, name)
                    if response.status_code == 201:
                        print(f"Ticket criado para {name}")
                    else:
                        print(f"Falha ao criar ticket para {name}")
                else:
                    print("Falha ao renovar o token.")
            else:
                print(f"Falha ao criar ticket para {name}: {response.text}")
    else:
        processar_stocks_sem_token(brazilian_stocks)


def main():
    """Função principal para gerenciar os argumentos e executar as opções."""
    parser = argparse.ArgumentParser(
        description="Este programa oferece ferramentas para análise de investimentos, incluindo previsão de dividendos, coleta de indicadores financeiros e execução de algoritmos de avaliação de investimentos.",
        epilog="Para mais informações, consulte a documentação do programa ou entre em contato com o desenvolvedor."
    )

    parser.add_argument("--previsao_dividendos", "-pd", action="store_true", help="Executar a previsão de dividendos.")
    parser.add_argument("--pegar_indicadores", "-pi", action="store_true", help="Coletar os indicadores das ações.")
    parser.add_argument("--algoritmos", "-pa", action="store_true", help="Executar algoritmos de Bazin e Graham.")
    parser.add_argument("--atualizar_web", "-aw", action="store_true", help="Coletar as ações para o sistema web.")
    parser.add_argument("--all", action="store_true", help="Executar todas as opções.")

    args = parser.parse_args()

    if args.all:
        print("Executando todas as opções...")
        previsao_dividendos()
        pegar_indicadores()
        algoritmos()
    else:
        if args.previsao_dividendos:
            previsao_dividendos()
        if args.pegar_indicadores:
            pegar_indicadores()
        if args.algoritmos:
            algoritmos()
        if args.atualizar_web:
            atualizar_web()


if __name__ == "__main__":
    main()
