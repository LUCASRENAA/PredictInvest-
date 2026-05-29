import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from typing import Optional, List, Tuple, Dict, Any

PALETAS_CORES = ["tab10", "Set2", "Set3", "Paired", "Accent", "Dark2"]
PALETAS_HEATMAP = [
    "YlGnBu",
    "Blues",
    "Greens",
    "Oranges",
    "Reds",
    "Purples",
    "coolwarm",
]
MESES_ORDENADOS_PORTUGUES = [
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro",
]


def configurar_grafico(
    ax: plt.Axes,
    titulo: str,
    xlabel: str,
    ylabel: str,
    xticks: Optional[List[str]] = None,
    rotation: int = 45,
    grid_visible: bool = True,
) -> None:
    """Configura os elementos comuns de um gráfico Mpl Axes."""
    ax.set_title(titulo, pad=15, fontsize=14, fontweight="bold")
    ax.set_xlabel(xlabel, fontweight="bold")
    ax.set_ylabel(ylabel, fontweight="bold")
    if xticks is not None:
        ax.set_xticks(range(len(xticks)))
        ax.set_xticklabels(xticks, rotation=rotation, ha="right")
    if grid_visible:
        ax.grid(True, linestyle="--", alpha=0.6)


def adicionar_estatisticas(
    ax: plt.Axes, estatisticas: Tuple[float, float, Any, float, float]
) -> None:
    """Fixa o painel de estatísticas textuais de forma flutuante para não sobrepor o gráfico."""
    media, mediana, moda, maximo, minimo = estatisticas
    texto_estatisticas = (
        f"Estatísticas Gerais (R$):\n"
        f"Média Mensal: {media:.2f}\n"
        f"Mediana: {mediana:.2f}\n"
        f"Moda: {moda if isinstance(moda, str) else f'{moda:.2f}'}\n"
        f"Máximo: {maximo:.2f}\n"
        f"Mínimo: {minimo:.2f}"
    )
    ax.text(
        0.02,
        0.95,
        texto_estatisticas,
        transform=ax.transAxes,
        fontsize=11,
        verticalalignment="top",
        bbox=dict(
            boxstyle="round,pad=0.5",
            edgecolor="#cccccc",
            facecolor="#ffffff",
            alpha=0.9,
        ),
    )


