import csv
import math
from datetime import datetime

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
            campos = ['Ticker', 'Quantidade', 'Setor', 'Data de atualização', 'Valor Atual', 'PAYOUT', 'LPA', 'VPA', 'P/L', 'P/VP', 'P/SR', 'ROE', 'ROA', 'EBITDA', 'Margem bruta', 'Margem líquida', 'Margem EBITDA', 'Margem operacional', 'P/CF', 'Liquidez corrente', 'Liquidez imediata', 'Liquidez seca', 'Giro do ativo', 'Endividamento geral', 'Ativo por ação', 'Dívida bruta', 'Dívida líquida', 'Capital de giro', 'Receita líquida por ação', 'EBIT por ação', 'Margem EBIT','Valor intrinseco Grahan', 'Bazin']
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
                valor_atuala = linha['Valor Atual']
                valor_atuala = round(float(valor_atuala), 2)


                valor_atual_porcentagem_bazin = 100*round(float(bazin_valor), 2)/valor_atuala
                valor_atual_porcentagem_valor_intrinseco = 100*round(float(valor_intrinseco), 2)/valor_atuala

                #print(f'{ticker}: valor atual: {valor_atuala} lpa:{lpa} payout:{payout} valor_intrinseco:{valor_intrinseco} bazin: {bazin_valor}')
                print(f'{ticker}: valor_pocentagem_Bazin: {valor_atual_porcentagem_bazin -100}  valor_intriseco: {valor_atual_porcentagem_valor_intrinseco-100}')

                #print()
                #print(bazin_valor)
                # Escrever os dados no arquivo valor_intrinseco.csv
                escritor_csv.writerow(linha)


if __name__ == '__main__':
    aplicar_valor_intrinseco()



import pandas as pd

# Caminho do arquivo CSV
caminho_arquivo = 'valor_intrinseco.csv'

# Leitura do arquivo CSV usando pandas
df = pd.read_csv(caminho_arquivo)

# Iterando sobre cada linha do DataFrame
for index, row in df.iterrows():
    ticker = row['Ticker']
    valor_atual = row['Valor Atual']
    valor_intrinseco_grahan = row['Valor intrinseco Grahan']
    valor_intrinseco_bazin = row['Bazin']

    # Calculando a variação percentual em relação ao Valor intrínseco de Grahan e Bazin
    variacao_grahan = ((valor_atual - valor_intrinseco_grahan) / valor_atual) * 100
    variacao_bazin = ((valor_atual - valor_intrinseco_bazin) / valor_atual) * 100

    # Verificando se a empresa pode subir ou descer com base nos valores intrínsecos
    mensagem_grahan = f'A empresa {ticker} pode subir {variacao_grahan:.2f}%' if variacao_grahan > 0 else f'A empresa {ticker} pode descer {variacao_grahan:.2f}%'
    mensagem_bazin = f'A empresa {ticker} pode subir {variacao_bazin:.2f}%' if variacao_bazin > 0 else f'A empresa {ticker} pode descer {variacao_bazin:.2f}%'

    # Imprimindo os resultados para cada empresa
    print("Análise com base no Valor intrínseco de Graham:")
    print(mensagem_grahan)
    print("\nAnálise com base no Valor intrínseco de Bazin:")
    print(mensagem_bazin)
    print("\n")
