import time
import random
import requests
import requests_cache
from bs4 import BeautifulSoup, PageElement
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import yfinance as yf
from pathlib import Path
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Configura o cache APENAS para a biblioteca 'requests' padrão (Dados de Mercado, Investidor10)
Path(".cache").mkdir(exist_ok=True)
requests_cache.install_cache(".cache/scraper_cache", expire_after=14400)


class ScraperBase:
    """Base scraper class providing common HTTP setup and Selenium context."""

    def __init__(self, use_selenium_fallback: bool = True):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.use_selenium_fallback = use_selenium_fallback

    def get_selenium_options(self) -> Options:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f"user-agent={self.headers['User-Agent']}")
        return options

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(
            (requests.exceptions.RequestException, requests.exceptions.Timeout)
        ),
    )
    def fetch_url(self, url: str, timeout: int = 15) -> requests.Response:
        """Fetches a URL using requests with exponential backoff on failure."""
        response = requests.get(url, headers=self.headers, timeout=timeout)
        response.raise_for_status()
        return response

    def get_html(self, url: str) -> BeautifulSoup | None:
        """Gets HTML via requests, falling back to Selenium if requested."""
        try:
            response = self.fetch_url(url)
            return BeautifulSoup(response.text, "html.parser")
        except Exception as e:
            logger.warning("Requests failed para %s: %s", url, e)
            if self.use_selenium_fallback:
                return self.get_html_with_selenium(url)
            return None

    def get_html_with_selenium(self, url: str) -> BeautifulSoup | None:
        """Gets HTML via headless Selenium."""
        try:
            with webdriver.Chrome(options=self.get_selenium_options()) as driver:
                driver.get(url)
                return BeautifulSoup(driver.page_source, "html.parser")
        except Exception as e:
            logger.exception("Selenium falhou para %s: %s", url, e)
            return None


class DividendScraper(ScraperBase):
    """Scraper logic specifically for dividends and tables."""

    def get_table_html(
        self,
        url: str,
        tabela_id: str | None = None,
    ) -> PageElement | None:
        """Busca o HTML de uma tabela (Requests -> Selenium)."""
        soup = self.get_html(url)
        if soup is None:
            return None
        return (
            soup.find("table", {"id": tabela_id}) if tabela_id else soup.find("table")
        )


class IndicatorScraper(ScraperBase):
    """Scraper logic specifically for stock indicators and payouts."""

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=2, min=4, max=20),
        retry=retry_if_exception_type(Exception),
        retry_error_callback=lambda retry_state: (
            0.0
        ),  # <- Se falhar 4 vezes, retorna 0.0 e não quebra o programa
    )
    def extrair_payout(self, ticker: str) -> float:
        """Extrai o payout ratio de uma ação usando a API do yfinance (com retry e jitter)."""
        time.sleep(random.uniform(1.0, 3.5))
        try:
            acao = yf.Ticker(f"{ticker}.SA")
            payout = acao.info.get("payoutRatio", 0.0)
            if payout is not None:
                return round(float(payout) * 100, 2)
            return 0.0
        except Exception as e:
            logger.warning(
                "Falha ao extrair payout para %s. Tentando novamente...", ticker
            )
            raise

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=2, min=4, max=20),
        retry=retry_if_exception_type(Exception),
        retry_error_callback=lambda retry_state: (
            None
        ),  # <- Se falhar 4 vezes, retorna None e não quebra o programa
    )
    def obter_valor_acao_brasileira(self, ticker: str) -> float | None:
        """Obtém o valor atual usando yfinance (com retry e jitter)."""
        time.sleep(random.uniform(0.5, 2.0))  # Espalha as threads
        try:
            acao = yf.Ticker(f"{ticker}.SA")
            dados = acao.history(period="1d")
            if not dados.empty:
                return round(float(dados["Close"].iloc[-1]), 2)
            return None
        except Exception as e:
            logger.warning(
                "Falha ao obter valor para %s. Tentando novamente...", ticker
            )
            raise

    def obter_indicadores_scrape(self, ticker: str) -> dict:
        """Scraping inicial da página da ação."""
        url = f"https://www.dadosdemercado.com.br/acoes/{ticker}"
        indicadores: dict = {}
        soup = self.get_html(url)

        if soup is not None:
            ratios = soup.find_all("tr", class_="level0")
            for tr in ratios:
                if isinstance(tr, PageElement):
                    continue
                tds = tr.find_all("td", class_="nw")
                if len(tds) >= 2:
                    indicador = tds[0].text.strip()
                    valor = tds[1].text.strip()
                    indicadores[indicador] = valor

        return indicadores
