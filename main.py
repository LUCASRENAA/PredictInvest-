import argparse
import subprocess
import investpy as inv
import requests
import os
from datetime import datetime
import csv

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

# Função para obter todos os tickets do servidor
def get_tickets(access_token):
    url = 'http://127.0.0.1:8000/ticket/'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Função para encontrar o ID do ticket com base no nome da ação (ticker)
def find_ticket_id(tickets, ticker):
    print(tickets)
    print("alo")
    print(ticker)
    for ticket in tickets:
        if ticket['ticket_id'] == ticker:
            return ticket['id']
    return None

def obter_acoes_brasileiras():
    # Obtém todas as ações do Brasil
    brazilian_stocks = inv.stocks.get_stocks(country='brazil')

    # Retorna apenas os tickers das ações
    tickers = brazilian_stocks['symbol'].tolist()

    return tickers

def gerar_arquivo_acoes(tickers, nome_arquivo):
    # Abre o arquivo CSV para escrita
    with open(nome_arquivo, mode='w', newline='', encoding='utf-8') as arquivo_csv:
        # Define os campos do cabeçalho
        campos = ['Ticker', 'Quantidade', 'Setor']
        
        # Cria o escritor CSV
        escritor_csv = csv.DictWriter(arquivo_csv, fieldnames=campos)

        # Escreve o cabeçalho no arquivo CSV
        escritor_csv.writeheader()

        # Itera sobre os tickers das ações
        for ticker in tickers:
            

            # Escreve os dados no arquivo CSV
            escritor_csv.writerow({'Ticker': ticker, 'Quantidade': 100, 'Setor': ""})
# Função para enviar os indicadores para o servidor
def enviar_indicadores(access_token, ticket_id, indicadores):
    url = f'http://127.0.0.1:8000/ticket_atualizacao/'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    response = requests.post(url, headers=headers, json=indicadores)
    return response
    
    
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
    body = {"ticket_id": ticket, "name": name}
    return requests.post(url, headers=headers, json=body)


def atualizar_indicadores():
    tickers = obter_acoes_brasileiras()
    print(tickers)
    # Gera o arquivo CSV com os tickers das ações
    gerar_arquivo_acoes(tickers, 'acoes2.csv')
    print("gerar aqui")
    import pandas as pd

    #subprocess.call(["python", "pegar_indicadores.py", "acoes2.csv", "indicadores2.csv"])

    username = "admin"
    password = "admin"
    access_token = get_access_token(username, password)

    if access_token:
        print("Token de Acesso:", access_token)

        # Obtém todos os tickets do servidor
        tickets = get_tickets(access_token)
        if not tickets:
            print("Falha ao obter os tickets do servidor.")
            return

        # Carrega os indicadores do arquivo CSV
        indicadores_df = pd.read_csv("indicadores2.csv")
        # Mapeamento entre os campos do CSV e os campos da API
        mapeamento = {
            "Valor Atual": "valor_atual",
            "PAYOUT": "payout",
            "LPA": "lpa",
            "VPA": "vpa",
            "P/L": "pl",
            "P/VP": "pvp",
            "P/SR": "psr",
            "ROE": "roe",
            "ROA": "roa",
            "EBITDA": "EBITDA",
            "Margem bruta": "margem_bruta",
            "Margem líquida": "margem_liquida",
            "Margem EBITDA": "margem_ebitda",
            "Margem operacional": "margem_operacional",
            "P/CF": "pcf",
            "Liquidez corrente": "liquidez_corrente",
            "Liquidez imediata": "liquidez_imediata",
            "Liquidez seca": "liquidez_seca",
            "Giro do ativo": "giro_ativo",
            "Endividamento geral": "endividamento_geral",
            "Ativo por ação": "ativo_acao",
            "Dívida bruta": "divida_bruta",
            "Dívida líquida": "divida_liquida",
            "Capital de giro": "capital_giro",
            "Receita líquida por ação": "receita_liquida",
            "EBIT por ação": "ebit_acao",
            "Margem EBIT": "margem_ebit",
            "ticket_id": "ticket",
            "bazin": "bazin",
            "grahan": "grahan"
        }
        # Itera sobre as linhas do DataFrame de indicadores

        import csv
        import math
        from datetime import datetime
        from main import formatar_data
        def calcular_valor_intrinseco(lpa, vpa):
                    multiplicador = 22
                    valor_intrinseco = math.sqrt(multiplicador * lpa * vpa)
                    return valor_intrinseco

        def calcular_bazin(lpa,payout):
                    return (lpa*payout/100)/0.06   
        for index, indicador in indicadores_df.iterrows():




            
                ticker = indicador['Ticker']
                ticket_id = find_ticket_id(tickets, ticker)
                if ticket_id is None:
                    print(f"Não foi possível encontrar o ticket para a ação {ticker}")
                    continue
                print(ticket_id)
                indicador['ticket_id'] = ticket_id
                indicador = indicador.fillna(0)

                # Remover o símbolo '%' e substituir a vírgula por um ponto
                try:
                    string_numero = indicador['PAYOUT'].replace(',', '.')
                    numero = float(string_numero[:-1])   # Remove o símbolo '%' e divide por 100
                    indicador['PAYOUT'] = numero
                except:
                    pass
                indicador['grahan'] = calcular_valor_intrinseco(float(indicador['LPA']),float(indicador['VPA']))
                try:
                    indicador['bazin'] = calcular_bazin(float(indicador['LPA']),float(indicador['PAYOUT']))
                except:
                    pass

                #print(indicador)
                # Arredonda todos os valores no dicionário indicador para duas casas decimais

                indicadores = {mapeamento[chave_csv]: valor for chave_csv, valor in indicador.items() if chave_csv in mapeamento}
                print(indicadores)
                # Converte a linha para um dicionário de indicadores
                # Arredonda todos os valores no dicionário indicador para duas casas decimais
                for chave, valor in indicadores.items():
                    if isinstance(valor, (int, float)):
                        indicadores[chave] = round(valor, 2)
                response = enviar_indicadores(access_token, ticket_id, indicadores)


                

                if response.status_code == 201:
                    print(f"Indicadores atualizados para o ticket {ticket_id}")
                elif response.status_code == 401:
                    print("Token expirado ou inválido.")
                else:
                    print(f"Falha ao atualizar indicadores para o ticket {ticket_id}: {response.text}")
            
    else:
        print("Falha na autenticação.")

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
                        print(f"Falha ao criar ticket para {name} com ticket {ticket}")
                else:
                    print("Falha ao renovar o token.")
            else:
                print(f"Falha ao criar ticket para {name}: {response.text} com {ticket}")
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
    parser.add_argument("--atualizar_indicadores", "-ai", action="store_true", help="Coletar os indicadores das ações para o sitema web.")

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
        if args.atualizar_indicadores:
            print("Enviando as ações para o banco de dados web...")

            atualizar_indicadores()


if __name__ == "__main__":
    main()
