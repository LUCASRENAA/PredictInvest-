import pandas as pd
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import calendar
from datetime import datetime
import csv
import statistics
from collections import Counter
from io import StringIO
from main import formatar_data

# Configurações iniciais
Caminho_Arquivo_Acoes = 'acoes.csv'
Caminho_Arquivo_Fiis = 'fiis.csv'
Ano_Atual = datetime.now().year

# Função para limpar e arredondar valores
def limpar_e_arredondar(valor):
    try:
        valor_limpo = str(valor).replace('*', '').replace(',', '.')
        if valor_limpo.count('.') > 1:
            valor_limpo = valor_limpo.split('.')[0] + '.' + valor_limpo.split('.')[1]
        valor_convertido = float(valor_limpo)

        if valor_convertido in {float('inf'), float('-inf')} or valor_convertido != valor_convertido:
            return 0
        return round(valor_convertido, 2)
    except (ValueError, TypeError):
        return 0

# Funções para obter dados de dividendos
def obter_dividendos_acao(ticket, quantidade):
    print(f"Obtendo dividendos da ação: {ticket}")
    url = f'https://www.dadosdemercado.com.br/acoes/{ticket}/dividendos'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    tabela_html = soup.find('table')
    tabela = pd.read_html(StringIO(str(tabela_html)), decimal=',', thousands='.')[0]
    tabela['Pagamento'] = pd.to_datetime(tabela['Pagamento'], format='%d/%m/%Y', errors='coerce')
    
    dados_ano_anterior = tabela[tabela['Pagamento'].dt.year == (Ano_Atual - 1)].copy()

    valores = dados_ano_anterior['Valor'].apply(limpar_e_arredondar)

    dados_ano_anterior['Valor Total'] = valores.apply(lambda x: x * quantidade if x else 0)
    print(f"Dividendos da ação {ticket} para o ano anterior:\n{dados_ano_anterior}")
    return dados_ano_anterior.groupby(dados_ano_anterior['Pagamento'].dt.month)['Valor Total'].sum().fillna(0)

def obter_dividendos_fii(ticket, quantidade):
    print(f"Obtendo dividendos do FII: {ticket}")
    url = f'https://investidor10.com.br/fiis/{ticket}/'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    dividends_table = soup.find('table', {'id': 'table-dividends-history'})
    tabela = pd.read_html(StringIO(str(dividends_table)), decimal=',', thousands='.')[0]
    tabela['Pagamento'] = pd.to_datetime(tabela['Pagamento'], format='%d/%m/%Y', errors='coerce')
    
    dados_ano_anterior = tabela[tabela['Pagamento'].dt.year == (Ano_Atual - 1)].copy()
    dados_ano_anterior['Valor Total'] = dados_ano_anterior['Valor'].apply(lambda x: x * quantidade if x else 0)
    print(f"Dividendos do FII {ticket} para o ano anterior:\n{dados_ano_anterior}")
    return dados_ano_anterior.groupby(dados_ano_anterior['Pagamento'].dt.month)['Valor Total'].sum().fillna(0)

# Função para ler CSV e obter dividendos
def ler_e_obter_dividendos(caminho_arquivo, obter_dividendos_func):
    tickers = []
    previsto_mensal_por_ticket = []

    try:
        with open(caminho_arquivo, 'r') as arquivo_csv:
            leitor_csv = csv.reader(arquivo_csv)
            next(leitor_csv, None)
            for linha in leitor_csv:
                ticket = linha[0]
                quantidade = int(linha[1])
                tickers.append(ticket)
                print(f"Lendo {ticket} com quantidade {quantidade}")
                
                # Obtém os dividendos mensais e garante que todos os meses (1 a 12) estão presentes
                previsto_mensal = obter_dividendos_func(ticket, quantidade)
                
                # Adiciona 0 para os meses que não possuem dividendos
                previsto_mensal_completo = previsto_mensal.reindex(range(1, 13), fill_value=0)
                
                previsto_mensal_por_ticket.append(previsto_mensal_completo)
                print(f"Dividendos para {ticket}: {previsto_mensal_completo}")
                
    except Exception as e:
        print(f'Erro ao processar {caminho_arquivo}: {e}')

    return tickers, previsto_mensal_por_ticket

# Obter dividendos de ações e FIIs
tickers_acoes, previsto_mensal_acoes = ler_e_obter_dividendos(Caminho_Arquivo_Acoes, obter_dividendos_acao)
tickers_fiis, previsto_mensal_fiis = ler_e_obter_dividendos(Caminho_Arquivo_Fiis, obter_dividendos_fii)

print("Dividendos de ações:", previsto_mensal_acoes)
print("Dividendos de FIIs:", previsto_mensal_fiis)

# Combina os dividendos em um único DataFrame
todos_previstos = pd.concat(previsto_mensal_acoes + previsto_mensal_fiis, axis=1)
todos_previstos.columns = tickers_acoes + tickers_fiis

# Renomeia os índices dos meses
meses_ordenados_portugues = [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
]

# Ajuste no reindex para garantir que os meses de 1 a 12 sejam reindexados corretamente
todos_previstos.index = meses_ordenados_portugues

# Limpa e arredonda os valores do DataFrame
print("Antes da limpeza e arredondamento:")
print(todos_previstos.head())
todos_previstos_limpos = todos_previstos.apply(lambda x: x.apply(limpar_e_arredondar)).apply(pd.to_numeric, errors='coerce').fillna(0)
print("Depois da limpeza e arredondamento:")
print(todos_previstos_limpos.head())

# Soma os dividendos de todos os tickers por mês
todos_previstos_limpos['TOTAL'] = todos_previstos_limpos.sum(axis=1)
print("Somatório total dos dividendos por mês:")
print(todos_previstos_limpos['TOTAL'])

# Função para calcular estatísticas
def calcular_estatisticas(data):
    media = statistics.mean(data)
    mediana = statistics.median(data)
    contagem = Counter(data)
    modos = [valor for valor, freq in contagem.items() if freq == contagem.most_common(1)[0][1]]
    moda = modos[0] if len(modos) == 1 else 'No unique mode'
    maximo = max(data)
    minimo = min(data)

    return media, mediana, moda, maximo, minimo

# Estatísticas do total
estatisticas_total = calcular_estatisticas(todos_previstos_limpos['TOTAL'])
print(f"Estatísticas do total de dividendos: {estatisticas_total}")

todos_previstos_limpos = todos_previstos_limpos.drop(columns=['TOTAL'])

# Plotando o gráfico
ax = todos_previstos_limpos.plot(kind='bar', xlabel='Mês', ylabel='Valor Previsto', title=f'Previsão de Dividendos para {Ano_Atual}', legend=True, stacked=True)
ax.set_xticklabels(meses_ordenados_portugues)

# Adiciona estatísticas no gráfico
ax.annotate(f'Média: {estatisticas_total[0]:.2f}\nModa: {estatisticas_total[2]}\nMáximo: {estatisticas_total[3]:.2f}\nMínimo: {estatisticas_total[4]:.2f}',
            xy=(0.97, 0.95), xycoords='axes fraction', fontsize=8, ha='right', va='top')

# Ajusta a posição da legenda
ax.legend(loc='best', bbox_to_anchor=(0, 1))

# Ajusta o tamanho do gráfico
fig = plt.gcf()
fig.set_size_inches(18.5, 10.5)

# Salva o gráfico
data_atual = formatar_data()
plt.savefig(f'arquivos/previsao{data_atual}.png', format='png', bbox_inches='tight')

# Exibe o gráfico
plt.show()
