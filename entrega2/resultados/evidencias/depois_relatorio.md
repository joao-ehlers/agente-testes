# Relatório do Agente de Testes — loja

**Portão de qualidade:** ❌ REPROVADO — 3 teste(s) reprovado(s)

| Total | Aprovados | Reprovados | Erros | Ignorados | Cobertura |
|---|---|---|---|---|---|
| 65 | 62 | 3 | 0 | 0 | 97.7% |

Relatório `REL-06f94437e2` · linguagem `python` · framework `pytest` · executor `docker` · modelo `nenhum (modo heurístico)` · iterações 1

## Achados

| Categoria | Teste | Explicação |
|---|---|---|
| defeito_suspeito | `test_cen_6a00c9a25c_ticket_medio_pedidos` | ZeroDivisionError: division by zero |
| validacao_ausente | `test_cen_56f2c1b86e_aplicar_cupom_total_none_rejeitado` | loja.aplicar_cupom aceitou entrada inválida sem rejeitá-la: Failed: entrada inválida aceita sem validação; retorno: None |
| validacao_ausente | `test_cen_7d63aab931_adicionar_sku_none_rejeitado` | loja.Estoque.adicionar aceitou entrada inválida sem rejeitá-la: Failed: entrada inválida aceita sem validação; retorno: 7 |

## Cenários (65: 9 sucesso, 14 falha, 42 borda)

