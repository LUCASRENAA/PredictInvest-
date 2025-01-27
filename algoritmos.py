import csv
import math
from datetime import datetime
from main import formatar_data
import pandas as pd


def calcular_valor_intrinseco(lpa, vpa):
    """Calcula o valor intrínseco com base no LPA e VPA."""
    if lpa is None or vpa is None:
        return 0  # Retorna 0 se LPA ou VPA forem None
    multiplicador = 12
    return math.sqrt(multiplicador * lpa * vpa)


def calcular_bazin(lpa, payout):
    """Calcula o valor de Bazin com base no LPA e Payout."""
    if lpa is None or payout is None:
        return 0  # Retorna 0 se LPA ou Payout forem None
    return (lpa * payout / 100) / 0.07


def converter_para_float(valor, substituicoes=None):
    """Converte um valor para float, com substituições opcionais para formatação."""
    if substituicoes:
        for old, new in substituicoes.items():
            valor = valor.replace(old, new)
    try:
        return float(valor)
    except ValueError:
        return 0.0  # Retorna 0.0 como padrão para erros de conversão

def aplicar_valor_intrinseco():
    """Aplica o cálculo de valor intrínseco e Bazin e gera um arquivo CSV."""
    # Abrir o arquivo indicadores.csv para leitura
    with open('indicadores.csv', newline='', encoding='utf-8') as arquivo_indicadores:
        leitor_csv = csv.DictReader(arquivo_indicadores)
        
        # Abrir o arquivo valor_intrinseco.csv para escrita
        with open('valor_intrinseco.csv', mode='w', newline='', encoding='utf-8') as arquivo_valor_intrinseco:
            campos = [
                'Ticker', 'Quantidade', 'Setor', 'Data de atualização', 'Valor Atual', 'PAYOUT', 'LPA', 'VPA',
                'P/L', 'P/VP', 'P/SR', 'ROE', 'ROA', 'EBITDA', 'Margem bruta', 'Margem líquida', 'Margem EBITDA',
                'Margem operacional', 'P/CF', 'Liquidez corrente', 'Liquidez imediata', 'Liquidez seca', 'Giro do ativo',
                'Endividamento geral', 'Ativo por ação', 'Dívida bruta', 'Dívida líquida', 'Capital de giro',
                'Receita líquida por ação', 'EBIT por ação', 'Margem EBIT', 'Valor intrinseco Graham', 'Bazin'
            ]
            escritor_csv = csv.DictWriter(arquivo_valor_intrinseco, fieldnames=campos)
            escritor_csv.writeheader()

            # Iterar sobre as linhas do arquivo indicadores.csv
            for linha in leitor_csv:
                # Extrair e converter dados relevantes
                lpa = converter_para_float(linha['LPA'], substituicoes={',': '.', '%': ''})
                vpa = converter_para_float(linha['VPA'])
                payout = converter_para_float(linha['PAYOUT'], substituicoes={',': '.', '%': ''})
                valor_atual = converter_para_float(linha['Valor Atual'])

                # Calcular valor intrínseco e Bazin
                valor_intrinseco = calcular_valor_intrinseco(lpa, vpa)
                bazin_valor = calcular_bazin(lpa, payout)

                # Atualizar dados na linha
                linha['Valor intrinseco Graham'] = round(valor_intrinseco, 2)
                linha['Bazin'] = round(bazin_valor, 2)
                linha['Valor Atual'] = round(valor_atual, 2)  # Atualizar valor atual na linha

                # Escrever a linha no arquivo CSV de saída
                escritor_csv.writerow(linha)


def cor(variacao):
    """Retorna a cor (vermelho, verde ou cinza) com base na variação percentual."""
    if pd.isna(variacao):
        return 'grey'  # Retorna cinza para valores NaN
    elif variacao > 0:
        return 'green'
    elif variacao < 0:
        return 'red'
    else:
        return 'grey'


def calcular_variacao(valor_atual, valor_comparado):
    """Calcula a variação percentual, mas evita NaN, -100% e outros valores inválidos."""
    
    if valor_atual == 0 or pd.isna(valor_atual) or valor_comparado == 0:
        return 0  # Retorna 0 para valores zero ou inválidos

    variacao = ((valor_comparado - valor_atual) / valor_atual) * 100

    # Evita variação extrema ou irrelevante
    if abs(variacao) < 0.01 or variacao <= -100 or variacao >= 10000:
        return 0  # Retorna 0 para pequenas variações ou valores extremos

    return round(variacao, 2)  # Retorna a variação arredondada


