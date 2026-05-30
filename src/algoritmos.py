import csv
from datetime import datetime
import pandas as pd
from pathlib import Path

from config import INDICADORES_CSV, VALOR_INTRINSECO_CSV, ARQUIVOS_DIR
from src.utils.logger import get_logger
from src.utils.data_processor import converter_para_float, calcular_valor_intrinseco_12, calcular_bazin, calcular_variacao
from src.utils.visualizer import cor_html

logger = get_logger(__name__)

def aplicar_valor_intrinseco(df_indicadores: pd.DataFrame = None) -> pd.DataFrame:
    """Aplica o cálculo de valor intrínseco e Bazin e retorna um DataFrame modificado."""
    # Se o df_indicadores não foi passado (ex: executado via --algoritmos isolado), lê do CSV
    if df_indicadores is None or df_indicadores.empty:
        if not Path(INDICADORES_CSV).exists():
            logger.error("Erro: Arquivo %s não encontrado.", INDICADORES_CSV)
            return pd.DataFrame()
        df_indicadores = pd.read_csv(INDICADORES_CSV, dtype=str)

    resultados = []
    
    with open(VALOR_INTRINSECO_CSV, mode='w', newline='', encoding='utf-8') as arquivo_valor_intrinseco:
        campos = [
            'Ticker', 'Quantidade', 'Setor', 'Data de atualização', 'Valor Atual', 'PAYOUT', 'LPA', 'VPA',
            'P/L', 'P/VP', 'P/SR', 'ROE', 'ROA', 'EBITDA', 'Margem bruta', 'Margem líquida', 'Margem EBITDA',
            'Margem operacional', 'P/CF', 'Liquidez corrente', 'Liquidez imediata', 'Liquidez seca', 'Giro do ativo',
            'Endividamento geral', 'Ativo por ação', 'Dívida bruta', 'Dívida líquida', 'Capital de giro',
            'Receita líquida por ação', 'EBIT por ação', 'Margem EBIT', 'Valor intrinseco Graham', 'Bazin'
        ]
        escritor_csv = csv.DictWriter(arquivo_valor_intrinseco, fieldnames=campos)
        escritor_csv.writeheader()

        for _, linha in df_indicadores.iterrows():
            linha_dict = linha.to_dict()
            lpa = converter_para_float(linha_dict.get('LPA'), substituicoes={',': '.', '%': ''})
            vpa = converter_para_float(linha_dict.get('VPA'))
            payout = converter_para_float(linha_dict.get('PAYOUT'), substituicoes={',': '.', '%': ''})
            valor_atual = converter_para_float(linha_dict.get('Valor Atual'))

            valor_intrinseco = calcular_valor_intrinseco_12(lpa, vpa)
            bazin_valor = calcular_bazin(lpa, payout)

            linha_dict['Valor intrinseco Graham'] = round(valor_intrinseco, 2)
            linha_dict['Bazin'] = round(bazin_valor, 2)
            linha_dict['Valor Atual'] = round(valor_atual, 2)

            escritor_csv.writerow(linha_dict)
            resultados.append(linha_dict)
            
    return pd.DataFrame(resultados)

def gerar_html(df: pd.DataFrame = None) -> None:
    """Gera um arquivo HTML com os dados calculados de valor intrínseco e Bazin."""
    if df is None or df.empty:
        if not Path(VALOR_INTRINSECO_CSV).exists():
            logger.error("Erro: Arquivo %s não encontrado ao tentar gerar HTML.", VALOR_INTRINSECO_CSV)
            return
        df = pd.read_csv(VALOR_INTRINSECO_CSV)

    df['Variacao_Bazin'] = df.apply(lambda row: calcular_variacao(row['Valor Atual'], row['Bazin']), axis=1)
    df['Variacao_Graham'] = df.apply(lambda row: calcular_variacao(row['Valor Atual'], row['Valor intrinseco Graham']), axis=1)
    df['Variacao_Nathalia'] = df.apply(
        lambda row: (calcular_variacao(row['Valor Atual'], row['Bazin']) + 
                     calcular_variacao(row['Valor Atual'], row['Valor intrinseco Graham'])) / 2, axis=1
    )

    df_html = df.copy()
    df_html['Bazin'] = df_html['Variacao_Bazin'].apply(lambda x: f'<span style="background-color:{cor_html(x)}; color:black;">{x:.2f}%</span>')
    df_html['Valor intrinseco Graham'] = df_html['Variacao_Graham'].apply(lambda x: f'<span style="background-color:{cor_html(x)}; color:black;">{x:.2f}%</span>')
    df_html['Metodo de Nathalia'] = df_html['Variacao_Nathalia'].apply(lambda x: f'<span style="background-color:{cor_html(x)}; color:black;">{x:.2f}%</span>')

    data_formatada = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    file_path = ARQUIVOS_DIR / f'saida_{data_formatada}.html'

    try:
        with open(file_path, 'w', encoding='utf-8') as htmlfile:
            htmlfile.write('<html>\n<head>\n<meta charset="UTF-8">\n<style>\ntable {border-collapse: collapse;}\n')
            htmlfile.write('td, th {border: 1px solid black; padding: 8px; text-align: center;}\n')
            htmlfile.write('</style>\n</head>\n<body>\n')

            htmlfile.write('<h2>Índices Utilizados:</h2>\n')
            htmlfile.write('<p><strong>Valor Intrínseco (Graham):</strong> Calculado a partir da fórmula &radic;(12 * LPA * VPA).</p>\n')
            htmlfile.write('<p><strong>Bazin:</strong> Calculado através da fórmula (LPA * Payout / 100) / 0.07.</p>\n')
            htmlfile.write('<p><strong>Índice de Nathalia:</strong> Média ponderada das variações percentuais.</p>\n')

            htmlfile.write('<table>\n<tr><th>Ação</th><th>Bazin</th><th>Graham</th><th>Nathalia</th></tr>\n')
            for _, row in df_html.iterrows():
                htmlfile.write(f'<tr><td>{row["Ticker"]}</td>')
                htmlfile.write(f'<td>{row["Bazin"]}</td>')
                htmlfile.write(f'<td>{row["Valor intrinseco Graham"]}</td>')
                htmlfile.write(f'<td>{row["Metodo de Nathalia"]}</td></tr>\n')

            htmlfile.write('</table>\n</body>\n</html>')
        logger.info("HTML gerado com sucesso em: %s", file_path)
    except Exception as e:
        logger.exception("Erro ao gerar HTML: %s", e)

def main() -> None:
    """Entry point da rotina de algoritmos."""
    logger.info("Executando algoritmos...")
    df_vi = aplicar_valor_intrinseco()
    gerar_html(df_vi)

if __name__ == '__main__':
    main()