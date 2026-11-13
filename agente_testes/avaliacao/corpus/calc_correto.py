"""Caso de controle: funções corretas, sem defeito plantado (mede falso positivo)."""
from typing import List


def dividir(a: float, b: float) -> float:
    """Divide a por b; divisor zero é rejeitado."""
    if b == 0:
        raise ValueError("divisão por zero")
    return a / b


def media(valores: List[float]) -> float:
    """Média aritmética; lista vazia resulta em 0.0."""
    if valores is None:
        raise TypeError("valores obrigatórios")
    if not valores:
        return 0.0
    return sum(valores) / len(valores)


def limitar(valor: int, minimo: int, maximo: int) -> int:
    """Restringe o valor ao intervalo [minimo, maximo]."""
    if minimo > maximo:
        raise ValueError("intervalo inválido")
    return max(minimo, min(valor, maximo))
