from fastapi.testclient import TestClient

from agente_testes.api import app as modulo_app
from agente_testes.controlador import ControladorAgente
from agente_testes.llm.cliente import SemModelo


def _cliente(config):
    ctrl = ControladorAgente(llm=SemModelo(), config=config)
    modulo_app.app.dependency_overrides[modulo_app.controlador] = lambda: ctrl
    return TestClient(modulo_app.app)


def test_endpoints(entrada_loja, config):
    c = _cliente(config)
    corpo = entrada_loja.model_dump(mode="json")
    assert c.get("/saude").json()["status"] == "ok"

    a = c.post("/analisar", json=corpo)
    assert a.status_code == 200 and a.json()["dados"]["cenarios"]

    g = c.post("/gerar-testes", json=corpo)
    assert g.status_code == 200 and g.json()["dados"]["casos"][0]["codigo"].startswith('"""Testes')

    e = c.post("/executar", json=corpo)
    assert e.status_code == 200
    rid = e.json()["id"]
    assert c.get(f"/relatorio/{rid}").json()["resumo"] == e.json()["resumo"]
    assert "Portão de qualidade" in c.get(f"/relatorio/{rid}/markdown").text
    assert c.get("/relatorio").json()[0]["id"] == rid
    assert c.get("/relatorio/REL-inexistente").status_code == 404
    assert c.post("/executar", json={"projeto": "vazio"}).status_code == 422
