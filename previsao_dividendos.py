import os
import csv
import pandas as pd
import requests
from selenium import webdriver
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from datetime import datetime
import time # ADICIONADO: Necessário para time.sleep()
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
    
    def processar_tabela(tabela_html):
        tabela = pd.read_html(StringIO(str(tabela_html)), decimal=',', thousands='.')[0]

        # Lógica de robustez: Identificar e padronizar colunas Pagamento e Valor
        colunas_tabela = [str(col) for col in tabela.columns]
        
        # Tenta encontrar a coluna de data (Pagamento ou Data)
        date_col_candidates = [col for col in colunas_tabela if 'Pagamento' in col or 'DATA' in col.upper()]
        # Tenta encontrar a coluna de valor (Valor sem porcentagem)
        value_col_candidates = [col for col in colunas_tabela if 'Valor' in col and '%' not in col]
        
        # Seleciona a primeira candidata para cada coluna
        date_col = date_col_candidates[0] if date_col_candidates else None
        value_col = value_col_candidates[0] if value_col_candidates else None
        
        # Fallback por índice (comum em sites como Investidor10)
        if not date_col and len(colunas_tabela) > 1:
            date_col = colunas_tabela[1] # Tentativa de índice 1 para data
        
        if not value_col and len(colunas_tabela) > 3:
            value_col = colunas_tabela[3] # Tentativa de índice 3 para valor

        if not date_col:
            raise ValueError("Coluna de Pagamento não identificada.")
        
        if not value_col:
            raise ValueError("Coluna de Valor não identificada.")

        # Renomeia para as colunas esperadas
        tabela.rename(columns={date_col: 'Pagamento', value_col: 'Valor'}, inplace=True)
        
        # A partir daqui, o processamento original continua
        tabela['Pagamento'] = pd.to_datetime(tabela['Pagamento'], format='%d/%m/%Y', errors='coerce')
        dados_ano_anterior = tabela[tabela['Pagamento'].dt.year == (Ano_Atual - 1)].copy()
        dados_ano_anterior['Valor Total'] = dados_ano_anterior['Valor'].apply(limpar_e_arredondar) * quantidade
        # Retorna uma Series agrupada por mês (1 a 12), preenchida com 0 onde não houver dados
        return dados_ano_anterior.groupby(dados_ano_anterior['Pagamento'].dt.month)['Valor Total'].sum().reindex(range(1, 13), fill_value=0)

    print(f"Obtendo dividendos de: {ticket}")
    tabela_html = None

    # 1. Tenta obter os dados via requests
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        tabela_html = soup.find('table', {'id': tabela_id}) if tabela_id else soup.find('table')
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição para {ticket}: {e}")

    # 2. Se a tabela não for encontrada, tenta usar Selenium
    if tabela_html is None:
        print(f"Tabela não encontrada para {ticket}. Tentando com Selenium...")
        tabela_html = obter_tabela_com_selenium(url, tabela_id)

    # 3. Processa a tabela encontrada ou retorna uma Series de zeros
    if tabela_html is not None:
        try:
            return processar_tabela(tabela_html)
        except Exception as e:
            print(f"Erro ao processar os dados para o ticket {ticket}: {e}")
            # Retorna uma Series de zeros para 12 meses (índices 1 a 12) em caso de erro de processamento
            return pd.Series([0.0] * 12, index=range(1, 13))

    # 4. Se a tabela não foi encontrada (após requests e selenium), retorna Series de zeros.
    print(f"Erro: Nenhuma tabela encontrada para o ticket {ticket}. Retornando zeros.")
    # Retorna uma Series de zeros para 12 meses (índices 1 a 12), para permitir a concatenação
    return pd.Series([0.0] * 12, index=range(1, 13))


def obter_tabela_com_selenium(url, tabela_id=None):
    try:
        # Configuração do WebDriver (assumindo que o Chrome está disponível no ambiente)
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Executa o navegador em modo headless (sem interface gráfica)
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36')

        with webdriver.Chrome(options=options) as driver:
            driver.get(url)
            # Espera um pouco para a página carregar (pode ser necessário ajuste)
            time.sleep(random.uniform(2, 5)) 
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            tabela_html = soup.find('table', {'id': tabela_id}) if tabela_id else soup.find('table')
            return tabela_html

    except Exception as e:
        print(f"Erro ao usar Selenium para acessar {url}: {e}")
        return None

# Funções específicas para ações e FIIs
def obter_dividendos_acao(ticket, quantidade):
    url = f'https://www.dadosdemercado.com.br/acoes/{ticket}/dividendos'
    return obter_dividendos(ticket, quantidade, url)

def obter_dividendos_fii(ticket, quantidade):
    url = f'https://investidor10.com.br/fiis/{ticket}/'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36'}
    return obter_dividendos(ticket, quantidade, url, tabela_id='table-dividends-history', headers=headers)

