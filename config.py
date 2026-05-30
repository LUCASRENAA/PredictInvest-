import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# App paths Configuration
ACOES_CSV = BASE_DIR / os.getenv('ACOES_CSV', 'acoes.csv')
FIIS_CSV = BASE_DIR / os.getenv('FIIS_CSV', 'fiis.csv')
INDICADORES_CSV = BASE_DIR / os.getenv('INDICADORES_CSV', 'arquivos/indicadores.csv')
VALOR_INTRINSECO_CSV = BASE_DIR / os.getenv('VALOR_INTRINSECO_CSV', 'arquivos/valor_intrinseco.csv')
ACOES_ALL_CSV = BASE_DIR / "arquivos/acoes_all.csv"

ARQUIVOS_DIR = BASE_DIR / "arquivos"
ARQUIVOS_DIR.mkdir(parents=True, exist_ok=True)

# Web API Configuration 
WEB_API_URL = os.getenv('WEB_API_URL', 'http://127.0.0.1:8000')
WEB_API_USERNAME = os.getenv('WEB_API_USERNAME', 'admin')
WEB_API_PASSWORD = os.getenv('WEB_API_PASSWORD', 'admin')
