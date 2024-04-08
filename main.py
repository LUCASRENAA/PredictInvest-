import argparse
import subprocess
import yfinance as yf
import pandas as pd
import investpy as inv
import requests
import argparse
import subprocess
import csv
def formatar_data():
    import datetime

    data_atual = datetime.datetime.now()
    data_formatada = data_atual.strftime("%d-%m-%Y %H %M %S")
    #print("Data atual:", data_formatada)
    return data_formatada


def previsao_dividendos():
    subprocess.call(["python", "previsao_dividendos.py"])

def pegar_indicadores():
    subprocess.call(["python", "pegar_indicadores.py", "acoes.csv", "indicadores.csv"])

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
    for ticket in tickets:
        if ticket['ticket'] == ticker:
            return ticket['id']
    return None


# Função para enviar os indicadores para o servidor
def enviar_indicadores(access_token, ticket_id, indicadores):
    url = f'http://127.0.0.1:8000/ticket_atualizacao/'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    response = requests.post(url, headers=headers, json=indicadores)
    return response

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

def atualizar_indicadores():
    tickers = obter_acoes_brasileiras()
    print(tickers)
    # Gera o arquivo CSV com os tickers das ações
    gerar_arquivo_acoes(tickers, 'acoes2.csv')
    print("gerar aqui")

    subprocess.call(["python", "pegar_indicadores.py", "acoes2.csv", "indicadores2.csv"])

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
            "valor_atual": "valor_atual",
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
            "ticket": "ticket"
        }
        # Itera sobre as linhas do DataFrame de indicadores

        import csv
        import math
        from datetime import datetime
        from main import formatar_data
        def calcular_valor_intrinseco(lpa, vpa):
                    multiplicador = 12
                    valor_intrinseco = math.sqrt(multiplicador * lpa * vpa)
                    return valor_intrinseco

        def calcular_bazin(lpa,payout):
                    return (lpa*payout/100)/0.07       
        for index, indicador in indicadores_df.iterrows():




            
                ticker = indicador['Ticker']
                ticket_id = find_ticket_id(tickets, ticker)
                if ticket_id is None:
                    print(f"Não foi possível encontrar o ticket para a ação {ticker}")
                    continue
                print(ticket_id)
                indicador['ticket'] = ticket_id
                indicador = indicador.fillna(0)

                # Remover o símbolo '%' e substituir a vírgula por um ponto
                try:
                    string_numero = indicador['PAYOUT'].replace(',', '.')
                    numero = float(string_numero[:-1]) / 100  # Remove o símbolo '%' e divide por 100
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
    parser.add_argument("--atualizar_indicadores", "-ai", action="store_true", help="Coletar os indicadores das ações para o sitema web.")

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
        elif args.atualizar_indicadores:
            print("Enviando as ações para o banco de dados web...")

            atualizar_indicadores()


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


