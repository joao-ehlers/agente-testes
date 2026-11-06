import json

from agente_testes.agente import AgenteDeTestes
from agente_testes.contratos import ArquivoFonte, EntradaAgente
from agente_testes.llm.cliente import SemModelo
from conftest import LLMFalso


def test_pipeline_completo_heuristico_aponta_defeitos(entrada_loja, config):
    r = AgenteDeTestes(SemModelo(), config).executar(entrada_loja)
    assert not r.aprovado and r.resumo.total > 40
    categorias = {(a.categoria, a.alvo) for a in r.achados}
    assert ("defeito_suspeito", "loja.ticket_medio") in categorias
    assert ("validacao_ausente", "loja.aplicar_cupom") in categorias
    assert r.cobertura and r.cobertura.percentual > 80
    assert [e.filtro for e in r.auditoria] == ["0-normalizacao", "1-analise-contexto", "2-geracao-cenarios",
                                               "3-selecao-estrategia", "4-geracao-codigo", "5-execucao",
                                               "6-analise-resultados"]
    assert all(c.requisito_id for c in r.cenarios if c.alvo == "loja.calcular_frete")


def test_codigo_correto_aprova_portao(config):
    codigo = ("def soma(a: int, b: int) -> int:\n    if a < 0:\n        raise ValueError('a')\n"
              "    if a is None or b is None:\n        raise TypeError('x')\n    return a + b\n")
    r = AgenteDeTestes(SemModelo(), config).executar(
        EntradaAgente(arquivos=[ArquivoFonte(caminho="calc.py", conteudo=codigo)]))
    assert r.aprovado, r.achados


def test_suite_existente_e_regressao(config):
    codigo = "def dobro(x: int) -> int:\n    return x * 3\n"
    teste = "from calc import dobro\n\ndef test_dobro():\n    assert dobro(2) == 4\n"
    r = AgenteDeTestes(SemModelo(), config).executar(EntradaAgente(
        arquivos=[ArquivoFonte(caminho="calc.py", conteudo=codigo)],
        testes_existentes=[ArquivoFonte(caminho="tests/test_calc.py", conteudo=teste)],
        relatorios_anteriores=[{"casos": [{"nome": "tests.test_calc::test_dobro", "status": "aprovado"}]}]))
    assert any(a.categoria == "regressao" for a in r.achados), r.achados


def test_llm_hipotese_e_laco_de_regeneracao(config):
    codigo = ("def media(xs: list) -> float:\n    if xs is None:\n        raise TypeError('xs')\n"
              "    return sum(xs) / len(xs) if xs else 0.0\n")
    cenario = {"titulo": "média de dois", "tipo": "sucesso", "descricao": "Dado [2, 4] quando média então 3",
               "alvo": "calc.media", "entradas": {"xs": [2, 4]}, "resultado_esperado": "3.0"}
    teste_quebrado = {"arquivos": [{"caminho": "x.py", "conteudo": "import modulo_inexistente\n\ndef test_x():\n    pass\n"}]}
    llm = LLMFalso({
        "intencao": [{"intencao": "calcula a média", "riscos": [{"descricao": "lista vazia", "severidade": "alta"}]}],
        "cenarios": [{"cenarios": [cenario, dict(cenario, alvo="calc.nao_existe")]}],
        "codigo": [teste_quebrado, "PLACEHOLDER"],
    })
    agente = AgenteDeTestes(llm, config)

    def codigo_bom():  # usa o id real do cenário (o nome do teste referencia o id)
        ids = [l for _, l in llm.chamadas if "CEN-" in l]
        cid = json.loads(ids[-1].split("## Cenários (JSON)\n")[1].split("\n\n## Código")[0])[0]["id"]
        nome = cid.lower().replace("-", "_")
        return json.dumps({"arquivos": [{"caminho": "x.py", "conteudo":
            f"from calc import media\n\ndef test_{nome}_media():\n    assert media([2, 4]) == 3.0\n"}]})

    original = llm._completar

    def completar(s, u):
        r = original(s, u)
        return codigo_bom() if r == "PLACEHOLDER" else r
    llm._completar = completar

    r = agente.executar(EntradaAgente(arquivos=[ArquivoFonte(caminho="calc.py", conteudo=codigo)]))
    assert r.iteracoes == 2
    assert r.aprovado, r.achados
    assert any(x.descricao == "lista vazia" for x in r.riscos)
    assert len([c for c in r.cenarios if c.origem.value == "llm"]) == 1  # alvo inexistente descartado
    assert r.casos[0].origem.value == "llm"
    assert any("Erros da execução anterior" in u for k, u in llm.chamadas if k == "codigo")


def test_resposta_llm_invalida_cai_para_heuristica(config):
    llm = LLMFalso({"intencao": ["nao é json"], "cenarios": ['{"cenarios": "errado"}'], "codigo": ["{}"]})
    r = AgenteDeTestes(llm, config).executar(EntradaAgente(arquivos=[ArquivoFonte(
        caminho="m.py", conteudo="def f(x: int) -> int:\n    return x\n")]))
    assert r.resumo.total > 0 and all(c.origem.value == "heuristica" for c in r.cenarios)


def test_llm_nao_legitima_excecao_acidental(config):
    """Regressão: com o Gemini real, o LLM escreveu 'lista vazia -> lança ZeroDivisionError' e o portão aprovou."""
    codigo = "def media(xs: list) -> float:\n    return sum(xs) / len(xs)\n"
    ruim = {"titulo": "lista vazia", "tipo": "falha", "descricao": "Dado [] então ZeroDivisionError",
            "alvo": "calc.media", "entradas": {"xs": []}, "excecao_esperada": "ZeroDivisionError"}
    llm = LLMFalso({
        "intencao": [{"intencao": "média", "riscos": []}],
        "cenarios": [{"cenarios": [ruim]}],
        "codigo": [{"arquivos": [{"caminho": "x.py", "conteudo":
                    "import pytest\nfrom calc import media\n\ndef test_x():\n    with pytest.raises(ZeroDivisionError):\n        media([])\n"}]}],
    })
    r = AgenteDeTestes(llm, config).executar(EntradaAgente(arquivos=[ArquivoFonte(caminho="calc.py", conteudo=codigo)]))
    assert not any(c.excecao_esperada == "ZeroDivisionError" for c in r.cenarios)
    assert any("ZeroDivisionError acidental" in x.descricao for x in r.riscos)
    assert not r.aprovado
    assert any(a.categoria == "defeito_suspeito" and "ZeroDivisionError" in a.explicacao for a in r.achados)
