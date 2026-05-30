import seaborn as sns
from pathlib import Path
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from io import StringIO
from typing import List, Tuple
import concurrent.futures
import random

from config import ACOES_CSV, FIIS_CSV, ARQUIVOS_DIR
from src.utils.logger import get_logger
from src.utils.scraper import DividendScraper
from src.utils.data_processor import limpar_e_arredondar, calcular_estatisticas
from src.utils.visualizer import (
    plotar_todos_graficos,
    PALETAS_CORES,
    PALETAS_HEATMAP,
    MESES_ORDENADOS_PORTUGUES,
)

logger = get_logger(__name__)
scraper = DividendScraper()


def _extrair_tabela_dinamica(soup, quantidade: int) -> pd.Series:
    """Função auxiliar para varrer todas as tabelas e achar a de dividendos."""
    if soup is None:
        return None
    try:
        ano_atual = datetime.now().year
        # O Pandas varre o HTML inteiro e traz todas as tabelas presentes na página
        tabelas = pd.read_html(StringIO(str(soup)), decimal=",", thousands=".")

        for tabela in tabelas:
            # Padroniza as colunas em minúsculo para evitar erros de formatação do site
            cols_lower = [str(c).lower().strip() for c in tabela.columns]

            # Verifica se a tabela atual é a de dividendos procurando colunas chave
            if "pagamento" in cols_lower and "valor" in cols_lower:
                tabela.columns = cols_lower
                tabela.rename(
                    columns={"pagamento": "Pagamento", "valor": "Valor"}, inplace=True
                )

                tabela["Pagamento"] = pd.to_datetime(
                    tabela["Pagamento"], format="%d/%m/%Y", errors="coerce"
                )

                # Filtra apenas o ano anterior
                dados_ano_anterior = tabela[
                    tabela["Pagamento"].dt.year == (ano_atual - 1)
                ].copy()

                if not dados_ano_anterior.empty:
                    dados_ano_anterior["Valor Total"] = (
                        dados_ano_anterior["Valor"].apply(limpar_e_arredondar)
                        * quantidade
                    )
                    soma_meses = dados_ano_anterior.groupby(
                        dados_ano_anterior["Pagamento"].dt.month
                    )["Valor Total"].sum()
                    return soma_meses.reindex(range(1, 13), fill_value=0.0)
                else:
                    return pd.Series([0.0] * 12, index=range(1, 13))

    except ValueError:
        pass  # Disparado quando o pd.read_html não acha tags <table> no HTML
    except Exception as e:
        logger.exception("Erro ao extrair dados da tabela: %s", e)

    return None


def obter_dividendos(ticket: str, quantidade: int, url: str) -> pd.Series:
    """Busca dividendos com fallback automático para Javascript/Selenium."""
    logger.info("Obtendo dividendos de: %s", ticket)

    # 1. Tenta carregar rápido via requests
    soup = scraper.get_html(url)
    resultado = _extrair_tabela_dinamica(soup, quantidade)

    # 2. Se falhou (tabela oculta por Javascript ou mudança estrutural), força o Selenium
    if resultado is None and scraper.use_selenium_fallback:
        logger.info(
            "Tabela não achada para %s. Forçando renderização via Selenium...", ticket
        )
        soup_selenium = scraper.get_html_with_selenium(url)
        resultado = _extrair_tabela_dinamica(soup_selenium, quantidade)

    if resultado is not None:
        return resultado

    logger.warning("Sem tabela ou falha para ticket %s.", ticket)
    return pd.Series([0.0] * 12, index=range(1, 13))


def obter_dividendos_acao(ticket: str, quantidade: int) -> pd.Series:
    """Busca dividendos de Ações."""
    url = f"https://www.dadosdemercado.com.br/acoes/{ticket}/dividendos"
    return obter_dividendos(ticket, quantidade, url)


def obter_dividendos_fii(ticket: str, quantidade: int) -> pd.Series:
    """Busca dividendos de FIIs."""
    url = f"https://investidor10.com.br/fiis/{ticket}/"
    return obter_dividendos(ticket, quantidade, url)


def ler_e_obter_dividendos(
    caminho_arquivo: str | Path, is_fii: bool = False
) -> Tuple[List[str], List[pd.Series]]:
    """Carrega dados dos FIIs ou Ações do CSV fornecido e faz raspagem da previsão (concorrente)."""
    tickers: List[str] = []
    previsto_mensal: List[pd.Series] = []
    caminho = Path(caminho_arquivo)
    if not caminho.exists():
        logger.warning("Arquivo %s não encontrado.", caminho_arquivo)
        return tickers, previsto_mensal

    try:
        tasks = []
        with open(caminho, "r", encoding="utf-8") as arquivo_csv:
            import csv

            leitor_csv = csv.reader(arquivo_csv)
            next(leitor_csv, None)
            for linha in leitor_csv:
                if len(linha) >= 2:
                    ticket = linha[0].strip()
                    quantidade = int(linha[1].strip() or 0)
                    tasks.append((ticket, quantidade))

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            if is_fii:
                futures = {
                    executor.submit(obter_dividendos_fii, t, q): t for t, q in tasks
                }
            else:
                futures = {
                    executor.submit(obter_dividendos_acao, t, q): t for t, q in tasks
                }

            for futuro in concurrent.futures.as_completed(futures):
                ticket = futures[futuro]
                res = futuro.result()
                tickers.append(ticket)
                previsto_mensal.append(res)
    except Exception as e:
        logger.exception("Erro ao ler %s: %s", caminho_arquivo, e)
    return tickers, previsto_mensal


def main() -> None:
    """Função principal da rotina de previsão de dividendos."""
    logger.info("Iniciando Previsão de Dividendos...")
    tickers_acoes, prev_acoes = ler_e_obter_dividendos(ACOES_CSV, is_fii=False)
    tickers_fiis, prev_fiis = ler_e_obter_dividendos(FIIS_CSV, is_fii=True)

    todas_prev = prev_acoes + prev_fiis
    tickers = tickers_acoes + tickers_fiis

    if not tickers:
        logger.info("Nenhum ticker processado. Encerrando previsão de dividendos.")
        return

    todos_previstos = pd.concat(todas_prev, axis=1)
    todos_previstos.columns = tickers
    todos_previstos.index = MESES_ORDENADOS_PORTUGUES
    todos_previstos_limpos = todos_previstos.fillna(0.0)

    todos_previstos_limpos["TOTAL"] = todos_previstos_limpos.sum(axis=1)
    estatisticas_total = calcular_estatisticas(todos_previstos_limpos["TOTAL"])
    logger.info("Estatísticas do total de dividendos: %s", estatisticas_total)

    todos_previstos_limpos = todos_previstos_limpos.drop(columns=["TOTAL"])

    paleta_escolhida = random.choice(PALETAS_CORES)
    paleta_heatmap = random.choice(PALETAS_HEATMAP)
    mapeamento_cores = {
        ticker: cor
        for ticker, cor in zip(
            tickers, sns.color_palette(paleta_escolhida, len(tickers))
        )
    }

    ano_atual = datetime.now().year
    fig_todos = plotar_todos_graficos(
        todos_previstos_limpos,
        estatisticas_total,
        ano_atual,
        mapeamento_cores,
        paleta_heatmap,
    )

    data_formatada = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    todos_graficos_img = f"todos_graficos_{data_formatada}.png"

    output_file = ARQUIVOS_DIR / todos_graficos_img
    plt.savefig(output_file, format="png", bbox_inches="tight")
    logger.info("Gráfico salvo em %s", output_file)


if __name__ == "__main__":
    main()
