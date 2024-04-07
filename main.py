import argparse
import subprocess
import yfinance as yf
import pandas as pd
import investpy as inv
import requests


def formatar_data():
    import datetime

    data_atual = datetime.datetime.now()
    data_formatada = data_atual.strftime("%d-%m-%Y %H %M %S")
    #print("Data atual:", data_formatada)
    return data_formatada


def previsao_dividendos():
    subprocess.call(["python", "previsao_dividendos.py"])

def pegar_indicadores():
    subprocess.call(["python", "pegar_indicadores.py"])

def algoritmos():
    subprocess.call(["python", "algoritmos.py"])

def atualizar_web():
# Obtém todas as ações do Brasil
    brazilian_stocks = get_brazilian_stocks()

    # Autentica na API e obtém o token de acesso
    username = "admin"
    password = "admin"
    access_token = get_access_token(username, password)

    if access_token:
        print("Token de Acesso:", access_token)
        # Percorre as ações do Brasil e cria um ticket para cada uma
        for stock in brazilian_stocks.iterrows():
            #print(stock)
            name = stock[1]['name']
            ticket = stock[1]['symbol']
            #print(stock[1])
            #print(name)
            #print(ticket)
            response = create_ticket(access_token,ticket, name)
            if response.status_code == 201:
                print(f"Ticket criado para {name}")
            elif response.status_code == 401:
                print("Token expirado ou inválido. Renovando token...")
                access_token = get_access_token(username, password)
                if access_token:
                    print("Token renovado:", access_token)
                    # Tenta criar o ticket novamente com o novo token
                    response = create_ticket(access_token,ticket, name)
                    if response.status_code == 201:
                        print(f"Ticket criado para {name}")
                    else:
                        print(f"Falha ao criar ticket para {name}")
                else:
                    print("Falha ao renovar o token.")
            else:
                print(f"Falha ao criar ticket para {name}: {response.text}")
    else:
        print("Falha na autenticação.")
        
def main():
    # Criação do parser de argumentos
    parser = argparse.ArgumentParser(
    description="Este programa oferece ferramentas para análise de investimentos, incluindo previsão de dividendos, coleta de indicadores financeiros e execução de algoritmos de avaliação de investimentos.",
    epilog="Para mais informações, consulte a documentação do programa ou entre em contato com o desenvolvedor."
)



    # Adiciona argumento para execução da previsão de dividendos
    parser.add_argument("--previsao_dividendos", "-pd", action="store_true", help="Executar a previsão de dividendos. Antes de executar esta opção, certifique-se de ter os seguintes arquivos: acoes.csv e/ou fiis.csv.")

    # Adiciona argumento para execução da coleta de indicadores
    parser.add_argument("--pegar_indicadores", "-pi", action="store_true", help="Coletar os indicadores das ações.")

    # Adiciona argumento para execução dos algoritmos de Bazin e Graham nos indicadores
    parser.add_argument("--algoritmos", "-pa", action="store_true", help="Executar algoritmos de Bazin e Graham nos indicadores coletados. Para Bazin foi utilizado essa formula (lpa*payout/100)/0.07, para Graham foi utilizado (12 * lpa * vpa) e para o metodo nathalia foi feito a média dos dois algoritmos anteriores")

    parser.add_argument("--atualizar_web", "-aw", action="store_true", help="Coletar as ações para o sitema web.")

    # Adiciona argumento para executar todas as opções
    parser.add_argument("--all", action="store_true", help="Executar todas as opções: previsão de dividendos, coleta de indicadores e execução dos algoritmos.")

    # Realiza o parsing dos argumentos da linha de comando
    args = parser.parse_args()

    # Verifica se a opção -all foi fornecida
    if args.all:
        print("Executando todas as opções...")
        print("Previsão de dividendos...\n\n")
        previsao_dividendos()
        print("Coletando indicadores...\n\n")

        pegar_indicadores()
        print("Realizando calculos...\n\n")
        algoritmos()
    else:
        # Verifica se o argumento de previsão de dividendos foi fornecido
        if args.previsao_dividendos:
            previsao_dividendos()
        elif args.pegar_indicadores:
            print("Coletando indicadores das ações...")
            pegar_indicadores()
        elif args.algoritmos:
            print("Executando algoritmos de Bazin e Graham nos indicadores...")
            algoritmos()
        elif args.atualizar_web:
            print("Enviando as ações para o banco de dados web...")

            atualizar_web()


# Função para obter todas as ações do Brasil
def get_brazilian_stocks():
    br = inv.stocks.get_stocks(country='brazil')
    return br

# Função para autenticar na API e obter o token de acesso
def get_access_token(username, password):
    url = 'http://127.0.0.1:8000/api/token/'
    body = {
        "username": username,
        "password": password
    }
    response = requests.post(url, json=body)
    if response.status_code == 200:
        return response.json().get('access')
    else:
        return None


# Função para enviar um POST para criar um ticket
def create_ticket(access_token, ticket,name):
    url = 'http://127.0.0.1:8000/ticket/'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    body = {
        "ticket": ticket,
        "name": name
    }
    response = requests.post(url, headers=headers, json=body)
    return response
if __name__ == "__main__":
    
   
    
    main()