def plotar_todos_graficos(
    data: pd.DataFrame,
    estatisticas: Tuple[float, float, Any, float, float],
    ano_atual: int,
    mapeamento_cores: Dict[str, Any],
    paleta_heatmap: str,
) -> plt.Figure:
    """Renderiza o grid de múltiplos subplots compilando dividendos e retornos em figura de alta dimensão."""
    if data.empty:
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, "Nenhum dado para exibir", ha="center", va="center")
        return fig

    fig = plt.figure(figsize=(24, 32))
    gs = fig.add_gridspec(
        4, 2, height_ratios=[1.5, 1.5, 1.2, 1.2], wspace=0.25, hspace=0.4
    )

    # Gráfico 1: Barras empilhadas
    ax1 = fig.add_subplot(gs[0, :])
    data.plot(
        kind="bar",
        stacked=True,
        color=[mapeamento_cores.get(col, "gray") for col in data.columns],
        ax=ax1,
        width=0.75,
    )
    configurar_grafico(
        ax1,
        f"Previsão de Dividendos Mensais para {ano_atual}",
        "Mês",
        "Valor (R$)",
        xticks=data.index,
        rotation=0,
    )
    adicionar_estatisticas(ax1, estatisticas)
    ncols = min(10, len(data.columns))
    ax1.legend(
        title="Tickers",
        loc="upper center",
        bbox_to_anchor=(0.5, -0.1),
        ncol=ncols,
        frameon=False,
    )

    # Gráfico 2: Linhas para cada ticker
    ax2 = fig.add_subplot(gs[1, :])
    for ticker in data.columns:
        ax2.plot(
            data.index,
            data[ticker],
            marker="o",
            linewidth=2.5,
            markersize=8,
            label=ticker,
            color=mapeamento_cores.get(ticker, "gray"),
        )
    configurar_grafico(
        ax2,
        f"Evolução Mensal de Dividendos Acumulados - {ano_atual}",
        "Mês",
        "Valor (R$)",
    )
    ax2.legend(
        title="Tickers",
        loc="upper center",
        bbox_to_anchor=(0.5, -0.12),
        ncol=ncols,
        frameon=False,
    )

    # Gráfico 3: Matriz de Calor (Heatmap)
    ax3 = fig.add_subplot(gs[2, 0])
    sns.heatmap(
        data.T,
        cmap=paleta_heatmap,
        annot=True,
        fmt=".1f",
        linewidths=0.5,
        ax=ax3,
        cbar_kws={"label": "Valor (R$)"},
        annot_kws={"size": 9},
    )
    ax3.set_title(
        f"Mapa de Calor dos Dividendos - {ano_atual}",
        pad=15,
        fontsize=14,
        fontweight="bold",
    )
    ax3.set_xlabel("Mês", fontweight="bold")
    ax3.set_ylabel("Ticker", fontweight="bold")
    ax3.tick_params(axis="y", rotation=0)
    ax3.tick_params(axis="x", rotation=45)

    # Gráfico 4: Proporção de Dividendos (Donut Chart com Agrupamento e Legenda Lateral)
    ax4 = fig.add_subplot(gs[2, 1])
    soma_por_ticker = data.sum().sort_values(ascending=False)
    soma_por_ticker = soma_por_ticker[soma_por_ticker > 0]

    if not soma_por_ticker.empty:
        LIMITE_FATIAS = 7

        # Se houver muitos ativos, agrupa os menores em "Outros"
        if len(soma_por_ticker) > LIMITE_FATIAS:
            top_tickers = soma_por_ticker.iloc[:LIMITE_FATIAS]
            outros_sum = soma_por_ticker.iloc[LIMITE_FATIAS:].sum()
            soma_por_ticker = pd.concat(
                [top_tickers, pd.Series({"Outros": outros_sum})]
            )

        cores_pizza = [
            mapeamento_cores.get(ticker, "#95a5a6") for ticker in soma_por_ticker.index
        ]

        wedges, _, autotexts = ax4.pie(
            soma_por_ticker,
            autopct=lambda p: f"{p:.1f}%" if p > 3 else "",
            pctdistance=0.75,
            colors=cores_pizza,
            startangle=140,
            wedgeprops={
                "edgecolor": "white",
                "linewidth": 2,
            },
            textprops={"fontsize": 11, "fontweight": "bold"},
        )

        centro_branco = plt.Circle((0, 0), 0.50, fc="white")
        ax4.add_artist(centro_branco)

        for autotext in autotexts:
            autotext.set_color("white")
            autotext.set_fontsize(10)

        # Monta a lista de textos para a legenda combinando Ticker, Valor e Porcentagem
        total_dividendos = soma_por_ticker.sum()
        legend_labels = []
        for ticker, valor in soma_por_ticker.items():
            pct = (valor / total_dividendos) * 100
            valor_fmt = (
                f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            )
            legend_labels.append(f"{ticker}: R$ {valor_fmt} ({pct:.1f}%)")

        # Adiciona a legenda customizada ao lado direito do gráfico
        ax4.legend(
            wedges,
            legend_labels,
            title="Distribuição e Valores Estimados",
            loc="center left",
            bbox_to_anchor=(0.95, 0.5),
            frameon=False,
            fontsize=11,
            title_fontsize=12,
        )

        ax4.set_title("Proporção de Dividendos", pad=20, fontsize=14, fontweight="bold")
        ax4.axis("equal")

    # Gráfico 5: Total Mensal Consolidado (Bar Chart)
    ax5 = fig.add_subplot(gs[3, :])
    cores_mensais = sns.color_palette(paleta_heatmap, n_colors=12)
    total_mensal = data.sum(axis=1)
    bars = total_mensal.plot(
        kind="bar", color=cores_mensais, edgecolor="black", ax=ax5, width=0.7
    )
    configurar_grafico(
        ax5,
        f"Total Consolidado Mensal Previsto - {ano_atual}",
        "Mês",
        "Valor Total (R$)",
        xticks=data.index,
        rotation=0,
    )

    for bar in bars.patches:
        if bar.get_height() > 0:
            ax5.annotate(
                f"R$ {bar.get_height():.2f}",
                (bar.get_x() + bar.get_width() / 2.0, bar.get_height()),
                ha="center",
                va="bottom",
                xytext=(0, 8),
                textcoords="offset points",
                fontsize=10,
                fontweight="bold",
                rotation=45,
            )

    fig.tight_layout(pad=4.0, h_pad=5.0)
    return fig


def cor_html(variacao: float) -> str:
    """Determina a cor HTML baseada no descasamento estrutural/estatístico usando o limite."""
    if variacao >= 10:
        return "color: green;"
    elif 0 <= variacao < 10:
        return "color: #b8860b;"
    else:
        return "color: red;"
