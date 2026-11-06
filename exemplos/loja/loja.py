"""Módulo de exemplo (código "produzido pela equipe") usado para demonstrar o agente.

Contém dois defeitos intencionais que o agente deve apontar:
  * `ticket_medio` divide por zero quando a lista de pedidos está vazia;
  * `aplicar_cupom` não valida `total` e devolve `None` silenciosamente quando ele é `None`.
"""
from typing import Dict, List, Optional


class EstoqueInsuficiente(Exception):
    pass


def calcular_desconto(valor: float, percentual: float) -> float:
    """Aplica um desconto percentual (0 a 100) sobre o valor."""
    if valor < 0:
        raise ValueError("valor negativo")
    if percentual < 0 or percentual > 100:
        raise ValueError("percentual fora do intervalo")
    return round(valor * (1 - percentual / 100), 2)


def calcular_frete(peso_kg: float, distancia_km: int) -> float:
    """Frete: R$ 10 fixo + R$ 0,50/kg + R$ 0,10/km; acima de 30 kg cobra 20% a mais."""
    if peso_kg <= 0:
        raise ValueError("peso deve ser positivo")
    if distancia_km < 0:
        raise ValueError("distância negativa")
    frete = 10 + 0.5 * peso_kg + 0.1 * distancia_km
    if peso_kg > 30:
        frete *= 1.2
    return round(frete, 2)


def ticket_medio(pedidos: List[float]) -> float:
    """Valor médio por pedido."""
    return round(sum(pedidos) / len(pedidos), 2)


def aplicar_cupom(total: float, codigo: Optional[str]) -> float:
    cupons: Dict[str, float] = {"BEMVINDO10": 10.0, "FRETEGRATIS": 0.0}
    if codigo in cupons:
        return calcular_desconto(total, cupons[codigo])
    return total


def fechar_pedido(itens: Dict[str, int], frete: float = 0.0) -> float:
    """Soma os itens (preço unitário fixo de R$ 25) e o frete."""
    if not itens:
        raise ValueError("pedido sem itens")
    subtotal = sum(25.0 * q for q in itens.values())
    return round(calcular_desconto(subtotal, 0) + frete, 2)


class Estoque:
    def __init__(self) -> None:
        self._itens: Dict[str, int] = {}

    def adicionar(self, sku: str, quantidade: int) -> int:
        if quantidade <= 0:
            raise ValueError("quantidade deve ser positiva")
        self._itens[sku] = self._itens.get(sku, 0) + quantidade
        return self._itens[sku]

    def retirar(self, sku: str, quantidade: int) -> int:
        disponivel = self._itens.get(sku, 0)
        if quantidade > disponivel:
            raise EstoqueInsuficiente(sku)
        self._itens[sku] = disponivel - quantidade
        return self._itens[sku]
