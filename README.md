# PredictInvest - Análise e Previsão de Ações e FIIs

O **PredictInvest** é um pipeline automatizado de extração, análise e visualização de dados do mercado financeiro brasileiro. Ele executa previsões de dividendos, coleta indicadores fundamentalistas de forma assíncrona e aplica algoritmos clássicos de valuation (Bazin e Graham) para encontrar o valor intrínseco e o potencial de valorização (upside) dos ativos.

## Funcionalidades

- **Previsão de Dividendos:** Calcula estatísticas e gera dashboards visuais avançados (Gráficos de Barras, Heatmaps, Donut Charts) estimando os pagamentos do ano atual baseados no histórico.

- **Scraping Resiliente:** Utiliza concorrência (`ThreadPoolExecutor`), Cache local dinâmico e sistema anti-bloqueio com retentativas exponenciais (`Tenacity`) para contornar Rate Limits.

- **Valuation Automático:** Calcula o Preço Teto de Bazin, o Valor Intrínseco de Graham e uma média customizada, gerando um relatório em HTML fácil de ler.

## Pré-requisitos e Configuração

1. Renomeie ou crie um arquivo `.env` baseado nas variáveis listadas em `config.py`.
2. Crie (ou atualize) os arquivos `acoes.csv` e `fiis.csv` na raiz do projeto.

## 🐳 Como Executar com Docker (Recomendado)

A aplicação foi conteinerizada para garantir que o Chromium (usado pelo Selenium no modo headless) e todas as dependências do Python rodem perfeitamente em qualquer sistema operacional.

**1. Construa e suba o ambiente (em segundo plano):**

```bash
docker compose up -d --build
```

**2. Execute o pipeline completo:**

```bash
docker compose run --rm predictinvest python -m src.main --all
```

## 💻 Como Executar Localmente (Python Nativo)

Caso prefira rodar sem Docker, certifique-se de ter o Python 3.11+ e o Google Chrome instalados na sua máquina.

**1. Instale as dependências:**

```bash
pip install -r requirements.txt
```

**2. Execute os comandos a partir da raiz do projeto:**

```bash
python -m src.main --all
```


* Executar apenas a previsão de dividendos:

    ```bash
    python -m src.main --previsao_dividendos
    ```

* Executar apenas a coleta de indicadores:

    ```bash
    python -m src.main --pegar_indicadores
    ```

* Executar apenas os algoritmos (Graham/Bazin):

    ```bash
    python -m src.main --algoritmos
    ```

Para manter o repositório organizado, todas as saídas geradas pelo sistema são salvas automaticamente na pasta **`arquivos/`** (que é criada dinamicamente na primeira execução). Os arquivos de log detalhados ficam na pasta **`logs/`**.