- ✅ **sucesso** `loja.calcular_desconto` [RF-01]: Dado valor=2.5, percentual=2.5, quando calcular_desconto é executada, então retorna um valor do tipo float.
- ✅ **borda** `loja.calcular_desconto` [RF-01]: Dado valor=0.0 (valor-limite), quando calcular_desconto é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float (ou uma exceção documentada: ValueError).
- ✅ **borda** `loja.calcular_desconto` [RF-01]: Dado valor=-0.01 (valor-limite), quando calcular_desconto é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float (ou uma exceção documentada: ValueError).
- ✅ **borda** `loja.calcular_desconto` [RF-01]: Dado valor=1000000000000.0 (valor-limite), quando calcular_desconto é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float (ou uma exceção documentada: ValueError).
- ✅ **borda** `loja.calcular_desconto` [RF-01]: Dado percentual=0.0 (valor-limite), quando calcular_desconto é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float (ou uma exceção documentada: ValueError).
- ✅ **borda** `loja.calcular_desconto` [RF-01]: Dado percentual=-0.01 (valor-limite), quando calcular_desconto é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float (ou uma exceção documentada: ValueError).
- ✅ **borda** `loja.calcular_desconto` [RF-01]: Dado percentual=1000000000000.0 (valor-limite), quando calcular_desconto é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float (ou uma exceção documentada: ValueError).
- ✅ **falha** `loja.calcular_desconto` [RF-01]: Dado valor=-0.5 (viola 'valor < 0'), quando calcular_desconto é executada, então lança ValueError.
- ✅ **falha** `loja.calcular_desconto` [RF-01]: Dado percentual=-0.5 (viola 'percentual < 0'), quando calcular_desconto é executada, então lança ValueError.
- ✅ **falha** `loja.calcular_desconto` [RF-01]: Dado percentual=100.5 (viola 'percentual > 100'), quando calcular_desconto é executada, então lança ValueError.
- ✅ **borda** `loja.calcular_desconto` [RF-01]: Dado valor=0 (fronteira válida de 'valor < 0'), quando calcular_desconto é executada, então não lança exceção e retorna um valor do tipo float.
- ✅ **borda** `loja.calcular_desconto` [RF-01]: Dado percentual=0 (fronteira válida de 'percentual < 0'), quando calcular_desconto é executada, então não lança exceção e retorna um valor do tipo float.
- ✅ **borda** `loja.calcular_desconto` [RF-01]: Dado percentual=100 (fronteira válida de 'percentual > 100'), quando calcular_desconto é executada, então não lança exceção e retorna um valor do tipo float.
- ✅ **falha** `loja.calcular_desconto` [RF-01]: Dado valor=None (tipo declarado float), quando calcular_desconto é executada, então deve rejeitar a entrada com TypeError/ValueError (ou uma exceção documentada: ValueError) em vez de prosseguir.
- ✅ **sucesso** `loja.calcular_frete` [RF-02]: Dado peso_kg=2.5, distancia_km=7, quando calcular_frete é executada, então retorna um valor do tipo float.
- ✅ **borda** `loja.calcular_frete` [RF-02]: Dado peso_kg=0.0 (valor-limite), quando calcular_frete é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float (ou uma exceção documentada: ValueError).
- ✅ **borda** `loja.calcular_frete` [RF-02]: Dado peso_kg=-0.01 (valor-limite), quando calcular_frete é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float (ou uma exceção documentada: ValueError).
- ✅ **borda** `loja.calcular_frete` [RF-02]: Dado peso_kg=1000000000000.0 (valor-limite), quando calcular_frete é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float (ou uma exceção documentada: ValueError).
- ✅ **borda** `loja.calcular_frete` [RF-02]: Dado distancia_km=0 (valor-limite), quando calcular_frete é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float (ou uma exceção documentada: ValueError).
- ✅ **borda** `loja.calcular_frete` [RF-02]: Dado distancia_km=-1 (valor-limite), quando calcular_frete é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float (ou uma exceção documentada: ValueError).
- ✅ **borda** `loja.calcular_frete` [RF-02]: Dado distancia_km=1000000000000 (valor-limite), quando calcular_frete é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float (ou uma exceção documentada: ValueError).
- ✅ **falha** `loja.calcular_frete` [RF-02]: Dado peso_kg=0 (viola 'peso_kg <= 0'), quando calcular_frete é executada, então lança ValueError.
- ✅ **falha** `loja.calcular_frete` [RF-02]: Dado distancia_km=-1 (viola 'distancia_km < 0'), quando calcular_frete é executada, então lança ValueError.
- ✅ **borda** `loja.calcular_frete` [RF-02]: Dado peso_kg=0.5 (fronteira válida de 'peso_kg <= 0'), quando calcular_frete é executada, então não lança exceção e retorna um valor do tipo float.
- ✅ **borda** `loja.calcular_frete` [RF-02]: Dado distancia_km=0 (fronteira válida de 'distancia_km < 0'), quando calcular_frete é executada, então não lança exceção e retorna um valor do tipo float.
- ✅ **falha** `loja.calcular_frete` [RF-02]: Dado peso_kg=None (tipo declarado float), quando calcular_frete é executada, então deve rejeitar a entrada com TypeError/ValueError (ou uma exceção documentada: ValueError) em vez de prosseguir.
- ✅ **sucesso** `loja.ticket_medio` [RF-03]: Dado pedidos=[1, 2, 3], quando ticket_medio é executada, então retorna um valor do tipo float.
- ❌ **borda** `loja.ticket_medio` [RF-03]: Dado pedidos=[] (valor-limite), quando ticket_medio é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float.
- ✅ **borda** `loja.ticket_medio` [RF-03]: Dado pedidos=[0] (valor-limite), quando ticket_medio é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float.
- ✅ **falha** `loja.ticket_medio` [RF-03]: Dado pedidos=None (tipo declarado List[float]), quando ticket_medio é executada, então deve rejeitar a entrada com TypeError/ValueError em vez de prosseguir.
- ✅ **sucesso** `loja.aplicar_cupom` [RF-04]: Dado total=2.5, codigo='abc', quando aplicar_cupom é executada, então retorna um valor do tipo float.
- ✅ **borda** `loja.aplicar_cupom` [RF-04]: Dado total=0.0 (valor-limite), quando aplicar_cupom é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float.
- ✅ **borda** `loja.aplicar_cupom` [RF-04]: Dado total=-0.01 (valor-limite), quando aplicar_cupom é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float.
- ✅ **borda** `loja.aplicar_cupom` [RF-04]: Dado total=1000000000000.0 (valor-limite), quando aplicar_cupom é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float.
- ✅ **borda** `loja.aplicar_cupom` [RF-04]: Dado codigo='' (valor-limite), quando aplicar_cupom é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float.
- ✅ **borda** `loja.aplicar_cupom` [RF-04]: Dado codigo='   ' (valor-limite), quando aplicar_cupom é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float.
- ✅ **borda** `loja.aplicar_cupom` [RF-04]: Dado codigo=str de tamanho 256 (valor-limite), quando aplicar_cupom é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float.
- ❌ **falha** `loja.aplicar_cupom` [RF-04]: Dado total=None (tipo declarado float), quando aplicar_cupom é executada, então deve rejeitar a entrada com TypeError/ValueError em vez de prosseguir.
- ✅ **sucesso** `loja.aplicar_cupom` [RF-04]: Dado os colaboradores reais (calcular_desconto) sem dublês, quando aplicar_cupom é executada com total=2.5, codigo='abc', então o fluxo completo retorna um valor do tipo float.
- ✅ **sucesso** `loja.fechar_pedido`: Dado itens={'a': 1}, frete=2.5, quando fechar_pedido é executada, então retorna um valor do tipo float.
- ✅ **borda** `loja.fechar_pedido`: Dado itens={} (valor-limite), quando fechar_pedido é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float (ou uma exceção documentada: ValueError).
- ✅ **borda** `loja.fechar_pedido`: Dado frete=0.0 (valor-limite), quando fechar_pedido é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float (ou uma exceção documentada: ValueError).
- ✅ **borda** `loja.fechar_pedido`: Dado frete=-0.01 (valor-limite), quando fechar_pedido é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float (ou uma exceção documentada: ValueError).
- ✅ **borda** `loja.fechar_pedido`: Dado frete=1000000000000.0 (valor-limite), quando fechar_pedido é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float (ou uma exceção documentada: ValueError).
- ✅ **falha** `loja.fechar_pedido`: Dado itens={} (viola 'itens vazio/falso'), quando fechar_pedido é executada, então lança ValueError.
- ✅ **falha** `loja.fechar_pedido`: Dado itens=None (tipo declarado Dict[str, int]), quando fechar_pedido é executada, então deve rejeitar a entrada com TypeError/ValueError (ou uma exceção documentada: ValueError) em vez de prosseguir.
- ✅ **sucesso** `loja.fechar_pedido`: Dado os colaboradores reais (calcular_desconto) sem dublês, quando fechar_pedido é executada com itens={'a': 1}, frete=2.5, então o fluxo completo retorna um valor do tipo float.
- ✅ **sucesso** `loja.Estoque.adicionar`: Dado sku='abc', quantidade=7, quando adicionar é executada, então retorna um valor do tipo int.
- ✅ **borda** `loja.Estoque.adicionar`: Dado sku='' (valor-limite), quando adicionar é executada, então não deve lançar exceção inesperada; retorna um valor do tipo int (ou uma exceção documentada: ValueError).
- ✅ **borda** `loja.Estoque.adicionar`: Dado sku='   ' (valor-limite), quando adicionar é executada, então não deve lançar exceção inesperada; retorna um valor do tipo int (ou uma exceção documentada: ValueError).
- ✅ **borda** `loja.Estoque.adicionar`: Dado sku=str de tamanho 256 (valor-limite), quando adicionar é executada, então não deve lançar exceção inesperada; retorna um valor do tipo int (ou uma exceção documentada: ValueError).
- ✅ **borda** `loja.Estoque.adicionar`: Dado quantidade=0 (valor-limite), quando adicionar é executada, então não deve lançar exceção inesperada; retorna um valor do tipo int (ou uma exceção documentada: ValueError).
- ✅ **borda** `loja.Estoque.adicionar`: Dado quantidade=-1 (valor-limite), quando adicionar é executada, então não deve lançar exceção inesperada; retorna um valor do tipo int (ou uma exceção documentada: ValueError).
- ✅ **borda** `loja.Estoque.adicionar`: Dado quantidade=1000000000000 (valor-limite), quando adicionar é executada, então não deve lançar exceção inesperada; retorna um valor do tipo int (ou uma exceção documentada: ValueError).
- ✅ **falha** `loja.Estoque.adicionar`: Dado quantidade=0 (viola 'quantidade <= 0'), quando adicionar é executada, então lança ValueError.
- ✅ **borda** `loja.Estoque.adicionar`: Dado quantidade=1 (fronteira válida de 'quantidade <= 0'), quando adicionar é executada, então não lança exceção e retorna um valor do tipo int.
- ❌ **falha** `loja.Estoque.adicionar`: Dado sku=None (tipo declarado str), quando adicionar é executada, então deve rejeitar a entrada com TypeError/ValueError (ou uma exceção documentada: ValueError) em vez de prosseguir.
- ✅ **sucesso** `loja.Estoque.retirar`: Dado sku='abc', quantidade=7, quando retirar é executada, então retorna um valor do tipo int.
- ✅ **borda** `loja.Estoque.retirar`: Dado sku='' (valor-limite), quando retirar é executada, então não deve lançar exceção inesperada; retorna um valor do tipo int (ou uma exceção documentada: EstoqueInsuficiente).
- ✅ **borda** `loja.Estoque.retirar`: Dado sku='   ' (valor-limite), quando retirar é executada, então não deve lançar exceção inesperada; retorna um valor do tipo int (ou uma exceção documentada: EstoqueInsuficiente).
- ✅ **borda** `loja.Estoque.retirar`: Dado sku=str de tamanho 256 (valor-limite), quando retirar é executada, então não deve lançar exceção inesperada; retorna um valor do tipo int (ou uma exceção documentada: EstoqueInsuficiente).
- ✅ **borda** `loja.Estoque.retirar`: Dado quantidade=0 (valor-limite), quando retirar é executada, então não deve lançar exceção inesperada; retorna um valor do tipo int (ou uma exceção documentada: EstoqueInsuficiente).
- ✅ **borda** `loja.Estoque.retirar`: Dado quantidade=-1 (valor-limite), quando retirar é executada, então não deve lançar exceção inesperada; retorna um valor do tipo int (ou uma exceção documentada: EstoqueInsuficiente).
- ✅ **borda** `loja.Estoque.retirar`: Dado quantidade=1000000000000 (valor-limite), quando retirar é executada, então não deve lançar exceção inesperada; retorna um valor do tipo int (ou uma exceção documentada: EstoqueInsuficiente).
- ✅ **falha** `loja.Estoque.retirar`: Dado sku=None (tipo declarado str), quando retirar é executada, então deve rejeitar a entrada com TypeError/ValueError (ou uma exceção documentada: EstoqueInsuficiente) em vez de prosseguir.