# Função para ler CSV e obter dividendos
def ler_e_obter_dividendos(caminho_arquivo, obter_dividendos_func):
    tickers, previsto_mensal_por_ticket = [], []
    try:
        with open(caminho_arquivo, 'r') as arquivo_csv:
            leitor_csv = csv.reader(arquivo_csv)
            next(leitor_csv, None)
            for linha in leitor_csv:
                # Garante que a linha tem pelo menos 2 elementos para evitar IndexError
                if len(linha) < 2:
                    print(f"Linha ignorada no arquivo {caminho_arquivo} devido a dados insuficientes: {linha}")
                    continue
                    
                ticket = linha[0]
                try:
                    quantidade = int(linha[1])
                except ValueError:
                    print(f"Quantidade inválida para {ticket} no arquivo {caminho_arquivo}. Usando 0.")
                    quantidade = 0
                
                tickers.append(ticket)
                previsto_mensal_por_ticket.append(obter_dividendos_func(ticket, quantidade))
                
                # Pausa para evitar bloqueio de IP
                time.sleep(random.uniform(1, 3)) 

    except FileNotFoundError:
        print(f"Aviso: Arquivo {caminho_arquivo} não encontrado. Continuando sem ele.")
    except Exception as e:
        print(f"Erro ao processar {caminho_arquivo}: {e}")
        
    return tickers, previsto_mensal_por_ticket

# Obter dividendos de ações e FIIs
tickers_acoes, previsto_mensal_acoes = ler_e_obter_dividendos(Caminho_Arquivo_Acoes, obter_dividendos_acao)
tickers_fiis, previsto_mensal_fiis = ler_e_obter_dividendos(Caminho_Arquivo_Fiis, obter_dividendos_fii)

# Combina os dividendos em um único DataFrame
# Corrigido: Agora, todos os elementos em previsto_mensal_acoes e previsto_mensal_fiis são pd.Series alinhadas.
todos_previstos = pd.concat(previsto_mensal_acoes + previsto_mensal_fiis, axis=1)

# Atribui as colunas corretas
todos_previstos.columns = tickers_acoes + tickers_fiis
# O índice já é 1 a 12, mas vamos redefinir para os nomes dos meses
todos_previstos.index = Meses_Ordenados_Portugues

# Limpa e arredonda os valores do DataFrame
todos_previstos_limpos = todos_previstos.map(limpar_e_arredondar).fillna(0)

# Soma os dividendos de todos os tickers por mês
todos_previstos_limpos['TOTAL'] = todos_previstos_limpos.sum(axis=1)

# Função para calcular estatísticas
def calcular_estatisticas(data):
    # Trata o caso em que 'data' está vazia
    if not data.any():
        return 0, 0, 'N/A', 0, 0
    
    media = statistics.mean(data)
    mediana = statistics.median(data)
    contagem = Counter(data)
    # Garante que há uma moda se a contagem não estiver vazia
    if contagem:
        modos = [valor for valor, freq in contagem.items() if freq == contagem.most_common(1)[0][1]]
        moda = modos[0] if len(modos) == 1 else 'Sem moda única'
    else:
        moda = 'N/A'
        
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
def configurar_grafico(ax, titulo, xlabel, ylabel, xticks=None, rotation=45, grid_visible=True):
    ax.set_title(titulo, fontsize=16)
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    if xticks:
        ax.set_xticks(range(len(xticks)))
        ax.set_xticklabels(xticks, rotation=rotation, ha='right')
    if grid_visible:
        ax.grid(axis='x', linestyle='--', alpha=0.7)

def adicionar_estatisticas(ax, estatisticas):
    estatisticas_texto = (
        f"$\\mathbf{{Média}}$: {estatisticas[0]:.2f}\n"
        f"$\\mathbf{{Moda}}$: {estatisticas[2]}\n"
        f"$\\mathbf{{Máximo}}$: {estatisticas[3]:.2f}\n"
        f"$\\mathbf{{Mínimo}}$: {estatisticas[4]:.2f}"
    )
    ax.annotate(
        estatisticas_texto,
        xy=(0.95, 0.95),  # Posição no canto superior direito
        xycoords='axes fraction',  # Coordenadas relativas ao eixo
        fontsize=10,
        ha='right',
        va='top',
        multialignment='left',  # Alinha o texto à esquerda
        bbox=dict(boxstyle="round", facecolor="lightgrey", edgecolor="black", alpha=0.5)
    )

def plotar_barras(data, estatisticas, ax):
    # Filtra colunas que existem no mapeamento (garante que não há problemas se algum ticker falhou)
    cols_para_plot = [col for col in data.columns if col in mapeamento_cores]
    cores = [mapeamento_cores[col] for col in cols_para_plot]
    
    # Se não houver dados válidos para plotar, exibe uma mensagem e retorna
    if data[cols_para_plot].empty:
        ax.text(0.5, 0.5, 'Sem dados válidos para o gráfico de Barras.', 
                transform=ax.transAxes, ha='center', va='center')
        return

    data[cols_para_plot].plot(kind='bar', ax=ax, stacked=True, color=cores, legend=False)
    
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, loc='center left', bbox_to_anchor=(-0.28, 0.5), fontsize=10)
    configurar_grafico(ax, f'Previsão Mensal de Dividendos - {Ano_Atual}', None, 'Valor Previsto (R$)', Meses_Ordenados_Portugues)
    adicionar_estatisticas(ax, estatisticas)

