"""Defeito plantado: lista vazia gera ZeroDivisionError (o requisito pede 0.0)."""
from typing import List


def media(valores: List[float]) -> float:
    return sum(valores) / len(valores)
