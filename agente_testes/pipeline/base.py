"""Infraestrutura do estilo Pipe-and-Filter.

* `Filtro` — uma única responsabilidade; recebe um contrato e devolve outro.
* `Pipeline` — encadeia filtros (a saída de um é a entrada do próximo), valida o
  contrato em cada fronteira e registra uma trilha de auditoria. Permite
  executar só um trecho (`ate`) ou retomar a partir de um filtro (`a_partir_de`),
  o que viabiliza a reexecução isolada de filtros.
"""
from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Generic, List, Optional, Type, TypeVar

from pydantic import BaseModel

from ..modelos.dominio import EtapaAuditoria

log = logging.getLogger("agente_testes.pipeline")

E = TypeVar("E", bound=BaseModel)
S = TypeVar("S", bound=BaseModel)


class ErroDeContrato(Exception):
    pass


class Filtro(ABC, Generic[E, S]):
    nome: str = "filtro"
    tipo_entrada: Type[BaseModel] = BaseModel
    tipo_saida: Type[BaseModel] = BaseModel

    def __init__(self) -> None:
        self.observacoes: List[str] = []

    def anotar(self, msg: str) -> None:
        self.observacoes.append(msg)
        log.info("[%s] %s", self.nome, msg)

    @abstractmethod
    def processar(self, entrada: E) -> S: ...


class Pipeline:
    def __init__(self, filtros: List[Filtro]):
        self.filtros = filtros
        self.auditoria: List[EtapaAuditoria] = []

    def indice(self, nome: str) -> int:
        for i, f in enumerate(self.filtros):
            if f.nome == nome:
                return i
        raise KeyError(nome)

    def executar(self, dados: BaseModel, a_partir_de: Optional[str] = None,
                 ate: Optional[str] = None, iteracao: int = 1) -> BaseModel:
        inicio = self.indice(a_partir_de) if a_partir_de else 0
        fim = self.indice(ate) if ate else len(self.filtros) - 1
        for filtro in self.filtros[inicio: fim + 1]:
            if not isinstance(dados, filtro.tipo_entrada):
                raise ErroDeContrato(
                    f"{filtro.nome} esperava {filtro.tipo_entrada.__name__}, recebeu {type(dados).__name__}")
            # Revalida o contrato na fronteira (protege contra mutações indevidas).
            dados = filtro.tipo_entrada.model_validate(dados.model_dump())
            filtro.observacoes = []
            t0 = time.perf_counter()
            dados = filtro.processar(dados)
            if not isinstance(dados, filtro.tipo_saida):
                raise ErroDeContrato(f"{filtro.nome} devolveu {type(dados).__name__}")
            self.auditoria.append(EtapaAuditoria(
                filtro=filtro.nome, iteracao=iteracao,
                duracao_s=round(time.perf_counter() - t0, 3),
                observacoes=list(filtro.observacoes)))
        return dados
