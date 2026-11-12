"""Testes validacao_entrada gerados pelo Agente de Testes para loja.

Gerados a partir de cenários (hipóteses); a execução é a fonte da verdade.
"""
import asyncio

import pytest

def test_cen_2fd6225bad_calcular_desconto_valor_none_rejeitado():
    """Dado valor=None (tipo declarado float), quando calcular_desconto é executada, então deve rejeitar a entrada com TypeError/ValueError (ou uma exceção documentada: ValueError) em vez de prosseguir."""
    from loja import calcular_desconto
    with pytest.raises((TypeError, ValueError)):
        resultado = calcular_desconto(valor=None, percentual=2.5)
        pytest.fail(f'entrada inválida aceita sem validação; retorno: {resultado!r}')



def test_cen_91bc8932af_calcular_frete_peso_kg_none_rejeitado():
    """Dado peso_kg=None (tipo declarado float), quando calcular_frete é executada, então deve rejeitar a entrada com TypeError/ValueError (ou uma exceção documentada: ValueError) em vez de prosseguir."""
    from loja import calcular_frete
    with pytest.raises((TypeError, ValueError)):
        resultado = calcular_frete(peso_kg=None, distancia_km=7)
        pytest.fail(f'entrada inválida aceita sem validação; retorno: {resultado!r}')



def test_cen_69b177af57_ticket_medio_pedidos_none_rejeitado():
    """Dado pedidos=None (tipo declarado List[float]), quando ticket_medio é executada, então deve rejeitar a entrada com TypeError/ValueError em vez de prosseguir."""
    from loja import ticket_medio
    with pytest.raises((TypeError, ValueError)):
        resultado = ticket_medio(pedidos=None)
        pytest.fail(f'entrada inválida aceita sem validação; retorno: {resultado!r}')



def test_cen_56f2c1b86e_aplicar_cupom_total_none_rejeitado():
    """Dado total=None (tipo declarado float), quando aplicar_cupom é executada, então deve rejeitar a entrada com TypeError/ValueError em vez de prosseguir."""
    from loja import aplicar_cupom
    with pytest.raises((TypeError, ValueError)):
        resultado = aplicar_cupom(total=None, codigo='abc')
        pytest.fail(f'entrada inválida aceita sem validação; retorno: {resultado!r}')



def test_cen_7bc33297ec_fechar_pedido_itens_none_rejeitado():
    """Dado itens=None (tipo declarado Dict[str, int]), quando fechar_pedido é executada, então deve rejeitar a entrada com TypeError/ValueError (ou uma exceção documentada: ValueError) em vez de prosseguir."""
    from loja import fechar_pedido
    with pytest.raises((TypeError, ValueError)):
        resultado = fechar_pedido(itens=None, frete=2.5)
        pytest.fail(f'entrada inválida aceita sem validação; retorno: {resultado!r}')



def test_cen_7d63aab931_adicionar_sku_none_rejeitado():
    """Dado sku=None (tipo declarado str), quando adicionar é executada, então deve rejeitar a entrada com TypeError/ValueError (ou uma exceção documentada: ValueError) em vez de prosseguir."""
    from loja import Estoque
    with pytest.raises((TypeError, ValueError)):
        resultado = Estoque().adicionar(sku=None, quantidade=7)
        pytest.fail(f'entrada inválida aceita sem validação; retorno: {resultado!r}')



def test_cen_689adc6bee_retirar_sku_none_rejeitado():
    """Dado sku=None (tipo declarado str), quando retirar é executada, então deve rejeitar a entrada com TypeError/ValueError (ou uma exceção documentada: EstoqueInsuficiente) em vez de prosseguir."""
    from loja import Estoque
    from loja import EstoqueInsuficiente
    with pytest.raises((EstoqueInsuficiente, TypeError, ValueError)):
        resultado = Estoque().retirar(sku=None, quantidade=7)
        pytest.fail(f'entrada inválida aceita sem validação; retorno: {resultado!r}')

