import os
import csv
import pandas as pd
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from datetime import datetime
import statistics
from collections import Counter
from io import StringIO
import seaborn as sns
from itertools import cycle
from main import formatar_data
import random

# Configurações iniciais
Caminho_Arquivo_Acoes = 'acoes.csv'
Caminho_Arquivo_Fiis = 'fiis.csv'
Ano_Atual = datetime.now().year
Meses_Ordenados_Portugues = [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
]

# Função para limpar e arredondar valores
def limpar_e_arredondar(valor):
    try:
        valor_limpo = str(valor).replace('*', '').replace(',', '.')
        if valor_limpo.count('.') > 1:
            valor_limpo = valor_limpo.split('.')[0] + '.' + valor_limpo.split('.')[1]
        return round(float(valor_limpo), 2) if not pd.isna(valor_limpo) else 0
    except (ValueError, TypeError):
        return 0

# Função genérica para obter dividendos
def obter_dividendos(ticket, quantidade, url, tabela_id=None, headers=None):
    print(f"Obtendo dividendos de: {ticket}")
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    tabela_html = soup.find('table', {'id': tabela_id}) if tabela_id else soup.find('table')
    tabela = pd.read_html(StringIO(str(tabela_html)), decimal=',', thousands='.')[0]
    tabela['Pagamento'] = pd.to_datetime(tabela['Pagamento'], format='%d/%m/%Y', errors='coerce')
    
    dados_ano_anterior = tabela[tabela['Pagamento'].dt.year == (Ano_Atual - 1)].copy()
    dados_ano_anterior['Valor Total'] = dados_ano_anterior['Valor'].apply(limpar_e_arredondar) * quantidade
    return dados_ano_anterior.groupby(dados_ano_anterior['Pagamento'].dt.month)['Valor Total'].sum().reindex(range(1, 13), fill_value=0)

# Funções específicas para ações e FIIs
def obter_dividendos_acao(ticket, quantidade):
    url = f'https://www.dadosdemercado.com.br/acoes/{ticket}/dividendos'
    return obter_dividendos(ticket, quantidade, url)

def obter_dividendos_fii(ticket, quantidade):
    url = f'https://investidor10.com.br/fiis/{ticket}/'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    return obter_dividendos(ticket, quantidade, url, tabela_id='table-dividends-history', headers=headers)

# Função para ler CSV e obter dividendos
def ler_e_obter_dividendos(caminho_arquivo, obter_dividendos_func):
    tickers, previsto_mensal_por_ticket = [], []
    try:
        with open(caminho_arquivo, 'r') as arquivo_csv:
            leitor_csv = csv.reader(arquivo_csv)
            next(leitor_csv, None)
            for linha in leitor_csv:
                ticket, quantidade = linha[0], int(linha[1])
                tickers.append(ticket)
                previsto_mensal_por_ticket.append(obter_dividendos_func(ticket, quantidade))
    except Exception as e:
        print(f'Erro ao processar {caminho_arquivo}: {e}')
    return tickers, previsto_mensal_por_ticket

# Obter dividendos de ações e FIIs
tickers_acoes, previsto_mensal_acoes = ler_e_obter_dividendos(Caminho_Arquivo_Acoes, obter_dividendos_acao)
tickers_fiis, previsto_mensal_fiis = ler_e_obter_dividendos(Caminho_Arquivo_Fiis, obter_dividendos_fii)

# Combina os dividendos em um único DataFrame
todos_previstos = pd.concat(previsto_mensal_acoes + previsto_mensal_fiis, axis=1)
todos_previstos.columns = tickers_acoes + tickers_fiis
todos_previstos.index = Meses_Ordenados_Portugues

# Limpa e arredonda os valores do DataFrame
todos_previstos_limpos = todos_previstos.map(limpar_e_arredondar).fillna(0)

# Soma os dividendos de todos os tickers por mês
todos_previstos_limpos['TOTAL'] = todos_previstos_limpos.sum(axis=1)

# Função para calcular estatísticas
def calcular_estatisticas(data):
    media = statistics.mean(data)
    mediana = statistics.median(data)
    contagem = Counter(data)
    modos = [valor for valor, freq in contagem.items() if freq == contagem.most_common(1)[0][1]]
    moda = modos[0] if len(modos) == 1 else 'No unique mode'
    return media, mediana, moda, max(data), min(data)

# Estatísticas do total
estatisticas_total = calcular_estatisticas(todos_previstos_limpos['TOTAL'])
print(f"Estatísticas do total de dividendos: {estatisticas_total}")

# Remove a coluna TOTAL para o gráfico
todos_previstos_limpos = todos_previstos_limpos.drop(columns=['TOTAL'])

