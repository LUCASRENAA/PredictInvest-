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

# Substitua 'seu_arquivo_acoes.csv' e 'seu_arquivo_fiis.csv' pelos caminhos dos seus arquivos CSV
caminho_arquivo_acoes = 'acoes.csv'
caminho_arquivo_fiis = 'fiis.csv'
ano_atual = datetime.now().year

# Função para obter dados de dividendos de ações
def obter_dividendos_acao(ticket, quantidade):
    url = f'https://www.dadosdemercado.com.br/bolsa/acoes/{ticket}/dividendos'
    response = requests.get(url)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    tabela_html = soup.find('table')
    tabela = pd.read_html(StringIO(str(tabela_html)), decimal=',', thousands='.')[0]
    tabela['Pagamento'] = pd.to_datetime(tabela['Pagamento'], format='%d/%m/%Y', errors='coerce')
    dados_ano_anterior = tabela[tabela['Pagamento'].dt.year == (ano_atual - 1)].copy()

    dados_ano_anterior.loc[:, 'Valor Total'] = dados_ano_anterior['Valor'] * quantidade
    return dados_ano_anterior.groupby(dados_ano_anterior['Pagamento'].dt.month)['Valor Total'].sum()

# Função para obter dados de dividendos de FIIs
def obter_dividendos_fii(ticker,quantidade):
    quantidade = float(quantidade)
    url = f'https://investidor10.com.br/fiis/{ticker}/'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    response = requests.get(url, headers=headers)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    dividends_table = soup.find('table', {'id': 'table-dividends-history'})
    table_data = pd.read_html(StringIO(str(dividends_table)), decimal=',', thousands='.')[0]
    table_data['Pagamento'] = pd.to_datetime(table_data['Pagamento'], format='%d/%m/%Y', errors='coerce')
    dados_ano_anterior = table_data[table_data['Pagamento'].dt.year == (ano_atual - 1)].copy()
    lista = [quantidade,quantidade,quantidade,quantidade,quantidade,quantidade,quantidade,quantidade,quantidade,quantidade,quantidade,quantidade]
    dados_ano_anterior.loc[:, 'Valor Total'] = dados_ano_anterior['Valor'].mul(lista)
    # Multiplicando a Série 'Valor' pela quantidade
    
    return dados_ano_anterior.groupby(dados_ano_anterior['Pagamento'].dt.month)['Valor Total'].sum()

# Lista para armazenar os tickers
tickers_acoes = []
tickers_fiis = []

# Lista para armazenar os DataFrames de previsões mensais
previsto_mensal_por_ticket = []

try:
    # Lê o arquivo de ações
    with open(caminho_arquivo_acoes, 'r') as arquivo_csv:
        leitor_csv = csv.reader(arquivo_csv)
        next(leitor_csv, None)

        for linha in leitor_csv:
            acao = linha[0]
            quantidade = int(linha[1])
            tickers_acoes.append(acao)
            previsto_mensal_acao = obter_dividendos_acao(acao, quantidade)
            previsto_mensal_por_ticket.append(previsto_mensal_acao)
except:
    pass

try:
    # Lê o arquivo de FIIs
    with open(caminho_arquivo_fiis, 'r') as arquivo_csv:
        leitor_csv = csv.reader(arquivo_csv)
        next(leitor_csv, None)

        for linha in leitor_csv:
            fii = linha[0]

            quantidadde = linha[1]

            tickers_fiis.append(fii)
            previsto_mensal_fii = obter_dividendos_fii(fii,quantidadde)
            previsto_mensal_por_ticket.append(previsto_mensal_fii)
except:
    pass