## Trechos não cobertos

- `loja.py:43 (loja.aplicar_cupom)`

## Testes gerados

### `tests_gerados/test_loja_unitario.py` (unitario, heuristica)

```py
"""Testes unitario gerados pelo Agente de Testes para loja.

Gerados a partir de cenários (hipóteses); a execução é a fonte da verdade.
"""
import asyncio

import pytest

def test_cen_20e0b290d1_calcular_desconto_entradas_t_picas():
    """Dado valor=2.5, percentual=2.5, quando calcular_desconto é executada, então retorna um valor do tipo float."""
    from loja import calcular_desconto
    try:
        resultado = calcular_desconto(valor=2.5, percentual=2.5)
    except (ValueError,):
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, (int, float)), f'retorno inesperado: {resultado!r}'



def test_cen_219e8d1bec_calcular_desconto_valor_0_0():
    """Dado valor=0.0 (valor-limite), quando calcular_desconto é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float (ou uma exceção documentada: ValueError)."""
    from loja import calcular_desconto
    try:
        resultado = calcular_desconto(valor=0.0, percentual=2.5)
    except (ValueError,):
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, (int, float)), f'retorno inesperado: {resultado!r}'



def test_cen_53f733f159_calcular_desconto_valor_0_01():
    """Dado valor=-0.01 (valor-limite), quando calcular_desconto é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float (ou uma exceção documentada: ValueError)."""
    from loja import calcular_desconto
    try:
        resultado = calcular_desconto(valor=-0.01, percentual=2.5)
    except (ValueError,):
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, (int, float)), f'retorno inesperado: {resultado!r}'



def test_cen_749c208c23_calcular_desconto_valor_1000000000000_0():
    """Dado valor=1000000000000.0 (valor-limite), quando calcular_desconto é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float (ou uma exceção documentada: ValueError)."""
    from loja import calcular_desconto
    try:
        resultado = calcular_desconto(valor=1000000000000.0, percentual=2.5)
    except (ValueError,):
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, (int, float)), f'retorno inesperado: {resultado!r}'



def test_cen_1db8d2a9a0_calcular_desconto_percentual_0_0():
    """Dado percentual=0.0 (valor-limite), quando calcular_desconto é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float (ou uma exceção documentada: ValueError)."""
    from loja import calcular_desconto
    try:
        resultado = calcular_desconto(valor=2.5, percentual=0.0)
    except (ValueError,):
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, (int, float)), f'retorno inesperado: {resultado!r}'



def test_cen_b63b5f005d_calcular_desconto_percentual_0_01():
    """Dado percentual=-0.01 (valor-limite), quando calcular_desconto é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float (ou uma exceção documentada: ValueError)."""
    from loja import calcular_desconto
    try:
        resultado = calcular_desconto(valor=2.5, percentual=-0.01)
    except (ValueError,):
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, (int, float)), f'retorno inesperado: {resultado!r}'



def test_cen_24be833dff_calcular_desconto_percentual_1000000000000_0():
    """Dado percentual=1000000000000.0 (valor-limite), quando calcular_desconto é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float (ou uma exceção documentada: ValueError)."""
    from loja import calcular_desconto
    try:
        resultado = calcular_desconto(valor=2.5, percentual=1000000000000.0)
    except (ValueError,):
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, (int, float)), f'retorno inesperado: {resultado!r}'



def test_cen_f1710123c9_calcular_desconto_rejeita_valor_0():
    """Dado valor=-0.5 (viola 'valor < 0'), quando calcular_desconto é executada, então lança ValueError."""
    from loja import calcular_desconto
    with pytest.raises((ValueError,)):
        calcular_desconto(valor=-0.5, percentual=2.5)



def test_cen_345d30abd4_calcular_desconto_rejeita_percentual_0():
    """Dado percentual=-0.5 (viola 'percentual < 0'), quando calcular_desconto é executada, então lança ValueError."""
    from loja import calcular_desconto
    with pytest.raises((ValueError,)):
        calcular_desconto(valor=2.5, percentual=-0.5)



def test_cen_06f94a711c_calcular_desconto_rejeita_percentual_100():
    """Dado percentual=100.5 (viola 'percentual > 100'), quando calcular_desconto é executada, então lança ValueError."""
    from loja import calcular_desconto
    with pytest.raises((ValueError,)):
        calcular_desconto(valor=2.5, percentual=100.5)



def test_cen_41a265c9a7_calcular_desconto_aceita_valor_0_limite_de_valor_0():
    """Dado valor=0 (fronteira válida de 'valor < 0'), quando calcular_desconto é executada, então não lança exceção e retorna um valor do tipo float."""
    from loja import calcular_desconto
    resultado = calcular_desconto(valor=0, percentual=2.5)
    assert isinstance(resultado, (int, float)), f'retorno inesperado: {resultado!r}'



def test_cen_ea0e6dcbc9_calcular_desconto_aceita_percentual_0_limite_de_pe():
    """Dado percentual=0 (fronteira válida de 'percentual < 0'), quando calcular_desconto é executada, então não lança exceção e retorna um valor do tipo float."""
    from loja import calcular_desconto
    resultado = calcular_desconto(valor=2.5, percentual=0)
    assert isinstance(resultado, (int, float)), f'retorno inesperado: {resultado!r}'



def test_cen_80cade12a4_calcular_desconto_aceita_percentual_100_limite_de_():
    """Dado percentual=100 (fronteira válida de 'percentual > 100'), quando calcular_desconto é executada, então não lança exceção e retorna um valor do tipo float."""
    from loja import calcular_desconto
    resultado = calcular_desconto(valor=2.5, percentual=100)
    assert isinstance(resultado, (int, float)), f'retorno inesperado: {resultado!r}'



def test_cen_c3bf8a9d9f_calcular_frete_entradas_t_picas():
    """Dado peso_kg=2.5, distancia_km=7, quando calcular_frete é executada, então retorna um valor do tipo float."""
    from loja import calcular_frete
    try:
        resultado = calcular_frete(peso_kg=2.5, distancia_km=7)
    except (ValueError,):
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, (int, float)), f'retorno inesperado: {resultado!r}'



def test_cen_2c3653e881_calcular_frete_peso_kg_0_0():
    """Dado peso_kg=0.0 (valor-limite), quando calcular_frete é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float (ou uma exceção documentada: ValueError)."""
    from loja import calcular_frete
    try:
        resultado = calcular_frete(peso_kg=0.0, distancia_km=7)
    except (ValueError,):
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, (int, float)), f'retorno inesperado: {resultado!r}'



def test_cen_484ec7a68d_calcular_frete_peso_kg_0_01():
    """Dado peso_kg=-0.01 (valor-limite), quando calcular_frete é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float (ou uma exceção documentada: ValueError)."""
    from loja import calcular_frete
    try:
        resultado = calcular_frete(peso_kg=-0.01, distancia_km=7)
    except (ValueError,):
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, (int, float)), f'retorno inesperado: {resultado!r}'



def test_cen_3966b9043a_calcular_frete_peso_kg_1000000000000_0():
    """Dado peso_kg=1000000000000.0 (valor-limite), quando calcular_frete é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float (ou uma exceção documentada: ValueError)."""
    from loja import calcular_frete
    try:
        resultado = calcular_frete(peso_kg=1000000000000.0, distancia_km=7)
    except (ValueError,):
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, (int, float)), f'retorno inesperado: {resultado!r}'



def test_cen_28de335856_calcular_frete_distancia_km_0():
    """Dado distancia_km=0 (valor-limite), quando calcular_frete é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float (ou uma exceção documentada: ValueError)."""
    from loja import calcular_frete
    try:
        resultado = calcular_frete(peso_kg=2.5, distancia_km=0)
    except (ValueError,):
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, (int, float)), f'retorno inesperado: {resultado!r}'



def test_cen_df39a1aa97_calcular_frete_distancia_km_1():
    """Dado distancia_km=-1 (valor-limite), quando calcular_frete é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float (ou uma exceção documentada: ValueError)."""
    from loja import calcular_frete
    try:
        resultado = calcular_frete(peso_kg=2.5, distancia_km=-1)
    except (ValueError,):
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, (int, float)), f'retorno inesperado: {resultado!r}'



def test_cen_57e0fde07a_calcular_frete_distancia_km_1000000000000():
    """Dado distancia_km=1000000000000 (valor-limite), quando calcular_frete é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float (ou uma exceção documentada: ValueError)."""
    from loja import calcular_frete
    try:
        resultado = calcular_frete(peso_kg=2.5, distancia_km=1000000000000)
    except (ValueError,):
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, (int, float)), f'retorno inesperado: {resultado!r}'



def test_cen_0502f971cc_calcular_frete_rejeita_peso_kg_0():
    """Dado peso_kg=0 (viola 'peso_kg <= 0'), quando calcular_frete é executada, então lança ValueError."""
    from loja import calcular_frete
    with pytest.raises((ValueError,)):
        calcular_frete(peso_kg=0, distancia_km=7)



def test_cen_86fafcf36f_calcular_frete_rejeita_distancia_km_0():
    """Dado distancia_km=-1 (viola 'distancia_km < 0'), quando calcular_frete é executada, então lança ValueError."""
    from loja import calcular_frete
    with pytest.raises((ValueError,)):
        calcular_frete(peso_kg=2.5, distancia_km=-1)



def test_cen_24deaa7d0a_calcular_frete_aceita_peso_kg_0_5_limite_de_peso_k():
    """Dado peso_kg=0.5 (fronteira válida de 'peso_kg <= 0'), quando calcular_frete é executada, então não lança exceção e retorna um valor do tipo float."""
    from loja import calcular_frete
    resultado = calcular_frete(peso_kg=0.5, distancia_km=7)
    assert isinstance(resultado, (int, float)), f'retorno inesperado: {resultado!r}'



def test_cen_32486f7332_calcular_frete_aceita_distancia_km_0_limite_de_dis():
    """Dado distancia_km=0 (fronteira válida de 'distancia_km < 0'), quando calcular_frete é executada, então não lança exceção e retorna um valor do tipo float."""
    from loja import calcular_frete
    resultado = calcular_frete(peso_kg=2.5, distancia_km=0)
    assert isinstance(resultado, (int, float)), f'retorno inesperado: {resultado!r}'



def test_cen_fa9a6e61c5_ticket_medio_entradas_t_picas():
    """Dado pedidos=[1, 2, 3], quando ticket_medio é executada, então retorna um valor do tipo float."""
    from loja import ticket_medio
    try:
        resultado = ticket_medio(pedidos=[1, 2, 3])
    except ():
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, (int, float)), f'retorno inesperado: {resultado!r}'



def test_cen_6a00c9a25c_ticket_medio_pedidos():
    """Dado pedidos=[] (valor-limite), quando ticket_medio é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float."""
    from loja import ticket_medio
    try:
        resultado = ticket_medio(pedidos=[])
    except ():
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, (int, float)), f'retorno inesperado: {resultado!r}'



def test_cen_4f960c71e7_ticket_medio_pedidos_0():
    """Dado pedidos=[0] (valor-limite), quando ticket_medio é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float."""
    from loja import ticket_medio
    try:
        resultado = ticket_medio(pedidos=[0])
    except ():
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, (int, float)), f'retorno inesperado: {resultado!r}'



def test_cen_9a58446164_aplicar_cupom_entradas_t_picas():
    """Dado total=2.5, codigo='abc', quando aplicar_cupom é executada, então retorna um valor do tipo float."""
    from loja import aplicar_cupom
    try:
        resultado = aplicar_cupom(total=2.5, codigo='abc')
    except ():
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, (int, float)), f'retorno inesperado: {resultado!r}'



def test_cen_705565d98e_aplicar_cupom_total_0_0():
    """Dado total=0.0 (valor-limite), quando aplicar_cupom é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float."""
    from loja import aplicar_cupom
    try:
        resultado = aplicar_cupom(total=0.0, codigo='abc')
    except ():
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, (int, float)), f'retorno inesperado: {resultado!r}'



def test_cen_28c526f56b_aplicar_cupom_total_0_01():
    """Dado total=-0.01 (valor-limite), quando aplicar_cupom é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float."""
    from loja import aplicar_cupom
    try:
        resultado = aplicar_cupom(total=-0.01, codigo='abc')
    except ():
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, (int, float)), f'retorno inesperado: {resultado!r}'



def test_cen_1c6be3378f_aplicar_cupom_total_1000000000000_0():
    """Dado total=1000000000000.0 (valor-limite), quando aplicar_cupom é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float."""
    from loja import aplicar_cupom
    try:
        resultado = aplicar_cupom(total=1000000000000.0, codigo='abc')
    except ():
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, (int, float)), f'retorno inesperado: {resultado!r}'



def test_cen_2d2b918fb5_aplicar_cupom_codigo():
    """Dado codigo='' (valor-limite), quando aplicar_cupom é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float."""
    from loja import aplicar_cupom
    try:
        resultado = aplicar_cupom(total=2.5, codigo='')
    except ():
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, (int, float)), f'retorno inesperado: {resultado!r}'



def test_cen_bdbb7e59bf_aplicar_cupom_codigo():
    """Dado codigo='   ' (valor-limite), quando aplicar_cupom é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float."""
    from loja import aplicar_cupom
    try:
        resultado = aplicar_cupom(total=2.5, codigo='   ')
    except ():
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, (int, float)), f'retorno inesperado: {resultado!r}'



def test_cen_8373d1253d_aplicar_cupom_codigo_str_de_tamanho_256():
    """Dado codigo=str de tamanho 256 (valor-limite), quando aplicar_cupom é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float."""
    from loja import aplicar_cupom
    try:
        resultado = aplicar_cupom(total=2.5, codigo='çççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççç')
    except ():
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, (int, float)), f'retorno inesperado: {resultado!r}'



def test_cen_27a59153aa_fechar_pedido_entradas_t_picas():
    """Dado itens={'a': 1}, frete=2.5, quando fechar_pedido é executada, então retorna um valor do tipo float."""
    from loja import fechar_pedido
    try:
        resultado = fechar_pedido(itens={'a': 1}, frete=2.5)
    except (ValueError,):
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, (int, float)), f'retorno inesperado: {resultado!r}'



def test_cen_ec0e4e8257_fechar_pedido_itens():
    """Dado itens={} (valor-limite), quando fechar_pedido é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float (ou uma exceção documentada: ValueError)."""
    from loja import fechar_pedido
    try:
        resultado = fechar_pedido(itens={}, frete=2.5)
    except (ValueError,):
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, (int, float)), f'retorno inesperado: {resultado!r}'



def test_cen_0bde6f922e_fechar_pedido_frete_0_0():
    """Dado frete=0.0 (valor-limite), quando fechar_pedido é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float (ou uma exceção documentada: ValueError)."""
    from loja import fechar_pedido
    try:
        resultado = fechar_pedido(itens={'a': 1}, frete=0.0)
    except (ValueError,):
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, (int, float)), f'retorno inesperado: {resultado!r}'



def test_cen_abcbea9c31_fechar_pedido_frete_0_01():
    """Dado frete=-0.01 (valor-limite), quando fechar_pedido é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float (ou uma exceção documentada: ValueError)."""
    from loja import fechar_pedido
    try:
        resultado = fechar_pedido(itens={'a': 1}, frete=-0.01)
    except (ValueError,):
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, (int, float)), f'retorno inesperado: {resultado!r}'



def test_cen_a3602e1d1e_fechar_pedido_frete_1000000000000_0():
    """Dado frete=1000000000000.0 (valor-limite), quando fechar_pedido é executada, então não deve lançar exceção inesperada; retorna um valor do tipo float (ou uma exceção documentada: ValueError)."""
    from loja import fechar_pedido
    try:
        resultado = fechar_pedido(itens={'a': 1}, frete=1000000000000.0)
    except (ValueError,):
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, (int, float)), f'retorno inesperado: {resultado!r}'



def test_cen_76e69367f7_fechar_pedido_rejeita_itens_vazio_falso():
    """Dado itens={} (viola 'itens vazio/falso'), quando fechar_pedido é executada, então lança ValueError."""
    from loja import fechar_pedido
    with pytest.raises((ValueError,)):
        fechar_pedido(itens={}, frete=2.5)



def test_cen_88a0b9ce4c_adicionar_entradas_t_picas():
    """Dado sku='abc', quantidade=7, quando adicionar é executada, então retorna um valor do tipo int."""
    from loja import Estoque
    try:
        resultado = Estoque().adicionar(sku='abc', quantidade=7)
    except (ValueError,):
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, int), f'retorno inesperado: {resultado!r}'



def test_cen_2032951148_adicionar_sku():
    """Dado sku='' (valor-limite), quando adicionar é executada, então não deve lançar exceção inesperada; retorna um valor do tipo int (ou uma exceção documentada: ValueError)."""
    from loja import Estoque
    try:
        resultado = Estoque().adicionar(sku='', quantidade=7)
    except (ValueError,):
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, int), f'retorno inesperado: {resultado!r}'



def test_cen_545b3ced40_adicionar_sku():
    """Dado sku='   ' (valor-limite), quando adicionar é executada, então não deve lançar exceção inesperada; retorna um valor do tipo int (ou uma exceção documentada: ValueError)."""
    from loja import Estoque
    try:
        resultado = Estoque().adicionar(sku='   ', quantidade=7)
    except (ValueError,):
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, int), f'retorno inesperado: {resultado!r}'



def test_cen_c38d40a951_adicionar_sku_str_de_tamanho_256():
    """Dado sku=str de tamanho 256 (valor-limite), quando adicionar é executada, então não deve lançar exceção inesperada; retorna um valor do tipo int (ou uma exceção documentada: ValueError)."""
    from loja import Estoque
    try:
        resultado = Estoque().adicionar(sku='çççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççç', quantidade=7)
    except (ValueError,):
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, int), f'retorno inesperado: {resultado!r}'



def test_cen_eb3d73d125_adicionar_quantidade_0():
    """Dado quantidade=0 (valor-limite), quando adicionar é executada, então não deve lançar exceção inesperada; retorna um valor do tipo int (ou uma exceção documentada: ValueError)."""
    from loja import Estoque
    try:
        resultado = Estoque().adicionar(sku='abc', quantidade=0)
    except (ValueError,):
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, int), f'retorno inesperado: {resultado!r}'



def test_cen_bce92e9a13_adicionar_quantidade_1():
    """Dado quantidade=-1 (valor-limite), quando adicionar é executada, então não deve lançar exceção inesperada; retorna um valor do tipo int (ou uma exceção documentada: ValueError)."""
    from loja import Estoque
    try:
        resultado = Estoque().adicionar(sku='abc', quantidade=-1)
    except (ValueError,):
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, int), f'retorno inesperado: {resultado!r}'



def test_cen_96fb245789_adicionar_quantidade_1000000000000():
    """Dado quantidade=1000000000000 (valor-limite), quando adicionar é executada, então não deve lançar exceção inesperada; retorna um valor do tipo int (ou uma exceção documentada: ValueError)."""
    from loja import Estoque
    try:
        resultado = Estoque().adicionar(sku='abc', quantidade=1000000000000)
    except (ValueError,):
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, int), f'retorno inesperado: {resultado!r}'



def test_cen_63b5a9340e_adicionar_rejeita_quantidade_0():
    """Dado quantidade=0 (viola 'quantidade <= 0'), quando adicionar é executada, então lança ValueError."""
    from loja import Estoque
    with pytest.raises((ValueError,)):
        Estoque().adicionar(sku='abc', quantidade=0)



def test_cen_513e03552b_adicionar_aceita_quantidade_1_limite_de_quantidade():
    """Dado quantidade=1 (fronteira válida de 'quantidade <= 0'), quando adicionar é executada, então não lança exceção e retorna um valor do tipo int."""
    from loja import Estoque
    resultado = Estoque().adicionar(sku='abc', quantidade=1)
    assert isinstance(resultado, int), f'retorno inesperado: {resultado!r}'



def test_cen_41efbc31c9_retirar_entradas_t_picas():
    """Dado sku='abc', quantidade=7, quando retirar é executada, então retorna um valor do tipo int."""
    from loja import Estoque
    from loja import EstoqueInsuficiente
    try:
        resultado = Estoque().retirar(sku='abc', quantidade=7)
    except (EstoqueInsuficiente,):
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, int), f'retorno inesperado: {resultado!r}'



def test_cen_94df6a73a4_retirar_sku():
    """Dado sku='' (valor-limite), quando retirar é executada, então não deve lançar exceção inesperada; retorna um valor do tipo int (ou uma exceção documentada: EstoqueInsuficiente)."""
    from loja import Estoque
    from loja import EstoqueInsuficiente
    try:
        resultado = Estoque().retirar(sku='', quantidade=7)
    except (EstoqueInsuficiente,):
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, int), f'retorno inesperado: {resultado!r}'



def test_cen_9a8362dfab_retirar_sku():
    """Dado sku='   ' (valor-limite), quando retirar é executada, então não deve lançar exceção inesperada; retorna um valor do tipo int (ou uma exceção documentada: EstoqueInsuficiente)."""
    from loja import Estoque
    from loja import EstoqueInsuficiente
    try:
        resultado = Estoque().retirar(sku='   ', quantidade=7)
    except (EstoqueInsuficiente,):
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, int), f'retorno inesperado: {resultado!r}'



def test_cen_d2369a8d28_retirar_sku_str_de_tamanho_256():
    """Dado sku=str de tamanho 256 (valor-limite), quando retirar é executada, então não deve lançar exceção inesperada; retorna um valor do tipo int (ou uma exceção documentada: EstoqueInsuficiente)."""
    from loja import Estoque
    from loja import EstoqueInsuficiente
    try:
        resultado = Estoque().retirar(sku='çççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççççç', quantidade=7)
    except (EstoqueInsuficiente,):
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, int), f'retorno inesperado: {resultado!r}'



def test_cen_6c5450a938_retirar_quantidade_0():
    """Dado quantidade=0 (valor-limite), quando retirar é executada, então não deve lançar exceção inesperada; retorna um valor do tipo int (ou uma exceção documentada: EstoqueInsuficiente)."""
    from loja import Estoque
    from loja import EstoqueInsuficiente
    try:
        resultado = Estoque().retirar(sku='abc', quantidade=0)
    except (EstoqueInsuficiente,):
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, int), f'retorno inesperado: {resultado!r}'



def test_cen_1da067bf2d_retirar_quantidade_1():
    """Dado quantidade=-1 (valor-limite), quando retirar é executada, então não deve lançar exceção inesperada; retorna um valor do tipo int (ou uma exceção documentada: EstoqueInsuficiente)."""
    from loja import Estoque
    from loja import EstoqueInsuficiente
    try:
        resultado = Estoque().retirar(sku='abc', quantidade=-1)
    except (EstoqueInsuficiente,):
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, int), f'retorno inesperado: {resultado!r}'



def test_cen_298e4d82e7_retirar_quantidade_1000000000000():
    """Dado quantidade=1000000000000 (valor-limite), quando retirar é executada, então não deve lançar exceção inesperada; retorna um valor do tipo int (ou uma exceção documentada: EstoqueInsuficiente)."""
    from loja import Estoque
    from loja import EstoqueInsuficiente
    try:
        resultado = Estoque().retirar(sku='abc', quantidade=1000000000000)
    except (EstoqueInsuficiente,):
        return  # exceção documentada pelo código: comportamento aceito
    assert isinstance(resultado, int), f'retorno inesperado: {resultado!r}'
```

