import csv
from datetime import datetime
import concurrent.futures
from pathlib import Path
import pandas as pd

from config import ACOES_CSV, INDICADORES_CSV
from src.utils.logger import get_logger
from src.utils.scraper import IndicatorScraper
from src.utils.data_processor import converter_valor_para_float

logger = get_logger(__name__)
scraper = IndicatorScraper()


def processar_linha_acoes(linha: dict, campos_permitidos: list) -> dict:
    """Processa uma única ação e retorna os resultados para compor o CSV/DataFrame."""
    ticker = str(linha.get("Ticker") or "").strip()
    quantidade = str(linha.get("Quantidade") or "").strip()
    setor = str(linha.get("Setor") or "").strip()

    if not ticker or not quantidade:
        logger.info("Dados inválidos na linha: %s", linha)
        return None

    logger.info("Processando ação: %s", ticker)

    indicadores_str = scraper.obter_indicadores_scrape(ticker)

    # Converte dicionário str para float
    indicadores_float = {
        k: converter_valor_para_float(v)
        for k, v in indicadores_str.items()
        if converter_valor_para_float(v) is not None
    }

    valor_acao_brasil = scraper.obter_valor_acao_brasileira(ticker)
    payout = scraper.extrair_payout(ticker)

    linha_indicadores = {
        "Ticker": ticker,
        "Quantidade": quantidade,
        "Setor": setor,
        "Data de atualização": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Valor Atual": valor_acao_brasil,
        "PAYOUT": payout,
    }
    linha_indicadores.update(indicadores_float)

    linha_filtrada = {
        k: v for k, v in linha_indicadores.items() if k in campos_permitidos
    }
    return linha_filtrada


def processar_acoes() -> pd.DataFrame:
    """Processa as ações usando ThreadPoolExecutor e retorna um DataFrame."""
    campos_permitidos = [
        "Ticker",
        "Quantidade",
        "Setor",
        "Data de atualização",
        "Valor Atual",
        "PAYOUT",
        "LPA",
        "VPA",
        "P/L",
        "P/VP",
        "P/SR",
        "ROE",
        "ROA",
        "EBITDA",
        "Margem bruta",
        "Margem líquida",
        "Margem EBITDA",
        "Margem operacional",
        "P/CF",
        "Liquidez corrente",
        "Liquidez imediata",
        "Liquidez seca",
        "Giro do ativo",
        "Endividamento geral",
        "Ativo por ação",
        "Dívida bruta",
        "Dívida líquida",
        "Capital de giro",
        "Receita líquida por ação",
        "EBIT por ação",
        "Margem EBIT",
    ]

    ACOES_CSV_PATH = Path(ACOES_CSV)
    if not ACOES_CSV_PATH.exists():
        logger.error("Erro: Arquivo não encontrado - %s", ACOES_CSV_PATH)
        return pd.DataFrame()

    try:
        linhas = []
        with open(ACOES_CSV_PATH, newline="", encoding="utf-8") as arquivo_acoes:
            leitor_csv = csv.DictReader(arquivo_acoes)
            linhas = list(leitor_csv)

        resultados = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futuros = {
                executor.submit(processar_linha_acoes, linha, campos_permitidos): linha
                for linha in linhas
            }
            for futuro in concurrent.futures.as_completed(futuros):
                res = futuro.result()
                if res:
                    resultados.append(res)

        caminho_saida = Path(INDICADORES_CSV)
        caminho_saida.parent.mkdir(parents=True, exist_ok=True)

        with open(
            caminho_saida, mode="w", newline="", encoding="utf-8"
        ) as arquivo_indicadores:
            escritor_csv = csv.DictWriter(
                arquivo_indicadores, fieldnames=campos_permitidos
            )
            escritor_csv.writeheader()
            for r in resultados:
                escritor_csv.writerow(r)

        return pd.DataFrame(resultados)

    except Exception as e:
        logger.exception("Erro inesperado: %s", e)
        return pd.DataFrame()


def main() -> None:
    """Entry point para o script isolado."""
    logger.info("Iniciando coleta de indicadores...")
    processar_acoes()


if __name__ == "__main__":
    main()
