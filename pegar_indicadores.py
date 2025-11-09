import csv
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import yfinance as yf
from yfinance.exceptions import YFRateLimitError # Importa a exceção específica
import time
import random

# A biblioteca 'requests' e 'BeautifulSoup' são mantidas pois são usadas
# na função 'obter_indicadores' para web scraping de outro site.
# O 're' não é usado, mas foi mantido na lista de imports do seu código original.
# O 'time' e 'random' são usados para o delay entre as requisições.

def extrair_payout(ticker_simbolo):
    """
    💰 Extrai o Payout Ratio (em porcentagem) de uma ação usando a biblioteca yfinance.

    Args:
        ticker_simbolo (str): O código do ticker da ação (ex: 'PETR4.SA').

    Returns:
        float or str: O Payout Ratio em porcentagem (ex: 55.23) ou uma 
                      mensagem de erro se não for encontrado.
    """
    
    # 1. Cria um objeto Ticker
    acao = yf.Ticker(ticker_simbolo)
    
    # 2. Busca as informações da empresa (dados_info é um dicionário)
    try:
        dados_info = acao.info
    except YFRateLimitError as e:
        # Se atingir o limite de taxa, retransmite a exceção para parar o processamento
        print(f"ERRO: Limite de taxa (Rate Limit) atingido em extrair_payout para {ticker_simbolo}.")
        raise e
    except Exception as e:
        return f"Erro ao acessar dados para {ticker_simbolo}: {e}"

    # 3. Tenta extrair o Payout Ratio do dicionário
    if 'payoutRatio' in dados_info and dados_info['payoutRatio'] is not None:
        payout_ratio = dados_info['payoutRatio']
        
        # Converte para porcentagem e formata
        payout_porcentagem = payout_ratio * 100
        return round(payout_porcentagem, 2)
    else:
        # Retorna uma mensagem clara se o dado não estiver disponível
        return "Não disponível"


def obter_valor_acao_brasileira(ticker):
    """Obtém o valor atual de uma ação brasileira usando o Yahoo Finance."""
    try:
        ticker_completo = ticker + '.SA'
        acao = yf.Ticker(ticker_completo)
        dados = acao.history(period='1d')
        
        # Se os dados estiverem vazios, a ação não foi encontrada ou não tem histórico recente
        if dados.empty:
            raise ValueError(f"Dados vazios para {ticker_completo}. Ticker pode ser inválido.")
            
        valor_atual = dados['Close'].iloc[-1]
        return valor_atual
    except YFRateLimitError as e:
        # Se atingir o limite de taxa, retransmite a exceção para parar o processamento
        print(f"ERRO: Limite de taxa (Rate Limit) atingido em obter_valor_acao_brasileira para {ticker}.")
        raise e
    except Exception as e:
        print(f"Erro ao obter valor da ação {ticker}: {e}")
        return None


def obter_indicadores(ticket, quantidade):
    """Obtém indicadores financeiros de uma ação a partir de uma página web (Web Scraping)."""
    # Esta função usa requests e BeautifulSoup, mantida do seu código original
    # pois busca dados de outro site.
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
    except Exception as e:
        print(f"Erro no scraping de indicadores para {ticket}: {e}")

    return indicadores


def converter_valor_para_float(valor):
    """Converte um valor textual para float, tratando vírgulas e caracteres não numéricos."""
    # Tratamento de valores: remove espaços, substitui vírgula por ponto para float
    valor_limpo = valor.replace(' ', '').replace('.', '').replace(',', '.')
    
    # Remove qualquer caractere que não seja número ou ponto decimal
    valor_limpo = ''.join(c for c in valor_limpo if c.isdigit() or c == '.')

    # Remove pontos extras, mantendo apenas o último para o float
    if valor_limpo.count('.') > 1:
        partes = valor_limpo.split('.')
        valor_limpo = ''.join(partes[:-1]) + '.' + partes[-1]
        
    try:
        return float(valor_limpo) if valor_limpo else None
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
                # O processamento da linha está em um try-except separado
                # para que o Rate Limit Error possa ser retransmitido (re-raised)
                processar_linha(linha, escritor_csv, campos_permitidos)

    except YFRateLimitError:
        # 🛑 Captura o erro específico e interrompe o programa aqui
        print("\n=======================================================")
        print("🛑 EXECUÇÃO INTERROMPIDA: Limite de taxa (Rate Limit) do Yahoo Finance atingido.")
        print("Tente novamente mais tarde para continuar o processamento.")
        print("=======================================================")
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

        # Obtém os indicadores (pode gerar YFRateLimitError)
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

    except YFRateLimitError as e:
        # Retransmite o erro de Rate Limit para que processar_acoes possa capturá-lo
        raise e
    except Exception as e:
        print(f"Erro ao processar a linha {linha}: {e}")


if __name__ == '__main__':
    # Simula a criação de um arquivo acoes.csv para o código ser executável
    # Em um ambiente real, você deve ter seu próprio arquivo.
    acoes_mock = [
        {'Ticker': 'PETR4', 'Quantidade': '100', 'Setor': 'Petróleo'},
        {'Ticker': 'VALE3', 'Quantidade': '50', 'Setor': 'Mineração'},
        {'Ticker': 'ITUB4', 'Quantidade': '200', 'Setor': 'Bancos'},
    ]
    with open('acoes.csv', mode='w', newline='', encoding='utf-8') as f:
        fieldnames = ['Ticker', 'Quantidade', 'Setor']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(acoes_mock)
        
    print("Arquivo 'acoes.csv' mock criado. Iniciando processamento...")
    
    processar_acoes()
    
    print("Processamento concluído ou interrompido.")