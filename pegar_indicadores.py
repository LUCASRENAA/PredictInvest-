import csv
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import yfinance as yf
import re
import time
import random


def extrair_payout(ticker):
    """Extrai o payout ratio de uma ação a partir do Yahoo Finance."""
    url = f"https://finance.yahoo.com/quote/{ticker}.SA/key-statistics/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    payout = 0

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            payout_tags = soup.find_all("td", class_="value yf-vaowmx")
            payout_ratios = [tag.text for tag in payout_tags]

            if len(payout_ratios) >= 47:
                payout = payout_ratios[46]  # O índice 46 corresponde ao 47º elemento
    except Exception as e:
        print(f"Erro ao extrair payout para {ticker}: {e}")

    return payout


def obter_valor_acao_brasileira(ticker):
    """Obtém o valor atual de uma ação brasileira usando o Yahoo Finance."""
    try:
        ticker += '.SA'
        acao = yf.Ticker(ticker)
        dados = acao.history(period='1d')
        valor_atual = dados['Close'].iloc[-1]
        return valor_atual
    except Exception as e:
        print(f"Erro ao obter valor da ação {ticker}: {e}")
        return None


def obter_indicadores(ticket, quantidade):
    """Obtém indicadores financeiros de uma ação a partir de uma página web."""
    url = f'https://www.dadosdemercado.com.br/acoes/{ticket}'
    indicadores = {}

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        ratios = soup.find_all('tr', class_='level0')

        for tr in ratios:
            tds = tr.find_all('td', class_='nw')
            if len(tds) >= 2:
                indicador = tds[0].text.strip()
                valor = tds[1].text.strip()
                valor_convertido = converter_valor_para_float(valor)
                if valor_convertido is not None:
                    indicadores[indicador] = valor_convertido
    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar {url}: {e}")

    return indicadores


def converter_valor_para_float(valor):
    """Converte um valor textual para float, tratando vírgulas e caracteres não numéricos."""
    valor_limpo = ''.join(c if c.isdigit() or c in ['.', ','] else ' ' for c in valor).replace(',', '.')
    try:
        return float(valor_limpo)
    except ValueError:
        return None


def processar_acoes():
    """Processa as ações do arquivo acoes.csv e salva os indicadores no arquivo indicadores.csv."""
    campos_permitidos = [
        'Ticker', 'Quantidade', 'Setor', 'Data de atualização', 'Valor Atual', 'PAYOUT', 'LPA', 'VPA', 'P/L',
        'P/VP', 'P/SR', 'ROE', 'ROA', 'EBITDA', 'Margem bruta', 'Margem líquida', 'Margem EBITDA',
        'Margem operacional', 'P/CF', 'Liquidez corrente', 'Liquidez imediata', 'Liquidez seca', 'Giro do ativo',
        'Endividamento geral', 'Ativo por ação', 'Dívida bruta', 'Dívida líquida', 'Capital de giro',
        'Receita líquida por ação', 'EBIT por ação', 'Margem EBIT'
    ]

    try:
        with open('acoes.csv', newline='', encoding='utf-8') as arquivo_acoes, \
             open('indicadores.csv', mode='w', newline='', encoding='utf-8') as arquivo_indicadores:

            leitor_csv = csv.DictReader(arquivo_acoes)
            escritor_csv = csv.DictWriter(arquivo_indicadores, fieldnames=campos_permitidos)
            escritor_csv.writeheader()

            for linha in leitor_csv:
                processar_linha(linha, escritor_csv, campos_permitidos)

    except FileNotFoundError as e:
        print(f"Erro: Arquivo não encontrado - {e}")
    except Exception as e:
        print(f"Erro inesperado: {e}")


def processar_linha(linha, escritor_csv, campos_permitidos):
    """Processa uma linha do arquivo CSV e escreve os indicadores no arquivo de saída."""
    try:
        ticker = linha.get('Ticker', '').strip()
        quantidade = linha.get('Quantidade', '').strip()
        setor = linha.get('Setor', '').strip()

        if not ticker or not quantidade:
            print(f"Dados inválidos na linha: {linha}")
            return

        print(f"Processando ação: {ticker}")

        # Obtém os indicadores
        indicadores = obter_indicadores(ticker, quantidade)
        valor_acao_brasil = obter_valor_acao_brasileira(ticker)
        payout = extrair_payout(ticker)

        # Aguarda um tempo aleatório entre 5 e 10 segundos
        tempo_aleatorio = random.uniform(5, 10)
        time.sleep(tempo_aleatorio)
        print(f"Aguardei {tempo_aleatorio:.2f} segundos na ação {ticker}.")

        # Monta o dicionário com os dados
        linha_indicadores = {
            'Ticker': ticker,
            'Quantidade': quantidade,
            'Setor': setor,
            'Data de atualização': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Valor Atual': valor_acao_brasil,
            'PAYOUT': payout
        }
        linha_indicadores.update(indicadores)

        # Filtra apenas as chaves permitidas
        linha_filtrada = {k: v for k, v in linha_indicadores.items() if k in campos_permitidos}

        # Escreve no arquivo de saída
        escritor_csv.writerow(linha_filtrada)

    except Exception as e:
        print(f"Erro ao processar a linha {linha}: {e}")


if __name__ == '__main__':
    processar_acoes()