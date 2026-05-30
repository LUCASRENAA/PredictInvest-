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

    # Só adiciona o xlabel se ele não for vazio
    if xlabel:
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
    """Posiciona o painel no canto superior com mais espaço vazio acima das barras."""
    media, mediana, moda, maximo, minimo = estatisticas
    texto_estatisticas = (
        r"$\bf{Média:}$" + f" {media:.2f}\n"
        r"$\bf{Mediana:}$" + f" {mediana:.2f}\n"
        r"$\bf{Moda:}$" + f" {moda if isinstance(moda, str) else f'{moda:.2f}'}\n"
        r"$\bf{Máximo:}$" + f" {maximo:.2f}\n"
        r"$\bf{Mínimo:}$" + f" {minimo:.2f}"
    )

    patches = ax.patches
    _, ymax = ax.get_ylim()

    if not patches:
        x_pos, y_pos, ha, va = 0.02, 0.95, "left", "top"
    else:
        xlim = ax.get_xlim()
        x_range = xlim[1] - xlim[0]

        # Divide em terço esquerdo, terço central e terço direito
        x_terco_esq = xlim[0] + x_range * 0.33
        x_terco_dir = xlim[0] + x_range * 0.67

        # Soma alturas empilhadas por posição X em cada região
        alturas: Dict[float, float] = {}
        for patch in patches:
            bx = patch.get_x() + patch.get_width() / 2
            h = patch.get_height()
            if h > 0:
                alturas[bx] = alturas.get(bx, 0) + h

        def max_altura_regiao(x_ini: float, x_fim: float) -> float:
            vals = [h for bx, h in alturas.items() if x_ini <= bx <= x_fim]
            return max(vals, default=0)

        max_esq = max_altura_regiao(xlim[0], x_terco_esq)
        max_dir = max_altura_regiao(x_terco_dir, xlim[1])

        # Escolhe o canto superior com mais espaço acima das barras
        if (ymax - max_esq) >= (ymax - max_dir):
            x_pos, ha = 0.02, "left"
        else:
            x_pos, ha = 0.98, "right"

        max_escolhido = max_esq if ha == "left" else max_dir
        if max_escolhido / ymax > 0.90:
            y_pos, va = 0.05, "bottom"
        else:
            y_pos, va = 0.95, "top"

    (
        ax.text(
            x_pos,
            y_pos,
            texto_estatisticas,
            transform=ax.transAxes,
            fontsize=11,
            horizontalalignment=ha,
            verticalalignment=va,
            bbox=dict(
                boxstyle="round,pad=0.5",
                edgecolor="#cccccc",
                facecolor="#ffffff",
                alpha=0.9,
            ),
        ),
    )


def plotar_todos_graficos(
    data: pd.DataFrame,
    estatisticas: Tuple[float, float, Any, float, float],
    ano_atual: int,
    mapeamento_cores: Dict[str, Any],
    paleta_heatmap: str,
) -> plt.Figure:
    """Renderiza a grade 2x2 de subplots compilando dividendos e retornos em figura de alta dimensão."""
    if data.empty:
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, "Nenhum dado para exibir", ha="center", va="center")
        return fig

    # Configuração da figura para o layout 2x2
    fig = plt.figure(figsize=(24, 16))
    gs = fig.add_gridspec(2, 2, wspace=0.15, hspace=0.4)

    ncols_legenda = min(6, len(data.columns))

    # ==========================================================
    # Gráfico 1: Barras empilhadas (Topo Esquerda)
    # ==========================================================
    ax1 = fig.add_subplot(gs[0, 0])
    data.plot(
        kind="bar",
        stacked=True,
        color=[mapeamento_cores.get(col, "gray") for col in data.columns],
        ax=ax1,
        width=0.75,
    )
    configurar_grafico(
        ax1,
        f"Previsão de Dividendos Mensais - {ano_atual}",
        "",
        "Valor (R$)",
        xticks=data.index,
        rotation=45,
    )
    adicionar_estatisticas(ax1, estatisticas)
    ax1.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.15),
        ncol=ncols_legenda,
        frameon=False,
    )

    # ==========================================================
    # Gráfico 2: Linhas para cada ticker (Topo Direita)
    # ==========================================================
    ax2 = fig.add_subplot(gs[0, 1])
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
        "",
        "Valor (R$)",
        xticks=data.index,
        rotation=45,
    )
    ax2.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.15),
        ncol=ncols_legenda,
        frameon=False,
    )

    # ==========================================================
    # Gráfico 3: Proporção de Dividendos - Donut (Baixo Esquerda)
    # ==========================================================
    ax4 = fig.add_subplot(gs[1, 0])
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

        wedges, texts = ax4.pie(
            soma_por_ticker,
            colors=cores_pizza,
            startangle=140,
            wedgeprops={
                "edgecolor": "white",
                "linewidth": 2,
            },
        )

        centro_branco = plt.Circle((0, 0), 0.50, fc="white")
        ax4.add_artist(centro_branco)

        # Monta a lista de textos para a legenda
        total_dividendos = soma_por_ticker.sum()
        legend_labels = []

        for ticker, valor in soma_por_ticker.items():
            pct = (valor / total_dividendos) * 100
            valor_fmt = (
                f"{valor:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
            )
            legend_labels.append(f"{ticker}: R$ {valor_fmt} ({pct:.1f}%)")

        ax4.legend(
            wedges,
            legend_labels,
            loc="center left",
            bbox_to_anchor=(-0.1, 0.5),
            frameon=False,
            fontsize=11,
            title_fontsize=12,
        )

        ax4.set_title(
            f"Proporção de Dividendos - {ano_atual}",
            pad=20,
            fontsize=14,
            fontweight="bold",
        )
        ax4.axis("equal")

    # ==========================================================
    # Gráfico 4: Mapa de Calor / Heatmap (Baixo Direita)
    # ==========================================================
    ax3 = fig.add_subplot(gs[1, 1])
    sns.heatmap(
        data.T,
        cmap=paleta_heatmap,
        annot=True,
        fmt=".0f",
        linewidths=0.5,
        ax=ax3,
        cbar_kws={"label": "Valor (R$)", "drawedges": False},
        annot_kws={"size": 9},
    )
    ax3.collections[0].colorbar.set_label(
        "Valor (R$)",
        fontweight="bold",
        labelpad=15,
    )
    ax3.set_title(
        f"Mapa de Calor dos Dividendos - {ano_atual}",
        pad=15,
        fontsize=14,
        fontweight="bold",
    )

    ax3.tick_params(axis="y", rotation=0)
    ax3.tick_params(axis="x", rotation=45)

    return fig

def cor_html(variacao: float) -> str:
    """Determina a cor HTML baseada no descasamento estrutural/estatístico usando o limite."""
    if variacao >= 10:
        return "green"      
    elif 0 <= variacao < 10:
        return "#b8860b"    
    else:
        return "red"