def gerar_html():
    """Gera um arquivo HTML com os dados de valor intrínseco e Bazin."""
    # Ler o arquivo CSV usando pandas
    df = pd.read_csv('valor_intrinseco.csv')

    # Calcular a variação percentual entre Valor Atual e Bazin
    df['Variacao_Bazin'] = df.apply(lambda row: calcular_variacao(row['Valor Atual'], row['Bazin']), axis=1)

    # Calcular a variação percentual entre Valor Atual e Graham
    df['Variacao_Graham'] = df.apply(lambda row: calcular_variacao(row['Valor Atual'], row['Valor intrinseco Graham']), axis=1)

    # Calcular a variação percentual média (Nathalia)
    df['Variacao_Nathalia'] = df.apply(lambda row: (
        calcular_variacao(row['Valor Atual'], row['Bazin']) + calcular_variacao(row['Valor Atual'], row['Valor intrinseco Graham'])
    ) / 2, axis=1)

    # Aplicar a função de cor para as colunas Bazin e Graham
    df['Bazin'] = df['Variacao_Bazin'].apply(lambda x: f'<span style="background-color:{cor(x)}; color:black;">{x:.2f}%</span>')
    df['Valor intrinseco Graham'] = df['Variacao_Graham'].apply(lambda x: f'<span style="background-color:{cor(x)}; color:black;">{x:.2f}%</span>')
    df['Metodo de Nathalia'] = df['Variacao_Nathalia'].apply(lambda x: f'<span style="background-color:{cor(x)}; color:black;">{x:.2f}%</span>')

    # Escrever os dados em um arquivo HTML
    data = formatar_data()
    with open(f'arquivos/saida{str(data)}.html', 'w') as htmlfile:
            htmlfile.write('<html>\n<head>\n<style>\ntable {border-collapse: collapse;}\n')
            htmlfile.write('td, th {border: 1px solid black; padding: 8px; text-align: center;}\n')
            htmlfile.write('</style>\n</head>\n<body>\n')

            # Adicionar descrição antes da tabela
            htmlfile.write('<h2>Índices Utilizados:</h2>\n')
            htmlfile.write('<p><strong>Valor Intrínseco (Graham):</strong> Calculado a partir da fórmula √(12 * LPA * VPA), onde LPA é o Lucro por Ação e VPA é o Valor Patrimonial por Ação. Este índice é utilizado para estimar o valor justo da ação com base em seus lucros e patrimônio.</p>\n')
            htmlfile.write('<p><strong>Bazin:</strong> Calculado através da fórmula (LPA * Payout / 100) / 0.07, onde LPA é o Lucro por Ação e Payout é o percentual de lucro distribuído aos acionistas. Este índice tenta estimar o valor justo da ação de acordo com a política de distribuição de lucros da empresa.</p>\n')
            htmlfile.write('<p><strong>Índice de Nathalia:</strong> Média ponderada das variações percentuais entre o Valor Atual e os índices de Bazin e Graham. Este índice combina os dois métodos para dar uma visão mais equilibrada do valor da ação.</p>\n')

            # Adicionar tabela
            htmlfile.write('<table>\n<tr><th>Ação</th><th>Bazin</th><th>Graham</th><th>Nathalia</th></tr>\n')
            for index, row in df.iterrows():
                htmlfile.write(f'<tr><td>{row["Ticker"]}</td>')
                htmlfile.write(f'<td style="background-color:{cor(row["Variacao_Bazin"])}">{row["Bazin"]}</td>')
                htmlfile.write(f'<td style="background-color:{cor(row["Variacao_Graham"])}">{row["Valor intrinseco Graham"]}</td>')
                htmlfile.write(f'<td style="background-color:{cor(row["Variacao_Nathalia"])}">{row["Metodo de Nathalia"]}</td></tr>\n')

            htmlfile.write('</table>\n</body>\n</html>')   


if __name__ == '__main__':
    aplicar_valor_intrinseco()
    gerar_html()