# Define uma lista de estilos de paletas de cores para os gráficos
paletas_cores = [
    plt.cm.tab20.colors,
    plt.cm.Paired.colors,
    plt.cm.Set1.colors,
    plt.cm.Set2.colors,
    plt.cm.Set3.colors,
    plt.cm.Accent.colors,
    plt.cm.Dark2.colors,
]

# Define uma lista de estilos de paletas para o heatmap
paletas_heatmap = [
    "YlGnBu",
    "coolwarm",
    "viridis",
    "magma",
    "cubehelix", 
    "mako",
    "rocket",
    "flare",
    "crest",
    "vlag",
    "icefire"
]

paleta_escolhida = random.choice(paletas_cores)
paleta_heatmap_escolhida = random.choice(paletas_heatmap)

# Define um mapeamento fixo de cores para os tickers
def gerar_mapeamento_cores(tickers):
    return {ticker: cor for ticker, cor in zip(tickers, cycle(paleta_escolhida))}

# Gera o mapeamento de cores para os tickers
tickers = tickers_acoes + tickers_fiis
mapeamento_cores = gerar_mapeamento_cores(tickers)

# Funções para plotagem de gráficos
def configurar_grafico(ax, titulo, xlabel, ylabel, xticks=None, rotation=45):
    ax.set_title(titulo, fontsize=16)
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    if xticks:
        ax.set_xticks(range(len(xticks)))
        ax.set_xticklabels(xticks, rotation=rotation, ha='right')
    ax.grid(axis='y', linestyle='--', alpha=0.7)

def adicionar_estatisticas(ax, estatisticas):
    estatisticas_texto = (
        f"Média: {estatisticas[0]:.2f}\n"
        f"Moda: {estatisticas[2]}\n"
        f"Máximo: {estatisticas[3]:.2f}\n"
        f"Mínimo: {estatisticas[4]:.2f}"
    )
    ax.text(0.95, 0.95, estatisticas_texto, transform=ax.transAxes, fontsize=10,
            ha='right', va='top', bbox=dict(boxstyle="round", facecolor="lightgrey", alpha=0.5))

def plotar_barras(data, estatisticas, ax):
    cores = [mapeamento_cores[col] for col in data.columns]
    data.plot(kind='bar', ax=ax, stacked=True, color=cores, legend=False)
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, loc='center left', bbox_to_anchor=(-0.25, 0.5), fontsize=10)
    configurar_grafico(ax, f'Previsão Acumulada de Dividendos Mensais - {Ano_Atual}', None, 'Valor Previsto (R$)', Meses_Ordenados_Portugues)
    adicionar_estatisticas(ax, estatisticas)

def plotar_boxplot(data, ax):
    data.T.boxplot(ax=ax, boxprops=dict(linestyle='-', linewidth=2, color='blue'),
                   flierprops=dict(marker='o', color='red', alpha=0.5),
                   medianprops=dict(linestyle='-', linewidth=2, color='green'))
    ax.set_xticks(range(1, len(Meses_Ordenados_Portugues) + 1))
    ax.set_xticklabels(Meses_Ordenados_Portugues, rotation=45, ha='right')
    configurar_grafico(ax, f'Boxplot da Distribuição Mensal de Dividendos - {Ano_Atual}', None, 'Valor Distribuído (R$)')

def plotar_tendencia(data, ax):
    for col in data.columns:
        data[col].plot(ax=ax, marker='o', label=col, color=mapeamento_cores[col])
    ax.legend(loc='center left', bbox_to_anchor=(-0.25, 0.5), fontsize=10)
    configurar_grafico(ax, f'Tendência Mensal dos Dividendos - {Ano_Atual}', None, 'Valor Previsto (R$)', Meses_Ordenados_Portugues)

def plotar_heatmap(data, ax):
    sns.heatmap(data.T, annot=True, fmt=".2f", cmap=paleta_heatmap_escolhida, cbar=True, ax=ax, 
                xticklabels=Meses_Ordenados_Portugues, yticklabels=data.T.index)
    configurar_grafico(ax, f'Mapa de Calor dos Dividendos Mensais - {Ano_Atual}', None, None)
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0, ha='right')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')

def plotar_todos_graficos(data, estatisticas):
    fig, axs = plt.subplots(2, 2, figsize=(20, 15))
    plotar_barras(data, estatisticas, axs[0, 0])
    plotar_boxplot(data, axs[0, 1])
    plotar_tendencia(data, axs[1, 0])
    plotar_heatmap(data, axs[1, 1])
    plt.tight_layout()
    return fig

# Gera e salva a imagem com todos os gráficos
path = 'arquivos'
os.makedirs(path, exist_ok=True)
fig_todos = plotar_todos_graficos(todos_previstos_limpos, estatisticas_total)
todos_graficos_img = f'todos_graficos_{formatar_data()}.png'
plt.savefig(os.path.join(path, todos_graficos_img), format='png', bbox_inches='tight')
plt.show()
