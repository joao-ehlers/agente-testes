"""Caso de análise incremental: só `dividir` foi alterada no diff."""


def somar(a: int, b: int) -> int:
    return a + b


def dividir(a: int, b: int) -> float:
    if b == 0:
        raise ValueError("divisor zero")
    return a / b
