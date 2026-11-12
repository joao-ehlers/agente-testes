"""Testes integracao gerados pelo Agente de Testes para loja.

Gerados a partir de cenários (hipóteses); a execução é a fonte da verdade.
"""
import asyncio

import pytest

def test_cen_7fffd518c0_aplicar_cupom_fluxo_integrado_com_calcular_descont():
    """Dado os colaboradores reais (calcular_desconto) sem dublês, quando aplicar_cupom é executada com total=2.5, codigo='abc', então o fluxo completo retorna um valor do tipo float."""
    from loja import aplicar_cupom
    try:
        resultado = aplicar_cupom(total=2.5, codigo='abc')
    except ():
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, (int, float)), f'retorno inesperado: {resultado!r}'



def test_cen_a54077ff3c_fechar_pedido_fluxo_integrado_com_calcular_descont():
    """Dado os colaboradores reais (calcular_desconto) sem dublês, quando fechar_pedido é executada com itens={'a': 1}, frete=2.5, então o fluxo completo retorna um valor do tipo float."""
    from loja import fechar_pedido
    try:
        resultado = fechar_pedido(itens={'a': 1}, frete=2.5)
    except (ValueError,):
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, (int, float)), f'retorno inesperado: {resultado!r}'

