from agente_testes.analise.diff import interpretar_diff
from agente_testes.analise.estatica_python import analisar_python, nome_modulo
from agente_testes.analise.openapi import carregar_openapi, extrair_endpoints
from agente_testes.analise.valores import resolver_condicao, tipo_base
from conftest import LOJA


def test_ast_extrai_unidades_excecoes_e_condicoes():
    unidades = {u.qualificado: u for u in analisar_python("loja.py", (LOJA / "loja.py").read_text())}
    assert {"loja.calcular_desconto", "loja.ticket_medio", "loja.Estoque.retirar"} <= set(unidades)
    d = unidades["loja.calcular_desconto"]
    assert d.excecoes == ["ValueError"]
    assert [(c.parametro, c.operador, c.valor) for c in d.condicoes_excecao] == [
        ("valor", "<", 0), ("percentual", "<", 0), ("percentual", ">", 100)]
    assert unidades["loja.Estoque.retirar"].tipo == "metodo"
    assert unidades["loja.aplicar_cupom"].chamadas_internas == ["calcular_desconto"]


def test_linhas_alteradas_limitam_escopo():
    codigo = "def a(x: int) -> int:\n    return x\n\n\ndef b(y: int) -> int:\n    return y\n"
    us = {u.nome: u.alterada for u in analisar_python("m.py", codigo, [6])}
    assert us == {"a": False, "b": True}


def test_nome_modulo():
    assert nome_modulo("src/app/servicos/pedido.py") == "app.servicos.pedido"
    assert nome_modulo("pkg/__init__.py") == "pkg"


def test_diff_unificado():
    diff = ("diff --git a/n.py b/n.py\nnew file mode 100644\n--- /dev/null\n+++ b/n.py\n@@ -0,0 +1,2 @@\n"
            "+def f():\n+    return 1\n--- a/v.py\n+++ b/v.py\n@@ -3,0 +4,1 @@\n+    x = 2\n")
    linhas, novos = interpretar_diff(diff)
    assert linhas == {"n.py": [1, 2], "v.py": [4]}
    assert novos["n.py"].startswith("def f():")


def test_openapi_endpoints_com_ref_e_exemplo():
    eps = {f"{e.metodo} {e.caminho}": e for e in extrair_endpoints(carregar_openapi((LOJA / "openapi.yaml").read_text()))}
    assert set(eps) == {"POST /pedidos", "GET /pedidos/{id}"}
    assert eps["POST /pedidos"].corpo_obrigatorio and eps["POST /pedidos"].exemplo_corpo["itens"] == {"SKU-1": 2}


def test_valores_e_condicoes():
    from agente_testes.contratos import Condicao, Parametro
    assert tipo_base("Optional[List[int]]") == ("list", True)
    assert tipo_base("int | None") == ("int", True)
    p = Parametro(nome="x", anotacao="float")
    assert resolver_condicao(Condicao(parametro="x", operador="<=", valor=0, excecao="E"), p) == 0
    assert resolver_condicao(Condicao(parametro="x", operador=">", valor=100, excecao="E"), p) == 100.5
