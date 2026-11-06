import json
import os
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("AGENTE_LLM", "nenhum")

from agente_testes.agente import Configuracao  # noqa: E402
from agente_testes.contratos import ArquivoFonte, EntradaAgente  # noqa: E402
from agente_testes.llm.cliente import ModeloLinguagem  # noqa: E402
from agente_testes.modelos.dominio import Requisito  # noqa: E402

LOJA = RAIZ / "exemplos" / "loja"


@pytest.fixture
def entrada_loja() -> EntradaAgente:
    import yaml
    reqs = yaml.safe_load((LOJA / "requisitos.yaml").read_text())["requisitos"]
    return EntradaAgente(projeto="loja",
                         arquivos=[ArquivoFonte(caminho="loja.py", conteudo=(LOJA / "loja.py").read_text())],
                         requisitos=[Requisito.model_validate(r) for r in reqs])


@pytest.fixture
def config(tmp_path) -> Configuracao:
    return Configuracao(executor="local", timeout_s=120, cobertura_minima=0, max_iteracoes=3,
                        dir_dados=tmp_path / "dados")


class LLMFalso(ModeloLinguagem):
    """Modelo roteirizado: responde conforme o tipo de prompt e registra as chamadas."""

    nome = "falso"

    def __init__(self, respostas):
        self.respostas = respostas  # dict: chave -> lista de respostas (str ou dict)
        self.chamadas = []

    def _completar(self, sistema, usuario):
        chave = ("codigo" if "Escreva testes" in usuario else
                 "cenarios" if "Derive cenários" in usuario else "intencao")
        self.chamadas.append((chave, usuario))
        fila = self.respostas[chave]
        r = fila.pop(0) if len(fila) > 1 else fila[0]
        return r if isinstance(r, str) else json.dumps(r)
