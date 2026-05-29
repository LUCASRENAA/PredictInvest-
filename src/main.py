import argparse
import requests
import pandas as pd
import investpy as inv

from config import WEB_API_URL, WEB_API_USERNAME, WEB_API_PASSWORD, ACOES_ALL_CSV
from src.utils.logger import get_logger
from src.previsao_dividendos import main as run_previsao
from src.pegar_indicadores import processar_acoes as run_indicadores
from src.algoritmos import aplicar_valor_intrinseco, gerar_html

logger = get_logger(__name__)

def get_brazilian_stocks() -> pd.DataFrame:
    """Obtém todas as ações do Brasil através do investpy."""
    try:
        return inv.stocks.get_stocks(country='brazil')
    except RuntimeError as e:
        logger.exception("Erro no investpy (site Investing.com pode ter bloqueado/mudado a API): %s", e)
        return pd.DataFrame()

def get_access_token(username: str, password: str) -> str:
    """Autentica na API e obtém o token de acesso."""
    url = f'{WEB_API_URL}/api/token/'
    try:
        response = requests.post(url, json={"username": username, "password": password}, timeout=10)
        if response.status_code == 200:
            return response.json().get('access', '')
    except requests.exceptions.RequestException as e:
        logger.exception("Erro ao conectar com %s: %s", url, e)
    return ""

def create_ticket(access_token: str, ticket: str, name: str) -> requests.Response:
    """Envia um POST para criar um ticket."""
    url = f'{WEB_API_URL}/ticket/'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    body = {"ticket": ticket, "name": name}
    return requests.post(url, headers=headers, json=body, timeout=10)

def processar_stocks_sem_token(brazilian_stocks: pd.DataFrame) -> None:
    """Processa as ações e salva em um arquivo CSV de rascunho (acoes_all.csv) quando não há token."""
    if brazilian_stocks.empty: return
    
    with open(ACOES_ALL_CSV, "a", encoding="utf-8") as file:
        for _, stock in brazilian_stocks.iterrows():
            ticket = stock['symbol']
            file.write(f"{ticket},,\n")

def atualizar_web() -> None:
    """Atualiza as ações no sistema web ou localmente se falhar conexão."""
    brazilian_stocks = get_brazilian_stocks()
    if brazilian_stocks.empty:
        logger.info("Nenhuma ação retornada para processar.")
        return

    access_token = get_access_token(WEB_API_USERNAME, WEB_API_PASSWORD)
    
    if access_token:
        logger.info("Token de Acesso obtido.")
        for _, stock in brazilian_stocks.iterrows():
            name, ticket = stock['name'], stock['symbol']
            try:
                response = create_ticket(access_token, ticket, name)

                if response.status_code == 201:
                    logger.info("Ticket criado para %s", name)
                elif response.status_code == 401:
                    logger.info("Token expirado. Renovando tokem...")
                    access_token = get_access_token(WEB_API_USERNAME, WEB_API_PASSWORD)
                    if access_token:
                        response_retry = create_ticket(access_token, ticket, name)
                        if response_retry.status_code == 201:
                            logger.info("Ticket criado para %s", name)
                        else:
                            logger.error("Falha ao criar ticket para %s após renovação.", name)
                    else:
                        logger.error("Falha ao renovar o token.")
                        break
                else:
                    logger.error("Falha ao criar ticket para %s: %s", name, response.text)
            except Exception as e:
                logger.exception("Erro ao criar ticket para %s: %s", name, e)
    else:
        logger.error("Falha na autenticação web. Processando as ações offline.")
        processar_stocks_sem_token(brazilian_stocks)

def run_algoritmos(df_indicadores: pd.DataFrame = None) -> None:
    logger.info("Executando algoritmos...")
    df_vi = aplicar_valor_intrinseco(df_indicadores)
    gerar_html(df_vi)
    
def parse_arguments(args_list=None):
    parser = argparse.ArgumentParser(
        description="Ferramentas para análise de investimentos: previsão de dividendos, indicadores e algoritmos (Graham/Bazin).",
        epilog="Consulte o README.md para mais informações."
    )

    parser.add_argument("--previsao_dividendos", "-pd", action="store_true", help="Executar a previsão de dividendos.")
    parser.add_argument("--pegar_indicadores", "-pi", action="store_true", help="Coletar os indicadores das ações.")
    parser.add_argument("--algoritmos", "-pa", action="store_true", help="Executar algoritmos de Bazin e Graham.")
    parser.add_argument("--atualizar_web", "-aw", action="store_true", help="Coletar as ações para o sistema web.")
    parser.add_argument("--all", action="store_true", help="Executar todas as opções.")

    return parser, parser.parse_args(args_list)

def main() -> None:
    """Função principal para gerenciar os argumentos e executar as opções."""
    parser, args = parse_arguments()

    if args.all:
        logger.info("Executando todas as opções pipeline...")
        run_previsao()
        df_indicadores = run_indicadores()
        run_algoritmos(df_indicadores)
    else:
        executed_any = False
        if args.previsao_dividendos:
            run_previsao()
            executed_any = True
        if args.pegar_indicadores:
            logger.info("Iniciando coleta de indicadores...")
            run_indicadores()
            executed_any = True
        if args.algoritmos:
            run_algoritmos()
            executed_any = True
        if args.atualizar_web:
            atualizar_web()
            executed_any = True
            
        if not executed_any:
            parser.print_help()

if __name__ == "__main__":
    main()