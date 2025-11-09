import csv
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import yfinance as yf
from yfinance.exceptions import YFRateLimitError 
import time
import random
import re 
import math # Adicionado para usar a função sqrt (raiz quadrada)

# --- Funções de Leitura e Extração ---

def ler_payout_csv(filename='payout.csv'):
    """Lê o arquivo payout.csv e retorna um dicionário {Ticker: Payout_Float}."""
    payouts = {}
    try:
        with open(filename, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ticker = row.get('Ticker', '').strip()
                # Substitui vírgula por ponto e tenta converter para float (porcentagem)
                payout_str = row.get('Payout', '').strip().replace(',', '.')
                try:
                    payouts[ticker] = float(payout_str)
                except ValueError:
                    print(f"Aviso: Valor de Payout inválido para {ticker} no CSV.")
    except FileNotFoundError:
        print(f"Aviso: Arquivo '{filename}' não encontrado.")
    return payouts


def extrair_payout_yf(ticker):
    """
    💰 Extrai o Payout Ratio (em porcentagem) usando a biblioteca yfinance.
    Adiciona '.SA' automaticamente.
    """
    acao = yf.Ticker(ticker + '.SA')
    
    try:
        dados_info = acao.info
    except YFRateLimitError:
        # Re-raise para que processar_linha possa capturar e iniciar o fallback
        raise 
    except Exception as e:
        # Se for qualquer outro erro, retorna a mensagem
        return f"Erro YF: {e}"

    if 'payoutRatio' in dados_info and dados_info['payoutRatio'] is not None:
        payout_ratio = dados_info['payoutRatio'] * 100
        return round(payout_ratio, 2)
    
    return "Não disponível"


def obter_valor_acao_brasileira(ticker):
    """
    Obtém o valor atual de uma ação brasileira usando Web Scraping do Status Invest (sem yfinance).
    """
    url = f"https://statusinvest.com.br/acoes/{ticker}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print(f"Buscando Valor Atual via Web Scraping (Status Invest) para {ticker}...")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # O preço geralmente está dentro de um <strong> com a classe 'value' na div principal
        valor_tag = soup.find('strong', {'class': 'value'})
        
        if valor_tag:
            valor_texto = valor_tag.text.strip()
            # Limpa o texto (remove R$, espaços, converte vírgula para ponto)
            valor_limpo = valor_texto.replace('R$', '').replace('.', '').replace(',', '.').strip()
            
            # Tenta converter para float
            return float(valor_limpo)
        
        print(f"AVISO: Tag de valor não encontrada no Status Invest para {ticker}.")
        return 0.0 # Retorna 0.0 se não encontrar a tag
        
    except requests.exceptions.RequestException as e:
        print(f"Erro de Web Scraping (Status Invest) para {ticker}: {e}")
        return 0.0 # Retorna 0.0 em caso de erro de conexão/HTTP
    except Exception as e:
        print(f"Erro inesperado ao processar o valor de {ticker}: {e}")
        return 0.0 # Retorna 0.0 em caso de erro de processamento


def obter_indicadores(ticket, quantidade):
    """Obtém indicadores financeiros de uma ação a partir de uma página web (Web Scraping)."""
    # Esta função é mantida para web scraping do outro site (dadosdemercado.com.br)
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
                    # Usamos o nome do campo como chave do dicionário
                    indicadores[indicador] = valor_convertido
    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar {url}: {e}")

    return indicadores


def converter_valor_para_float(valor):
    """Converte um valor textual para float, tratando vírgulas e caracteres não numéricos."""
    valor_limpo = valor.replace(' ', '').replace('.', '').replace(',', '.')
    
    # Remove caracteres que não sejam dígitos ou ponto
    valor_limpo = ''.join(c for c in valor_limpo if c.isdigit() or c == '.')

    # Garante que só há um ponto decimal para conversão
    if valor_limpo.count('.') > 1:
        partes = valor_limpo.split('.')
        valor_limpo = ''.join(partes[:-1]) + '.' + partes[-1]
        
    try:
        return float(valor_limpo) if valor_limpo else None
    except ValueError:
        return None

# --- Funções de Cálculo de Valor Intrínseco ---

def calcular_graham(lpa, vpa):
    """Calcula o Valor Intrínseco de Graham: V = sqrt(22.5 * LPA * VPA)"""
    # Constante 22.5: (P/L máximo de 15) * (P/VP máximo de 1.5)
    if lpa is not None and vpa is not None and lpa > 0 and vpa > 0:
        try:
            return round(math.sqrt(22.5 * lpa * vpa), 2)
        except Exception:
            return None
    return None

def calcular_bazin(lpa, payout_percentual):
    """
    Calcula o Preço Justo de Bazin: Preço Justo = DPA / Taxa Desejada (assumimos 6% ou 0.06).
    DPA é aproximado: LPA * (Payout / 100).
    """
    taxa_desejada = 0.06 # 6%
    
    if lpa is not None and payout_percentual is not None and lpa > 0 and payout_percentual > 0:
        try:
            # 1. Calcular Dividendo por Ação (DPA)
            dpa = lpa * (payout_percentual / 100)
            
            # 2. Calcular Preço Justo de Bazin
            preco_justo = dpa / taxa_desejada
            return round(preco_justo, 2)
        except Exception:
            return None
    return None


# --- Funções de Processamento Principal ---

def processar_acoes():
    """Processa as ações do arquivo acoes.csv e salva os indicadores no arquivo indicadores.csv."""
    campos_permitidos = [
        'Ticker', 'Quantidade', 'Setor', 'Data de atualização', 'Valor Atual', 'PAYOUT', 'LPA', 'VPA', 'P/L',
        'P/VP', 'P/SR', 'ROE', 'ROA', 'EBITDA', 'Margem bruta', 'Margem líquida', 'Margem EBITDA',
        'Margem operacional', 'P/CF', 'Liquidez corrente', 'Liquidez imediata', 'Liquidez seca', 'Giro do ativo',
        'Endividamento geral', 'Ativo por ação', 'Dívida bruta', 'Dívida líquida', 'Capital de giro',
        'Receita líquida por ação', 'EBIT por ação', 'Margem EBIT',
        'Valor intrinseco Graham', 'Bazin' # NOVOS CAMPOS ADICIONADOS
    ]

    try:
        # Carrega os payouts do arquivo CSV antes de começar o loop
        payouts_csv = ler_payout_csv()

        with open('acoes.csv', newline='', encoding='utf-8') as arquivo_acoes, \
             open('indicadores.csv', mode='w', newline='', encoding='utf-8') as arquivo_indicadores:

            leitor_csv = csv.DictReader(arquivo_acoes)
            escritor_csv = csv.DictWriter(arquivo_indicadores, fieldnames=campos_permitidos)
            escritor_csv.writeheader()

            for linha in leitor_csv:
                processar_linha(linha, escritor_csv, campos_permitidos, payouts_csv)

    except FileNotFoundError as e:
        print(f"Erro: Arquivo não encontrado - {e}")
    except Exception as e:
        print(f"Erro inesperado: {e}")


def processar_linha(linha, escritor_csv, campos_permitidos, payouts_csv):
    """
    Processa uma linha do arquivo CSV, aplicando a lógica de fallback do Payout.
    """
    ticker = linha.get('Ticker', '').strip()
    quantidade = linha.get('Quantidade', '').strip()
    setor = linha.get('Setor', '').strip()
    valor_acao_brasil = None
    payout = None

    if not ticker or not quantidade:
        print(f"Dados inválidos na linha: {linha}")
        return

    print(f"\n--- Processando ação: {ticker} ---")
    
    # 3. Obtém os Indicadores (Web Scraping - dadosdemercado.com.br)
    indicadores = obter_indicadores(ticker, quantidade)

    # 1. Tenta obter o Valor Atual da Ação (via Web Scraping - Status Invest)
    # Não levanta YFRateLimitError, pois não usa yfinance.
    valor_acao_brasil = obter_valor_acao_brasileira(ticker)
    # Se a função retornar 0.0, é considerado um erro/falha na obtenção do valor.

    # 2. Tenta obter o Payout (via yfinance com fallback)
    try:
        payout = extrair_payout_yf(ticker)
        print(f"✅ PAYOUT obtido via yfinance: {payout}%")
    except YFRateLimitError:
        
        # --- Lógica de Fallback ---
        print(f"\n🛑 RATE LIMIT YF ATINGIDO ao tentar obter o Payout para {ticker}. Iniciando Fallback...")
        
        # Fallback 1: Verificar payout.csv
        if ticker in payouts_csv:
            payout = payouts_csv[ticker]
            print(f"✅ PAYOUT de {ticker} obtido de 'payout.csv': {payout}%.")
        else:
            # Fallback 2: Solicitar input manual
            print(f"❌ Payout de {ticker} não encontrado em 'payout.csv'.")
            while True:
                payout_input = input(f"Por favor, digite o Payout Ratio de {ticker} (em %): ").replace(',', '.')
                try:
                    payout = round(float(payout_input), 2)
                    print(f"👍 Payout de {ticker} definido manualmente para {payout}%.")
                    break
                except ValueError:
                    print("Entrada inválida. Por favor, digite apenas um número (ex: 21.14).")
        # --- Fim da Lógica de Fallback ---
    except Exception as e:
        payout = f"Erro Payout: {e}"


    # 4. Cálculo dos Valores Intrínsecos
    lpa = indicadores.get('LPA')
    vpa = indicadores.get('VPA')
    
    graham = calcular_graham(lpa, vpa)
    # Usa o valor de payout obtido (de yf, csv ou input manual)
    bazin = calcular_bazin(lpa, payout if isinstance(payout, (int, float)) else None)

    # 5. Aguarda um tempo aleatório entre 5 e 10 segundos
    tempo_aleatorio = random.uniform(5, 10)
    time.sleep(tempo_aleatorio)
    print(f"Aguardei {tempo_aleatorio:.2f} segundos antes de continuar.")

    # 6. Monta o dicionário e escreve
    linha_indicadores = {
        'Ticker': ticker,
        'Quantidade': quantidade,
        'Setor': setor,
        'Data de atualização': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'Valor Atual': valor_acao_brasil,
        'PAYOUT': payout,
        'Valor intrinseco Graham': graham, # Novo campo
        'Bazin': bazin                     # Novo campo
    }
    # Atualiza o dicionário com os indicadores raspados (LPA, VPA, P/L, etc.)
    linha_indicadores.update(indicadores)

    # Filtra apenas as chaves permitidas
    linha_filtrada = {k: v for k, v in linha_indicadores.items() if k in campos_permitidos}

    # Escreve no arquivo de saída
    escritor_csv.writerow(linha_filtrada)


if __name__ == '__main__':
    processar_acoes()
    
    print("\nProcessamento concluído.")