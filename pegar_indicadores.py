import csv
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import re
def extrair_payout(ticker):
    url = f"https://br.financas.yahoo.com/quote/{ticker}.SA/key-statistics?p={ticker}.SA"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    response = requests.get(url, headers=headers)
    # Faça a solicitação HTTP para obter o conteúdo da página

    # Verifique se a solicitação foi bem-sucedida (código de status 200)
    if response.status_code == 200:
        # Use BeautifulSoup para analisar o HTML da página
        soup = BeautifulSoup(response.content, 'html.parser')

        # Encontre todas as tags td com a classe específica
        payout_tags = soup.find_all("td", class_="Fw(500) Ta(end) Pstart(10px) Miw(60px)")

        # Extraia o texto de cada tag
        payout_ratios = [tag.text for tag in payout_tags]

        # Imprima os resultados
        for i, payout_ratio in enumerate(payout_ratios, start=1):
            if i == 34:
                print(f'O Payout Ratio {i} da empresa é: {payout_ratio}')
                payout = payout_ratio
            #print(f'O Payout Ratio {i} da empresa é: {payout_ratio}')
            #payout = payout_ratio
    else:
        print(f'Erro ao acessar a página. Código de status: {response.status_code}')
    return payout
def obter_valor_acao_brasileira(ticker):
    try:
        # Adicionando '.SA' ao final do ticker para representar a Bovespa
        ticker += '.SA'

        # Criar um objeto Ticker
        acao = yf.Ticker(ticker)

        # Obter dados históricos
        dados = acao.history(period='1d')

        # Retornar o valor mais recente
        valor_atual = dados['Close'].iloc[-1]
        return valor_atual

    except Exception as e:
        print(f"Erro ao obter valor da ação {ticker}: {e}")
        return None
    

def obter_indicadores(ticket, quantidade):
    url = f'https://www.dadosdemercado.com.br/bolsa/acoes/{ticket}'
    response = requests.get(url)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')

    indicadores = {}

    # Encontrar os elementos com a classe "ratio"
    ratios = soup.find_all(class_='ratio')

    for ratio in ratios:
        span_tags = ratio.find_all('span')
        if len(span_tags) >= 2:
            indicador = span_tags[0].text.strip()
            valor = span_tags[1].text.strip()

            # Trata o valor para remoção de caracteres não numéricos e conversão para float
            valor_convertido = converter_valor_para_float(valor)
            
            # Armazena o valor no dicionário de indicadores
            indicadores[indicador] = valor_convertido

    return indicadores

def converter_valor_para_float(valor):
    # Remove espaços e outros caracteres não numéricos, substitui vírgulas por pontos
    valor_limpo = ''.join(c if c.isdigit() or c in ['.', ','] else ' ' for c in valor).replace(',', '.')
    try:
        # Tenta converter para float
        return float(valor_limpo)
    except ValueError:
        # Caso não seja possível converter, retorna None
        return None

# Função para ler o arquivo acoes.csv e escrever em indicadores.csv
def processar_acoes():
    # Abrir o arquivo acoes.csv para leitura
    with open('acoes.csv', newline='', encoding='utf-8') as arquivo_acoes:
        leitor_csv = csv.DictReader(arquivo_acoes)
        
        # Abrir o arquivo indicadores.csv para escrita
        with open('indicadores.csv', mode='w', newline='', encoding='utf-8') as arquivo_indicadores:
            campos = ['Ticker', 'Quantidade', 'Setor', 'Data de atualização', 'Valor Atual', 'PAYOUT', 'LPA', 'VPA', 'P/L', 'P/VP', 'P/SR', 'ROE', 'ROA', 'EBITDA', 'Margem bruta', 'Margem líquida', 'Margem EBITDA', 'Margem operacional', 'P/CF', 'Liquidez corrente', 'Liquidez imediata', 'Liquidez seca', 'Giro do ativo', 'Endividamento geral', 'Ativo por ação', 'Dívida bruta', 'Dívida líquida', 'Capital de giro', 'Receita líquida por ação', 'EBIT por ação', 'Margem EBIT']
            escritor_csv = csv.DictWriter(arquivo_indicadores, fieldnames=campos)

            # Escrever o cabeçalho no arquivo indicadores.csv
            escritor_csv.writeheader()

            # Iterar sobre as linhas do arquivo acoes.csv
            for linha in leitor_csv:
                ticker = linha['Ticker']
                quantidade = linha['Quantidade']
                setor = linha['Setor']

                # Obter indicadores usando a função
                indicadores = obter_indicadores(ticker, quantidade)
                valor_acao_brasil = obter_valor_acao_brasileira(ticker)
                print(ticker)
                #print(extrair_payout(ticker))

               
                # Escrever os dados no arquivo indicadores.csv
                linha_indicadores = {
                    'Ticker': ticker,
                    'Quantidade': quantidade,
                    'Setor': setor,
                    'Data de atualização': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'Valor Atual': valor_acao_brasil,
                    'PAYOUT': extrair_payout(ticker)

                }
                linha_indicadores.update(indicadores)
                escritor_csv.writerow(linha_indicadores)

if __name__ == '__main__':
    processar_acoes()