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
def aplicar_valor_intrinseco():
    # Abrir o arquivo indicadores.csv para leitura
    with open('indicadores.csv', newline='', encoding='utf-8') as arquivo_indicadores:
        leitor_csv = csv.DictReader(arquivo_indicadores)
        
        # Abrir o arquivo valor_intrinseco.csv para escrita
        with open('valor_intrinseco.csv', mode='w', newline='', encoding='utf-8') as arquivo_valor_intrinseco:
            campos = ['Ticker', 'Quantidade', 'Setor', 'Data de atualização', 'valor_atual', 'PAYOUT', 'LPA', 'VPA', 'P/L', 'P/VP', 'P/SR', 'ROE', 'ROA', 'EBITDA', 'Margem bruta', 'Margem líquida', 'Margem EBITDA', 'Margem operacional', 'P/CF', 'Liquidez corrente', 'Liquidez imediata', 'Liquidez seca', 'Giro do ativo', 'Endividamento geral', 'Ativo por ação', 'Dívida bruta', 'Dívida líquida', 'Capital de giro', 'Receita líquida por ação', 'EBIT por ação', 'Margem EBIT','Valor intrinseco Grahan', 'Bazin']
            escritor_csv = csv.DictWriter(arquivo_valor_intrinseco, fieldnames=campos)

            # Escrever o cabeçalho no arquivo valor_intrinseco.csv
            escritor_csv.writeheader()

            # Iterar sobre as linhas do arquivo indicadores.csv
            for linha in leitor_csv:
                ticker = linha['Ticker']
                quantidade = linha['Quantidade']
                setor = linha['Setor']
                data_atualizacao = linha['Data de atualização']
                lpa = float(linha['LPA'])
                vpa = float(linha['VPA'])
                try:
                    payout = float(linha['PAYOUT'].replace(',','.').replace('%',''))
                except:
                    payout = None

                # Calcular valor intrínseco usando a função
                valor_intrinseco = calcular_valor_intrinseco(lpa, vpa)
                if payout == None:
                    bazin_valor = 0
                else:
                    bazin_valor = calcular_bazin(lpa,payout)
                # Adicionar o valor intrínseco aos dados
                linha['Valor intrinseco Grahan'] = round(float(valor_intrinseco), 2)
                linha['Bazin'] = round(float(bazin_valor), 2)
                valor_atuala = linha['valor_atual']
                valor_atuala = round(float(valor_atuala), 2)


                valor_atual_porcentagem_bazin = 100*round(float(bazin_valor), 2)/valor_atuala
                valor_atual_porcentagem_valor_intrinseco = 100*round(float(valor_intrinseco), 2)/valor_atuala

                escritor_csv.writerow(linha)
def cor(variacao):
            if variacao > 0:
                return 'green'
            elif variacao < 0:
                return 'red'
            else:
                return 'grey'
def gerar_html():
        import pandas as pd

        # Função para calcular a cor da célula com base na variação percentual
        

        # Ler o arquivo CSV usando pandas
        df = pd.read_csv('valor_intrinseco.csv')

        # Calcular a variação percentual entre valor_atual e Bazin
        df['Variacao_Bazin'] = ((df['Bazin'] - df['valor_atual']) / df['valor_atual']) * 100

        # Calcular a variação percentual entre valor_atual e Graham
        df['Variacao_Graham'] = ((df['Valor intrinseco Grahan'] - df['valor_atual']) / df['valor_atual']) * 100
        df['Variacao_Nathalia'] = (((df['Bazin'] - df['valor_atual']) / df['valor_atual']) * 100 + ((df['Valor intrinseco Grahan'] - df['valor_atual']) / df['valor_atual']) * 100)/2

        # Aplicar a função de cor para as colunas Bazin e Graham
        df['Bazin'] = df['Variacao_Bazin'].apply(lambda x: f'<span style="background-color:{cor(x)}; color:black;">{x:.2f}%</span>')
        df['Valor intrinseco Grahan'] = df['Variacao_Graham'].apply(lambda x: f'<span style="background-color:{cor(x)}; color:black;">{x:.2f}%</span>')
        df['Metodo de Nathalia'] = df['Variacao_Nathalia'].apply(lambda x: f'<span style="background-color:{cor(x)}; color:black;">{x:.2f}%</span>')

        # Escrever os dados em um arquivo HTML
        data = formatar_data()
        with open(f'arquivos/saida{str(data)}.html', 'w') as htmlfile:
            htmlfile.write('<html>\n<head>\n<style>\ntable {border-collapse: collapse;}\n')
            htmlfile.write('td, th {border: 1px solid black; padding: 8px; text-align: center;}\n')
            htmlfile.write('</style>\n</head>\n<body>\n')

            htmlfile.write('<table>\n<tr><th>Ação</th><th>Bazin</th><th>Graham</th><th>Nathalia</th></tr>\n')
            for index, row in df.iterrows():
                htmlfile.write(f'<tr><td>{row["Ticker"]}</td>')
                htmlfile.write(f'<td style="background-color:{cor(row["Variacao_Bazin"])}">{row["Bazin"]}</td>')
                htmlfile.write(f'<td style="background-color:{cor(row["Variacao_Graham"])}">{row["Valor intrinseco Grahan"]}</td>')
                htmlfile.write(f'<td style="background-color:{cor(row["Variacao_Nathalia"])}">{row["Metodo de Nathalia"]}</td></tr>\n')

            htmlfile.write('</table>\n</body>\n</html>')

if __name__ == '__main__':
    aplicar_valor_intrinseco()
    gerar_html()