### `tests_gerados/test_loja_validacao_entrada.py` (validacao_entrada, heuristica)

```py
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
```

### `tests_gerados/test_loja_integracao.py` (integracao, heuristica)

```py
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
```

<details><summary>Trilha de auditoria do pipeline</summary>

- **0-normalizacao** (iteração 1, 0.0s): 1 arquivo(s), linguagem=python, framework=pytest, openapi=não, diff=não
- **1-analise-contexto** (iteração 1, 0.001s): 7 unidade(s) (7 no escopo da mudança), 0 endpoint(s)
- **2-geracao-cenarios** (iteração 1, 0.001s): 65 cenário(s) derivados por heurística (AST/contrato); cenários por tipo: {'sucesso': 9, 'falha': 14, 'borda': 42}
- **3-selecao-estrategia** (iteração 1, 0.0s): estratégias ativas: e2e, validacao_entrada, integracao, unitario; unitario -> loja: 56 cenário(s); validacao_entrada -> loja: 7 cenário(s); integracao -> loja: 2 cenário(s)
- **4-geracao-codigo** (iteração 1, 0.003s): tests_gerados/test_loja_unitario.py: 56 teste(s) [heuristica]; tests_gerados/test_loja_validacao_entrada.py: 7 teste(s) [heuristica]; tests_gerados/test_loja_integracao.py: 2 teste(s) [heuristica]
- **5-execucao** (iteração 1, 0.717s): pytest via docker: código 1 em 0.6s; 65 resultado(s); cobertura=97.7%
- **6-analise-resultados** (iteração 1, 0.0s): resumo: {'total': 65, 'aprovados': 62, 'reprovados': 3, 'erros': 0, 'ignorados': 0} | achados: {'defeito_suspeito': 1, 'validacao_ausente': 2}

</details>
