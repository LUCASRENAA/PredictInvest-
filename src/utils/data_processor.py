import math
import statistics
import pandas as pd
from typing import Optional, Dict, Any, Tuple
from collections import Counter


def limpar_e_arredondar(valor: Any) -> float:
    """Limpa strings financeiras e retorna float arredondado a 2 casas decimais."""
    try:
        if pd.isna(valor):
            return 0.0
        valor_limpo = str(valor).replace("*", "").replace(",", ".")
        if valor_limpo.count(".") > 1:
            partes = valor_limpo.split(".")
            valor_limpo = partes[0] + "." + "".join(partes[1:])
        return round(float(valor_limpo), 2)
    except (ValueError, TypeError):
        return 0.0


def converter_valor_para_float(valor: str) -> Optional[float]:
    """Converte string com caracteres ilegais para float limpo."""
    valor_limpo = "".join(
        c if c.isdigit() or c in [".", ","] else " " for c in valor
    ).replace(",", ".")
    try:
        return float(valor_limpo)
    except ValueError:
        return None


def converter_para_float(
    valor: Any, substituicoes: Optional[Dict[str, str]] = None
) -> float:
    """Converte valor string para float aplicando substituições prévias."""
    if pd.isna(valor) or valor is None:
        return 0.0
    valor_str = str(valor)
    if substituicoes:
        for old, new in substituicoes.items():
            valor_str = valor_str.replace(old, new)
    try:
        return float(valor_str)
    except ValueError:
        return 0.0


def calcular_estatisticas(data: pd.Series) -> Tuple[float, float, Any, float, float]:
    """Calcula parâmetros estatísticos para uma série de dados."""
    data_list = data.tolist()
    if not data_list:
        return 0.0, 0.0, "N/A", 0.0, 0.0

    media = float(statistics.mean(data_list))
    mediana = float(statistics.median(data_list))
    contagem = Counter(data_list)
    mais_comum = contagem.most_common(1)[0][1]
    modos = [valor for valor, freq in contagem.items() if freq == mais_comum]
    moda = modos[0] if len(modos) == 1 else "No unique mode"

    return media, mediana, moda, max(data_list), min(data_list)


def calcular_valor_intrinseco(lpa: Optional[float], vpa: Optional[float]) -> float:
    """Calcula valor da fórmula Graham original (22.5)."""
    if not lpa or not vpa or lpa <= 0 or vpa <= 0:
        return 0.0
    return math.sqrt(22.5 * lpa * vpa)


def calcular_valor_intrinseco_12(lpa: Optional[float], vpa: Optional[float]) -> float:
    """Implementa o calculo Graham com fator original de 12 configurado."""
    if not lpa or not vpa or lpa < 0 or vpa < 0:
        return 0.0
    return math.sqrt(12 * lpa * vpa)


def calcular_bazin(lpa: Optional[float], payout: Optional[float]) -> float:
    """Calcula valor intrínseco da ação por meio de Bazin."""
    if lpa is None or payout is None:
        return 0.0
    return (lpa * payout / 100) / 0.07


def calcular_variacao(valor_atual: float, valor_comparado: float) -> float:
    """Descreve quão longe do preço teto a ação está presentemente."""
    if not valor_atual or pd.isna(valor_atual) or not valor_comparado:
        return 0.0

    variacao = ((valor_comparado - valor_atual) / valor_atual) * 100
    if abs(variacao) < 0.01 or variacao <= -100 or variacao >= 10000:
        return 0.0

    return round(float(variacao), 2)