# Combina os DataFrames de previsões mensais em um único DataFrame
if 1 == 1:
    previsto_mensal_total = pd.concat(previsto_mensal_por_ticket, axis=1)
    previsto_mensal_total.columns = tickers_acoes + tickers_fiis



    import pandas as pd
    from bs4 import BeautifulSoup
    import requests
    from datetime import datetime
    import calendar
    import statistics
    from collections import Counter
    import matplotlib.pyplot as plt
    # Renomeia os índices (números dos meses) para os nomes dos meses
    previsto_mensal_total.index = [calendar.month_name[i] for i in previsto_mensal_total.index]

    # Cria uma lista de meses ordenados, com dezembro como o último mês
    meses_ordenados = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]
    meses_ordenados_portugues = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]

    # Reordena os meses do DataFrame de acordo com a ordem dos meses do calendário
    previsto_mensal_total = previsto_mensal_total.reindex(meses_ordenados)

    # Adicione esta linha para criar uma cópia do DataFrame original
    previsto_mensal_total_com_total = previsto_mensal_total.copy()

    # Soma total de cada linha (mês) e adiciona como uma nova coluna chamada 'TOTAL'
    previsto_mensal_total_com_total['TOTAL'] = previsto_mensal_total_com_total.sum(axis=1)

    # Exibe o DataFrame com a nova coluna
    print(previsto_mensal_total_com_total)

    # Restante do seu código para calcular estatísticas, plotar gráficos etc.


    # Calcula estatísticas para todos os meses, incluindo a nova coluna 'TOTAL'
    estatisticas_por_mes_com_total = pd.DataFrame(index=['Média', 'Mediana', 'Moda', 'Máximo', 'Mínimo'])

    # Lista para armazenar todos os proventos de cada mês, incluindo a nova coluna 'TOTAL'
    todos_os_proventos_com_total = []

    # Loop sobre os meses
    for mes in previsto_mensal_total_com_total.index:
        # Pega todos os proventos do mês, incluindo a nova coluna 'TOTAL'
        valores_mes = previsto_mensal_total_com_total.loc[mes].values

        # Adiciona 0 se não houver valores no mês
        if len(valores_mes) == 0:
            valores_mes = [0]

        todos_os_proventos_com_total.extend(valores_mes)

    import statistics
    from collections import Counter

    # Considere somente a coluna 'TOTAL'
    total_column = previsto_mensal_total_com_total['TOTAL']

    # Calcula estatísticas para a coluna 'TOTAL'
    media_total = statistics.mean(total_column)
    mediana_total = statistics.median(total_column)

    # Calcula a moda usando Counter
    contagem_total = Counter(total_column)
    modos_total = [valor for valor, freq in contagem_total.items() if freq == contagem_total.most_common(1)[0][1]]
    # Adiciona 'No unique mode' se não houver um valor modal único
    moda_total = modos_total[0] if len(modos_total) == 1 else 'No unique mode'

    maximo_total = max(total_column)
    minimo_total = min(total_column)

    # Exibe as estatísticas para a coluna 'TOTAL'
    print(f'Média TOTAL: {media_total:.2f}')
    print(f'Mediana TOTAL: {mediana_total:.2f}')
    print(f'Moda TOTAL: {moda_total}')
    print(f'Máximo TOTAL: {maximo_total:.2f}')
    print(f'Mínimo TOTAL: {minimo_total:.2f}')


    ax = previsto_mensal_total.plot(kind='bar', xlabel='Mês', ylabel='Valor Previsto', title=f'Previsão de Dividendos para {ano_atual}', legend=True, stacked=True)
    ax.set_xticklabels(meses_ordenados_portugues)

    ax.annotate(f'Média: {media_total}\nModa: {moda_total}\nMáximo: {maximo_total:.2f}\nMínimo: {minimo_total:.2f}',
            xy=(0.97, 0.95), xycoords='axes fraction', fontsize=8, ha='right', va='top')

    # Obter o número de barras no gráfico
    num_barras = len(previsto_mensal_total)

    # Ajustar o tamanho da figura de acordo com o número de barras
    plt.gcf().set_size_inches(0.5 * num_barras, 6)

    # Salvar o gráfico como uma imagem PNG com tamanho adaptável
    plt.savefig('img/prv.png', format='png', bbox_inches='tight')
