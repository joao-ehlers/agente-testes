"""Padrão Strategy (GoF): estratégias de teste intercambiáveis, escolhidas em tempo
de execução de acordo com o contexto analisado e com cada cenário.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from ..contratos import ContextoAnalisado
from ..modelos.dominio import CenarioDeTeste, TipoCenario, TipoTeste


def _eh_endpoint(alvo: str) -> bool:
    return alvo.split(" ", 1)[0] in ("GET", "POST", "PUT", "PATCH", "DELETE")


class EstrategiaDeTeste(ABC):
    tipo: TipoTeste
    prioridade: int = 50  # menor = avaliada antes

    def ativa(self, contexto: ContextoAnalisado) -> bool:
        forcados = contexto.entrada.tipos_teste
        return not forcados or self.tipo in forcados

    @abstractmethod
    def aplicavel(self, cenario: CenarioDeTeste, contexto: ContextoAnalisado) -> bool: ...


class EstrategiaContratoAPI(EstrategiaDeTeste):
    tipo = TipoTeste.API
    prioridade = 10

    def ativa(self, contexto):
        return super().ativa(contexto) and bool(contexto.endpoints)

    def aplicavel(self, cenario, contexto):
        return _eh_endpoint(cenario.alvo)


class EstrategiaE2E(EstrategiaDeTeste):
    tipo = TipoTeste.E2E
    prioridade = 15

    def aplicavel(self, cenario, contexto):
        return cenario.tipo_teste_sugerido == TipoTeste.E2E


class EstrategiaValidacaoEntrada(EstrategiaDeTeste):
    tipo = TipoTeste.VALIDACAO_ENTRADA
    prioridade = 20

    def aplicavel(self, cenario, contexto):
        if _eh_endpoint(cenario.alvo):
            return False
        if cenario.tipo_teste_sugerido == TipoTeste.VALIDACAO_ENTRADA:
            return True
        return cenario.tipo == TipoCenario.FALHA and any(v is None for v in cenario.entradas.values())


class EstrategiaIntegracao(EstrategiaDeTeste):
    tipo = TipoTeste.INTEGRACAO
    prioridade = 30

    def aplicavel(self, cenario, contexto):
        if cenario.tipo_teste_sugerido == TipoTeste.INTEGRACAO:
            return True
        unidade = next((u for u in contexto.unidades if u.qualificado == cenario.alvo), None)
        return bool(unidade and unidade.chamadas_internas and cenario.tipo == TipoCenario.SUCESSO
                    and cenario.tipo_teste_sugerido is None and "fluxo" in cenario.titulo.lower())


class EstrategiaUnitaria(EstrategiaDeTeste):
    tipo = TipoTeste.UNITARIO
    prioridade = 90

    def aplicavel(self, cenario, contexto):
        return not _eh_endpoint(cenario.alvo)


TODAS: List[EstrategiaDeTeste] = sorted(
    [EstrategiaContratoAPI(), EstrategiaE2E(), EstrategiaValidacaoEntrada(),
     EstrategiaIntegracao(), EstrategiaUnitaria()], key=lambda e: e.prioridade)