def plotar_boxplot(data, ax):
    if data.empty:
        ax.text(0.5, 0.5, 'Sem dados válidos para o Boxplot.', 
                transform=ax.transAxes, ha='center', va='center')
        return
        
    data.T.boxplot(
        ax=ax,
        boxprops=dict(linestyle='-', linewidth=2, color='blue'),
        flierprops=dict(marker='o', color='red', alpha=0.5),
        medianprops=dict(linestyle='-', linewidth=2, color='green')
    )

    # Plota os pontos individuais
    for i, col in enumerate(data.columns):
        if col in mapeamento_cores:
            ax.scatter(
                [i + 1] * len(data), # Posições no eixo X
                data[col],           # Valores no eixo Y
                marker='o',
                label=col,
                color=mapeamento_cores[col],
                alpha=0.7,
                zorder=2
            )

    # Ajusta os rótulos do eixo X
    ax.set_xticks(range(1, len(data.columns) + 1))
    ax.set_xticklabels(data.columns, rotation=45, ha='right')

    # Configura o gráfico
    configurar_grafico(ax, f'Boxplot da Distribuição Mensal de Dividendos - {Ano_Atual}', None, 'Valor Previsto (R$)')
    ax.legend(loc='center left', bbox_to_anchor=(-0.28, 0.5), fontsize=10)

def plotar_pizza(data, ax):
    totais_por_ticker = data.sum(axis=0)
    # Filtra tickers com total zero (evita fatias irrelevantes ou erros de plotagem)
    totais_validos = totais_por_ticker[totais_por_ticker > 0]
    
    if totais_validos.empty:
        ax.text(0.5, 0.5, 'Sem dados válidos para o gráfico de Pizza.', 
                transform=ax.transAxes, ha='center', va='center')
        return

    cores = [mapeamento_cores[ticker] for ticker in totais_validos.index]
    
    wedges, texts = ax.pie(
        totais_validos,
        startangle=90,
        colors=cores,
        wedgeprops=dict(width=0.5)  # Define o buraco no meio
    )
    
    legend_labels = [f"{ticker}: {valor:,.2f}" for ticker, valor in zip(totais_validos.index, totais_validos)]
    
    ax.legend(
        wedges,
        legend_labels,
        loc='center left',
        bbox_to_anchor=(-0.35, 0.5),
        fontsize=10,
    )
    ax.set_title(f'Previsão de Dividendos Anual por Ticker (R$) - {Ano_Atual}', fontsize=16)

def plotar_heatmap(data, ax):
    if data.empty:
        ax.text(0.5, 0.5, 'Sem dados válidos para o Mapa de Calor.', 
                transform=ax.transAxes, ha='center', va='center')
        return
        
    sns.heatmap(data.T, annot=True, linewidth=.5, fmt=".2f", cmap=paleta_heatmap_escolhida, cbar=True,
                ax=ax, xticklabels=Meses_Ordenados_Portugues, yticklabels=data.T.index,
                annot_kws={"size": "small"})
    configurar_grafico(ax, f'Mapa de Calor Mensal de Dividendos - {Ano_Atual}', None, None, grid_visible=False)
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0, ha='right')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')

def plotar_todos_graficos(data, estatisticas):
    fig, axs = plt.subplots(2, 2, figsize=(25, 15))
    plotar_barras(data, estatisticas, axs[0, 0])
    plotar_boxplot(data, axs[0, 1])
    plotar_pizza(data, axs[1, 0])
    plotar_heatmap(data, axs[1, 1])
    plt.subplots_adjust(hspace=0.3, wspace=0.3)
    return fig

# Gera e salva a imagem com todos os gráficos
path = 'arquivos'
os.makedirs(path, exist_ok=True)
# Verifica se há tickers válidos antes de tentar plotar
if not todos_previstos_limpos.empty:
    fig_todos = plotar_todos_graficos(todos_previstos_limpos, estatisticas_total)
    todos_graficos_img = f'todos_graficos_{formatar_data()}.png'
    # Salva o gráfico
    try:
        plt.savefig(os.path.join(path, todos_graficos_img), format='png', bbox_inches='tight')
        print(f"Gráfico salvo em: {os.path.join(path, todos_graficos_img)}")
    except Exception as e:
        print(f"Erro ao salvar o gráfico: {e}")
    plt.show() # Removido para evitar que a aplicação fique presa em ambientes sem display.
else:
    print("Nenhum dado de dividendo válido foi processado. Nenhum gráfico gerado.")