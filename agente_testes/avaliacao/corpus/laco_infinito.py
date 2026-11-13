"""Defeito plantado: o laço nunca termina porque `restante` não é decrementado."""


def processar(fila: int) -> int:
    restante = fila
    processados = 0
    while restante >= 0:
        processados += 1
    return processados
