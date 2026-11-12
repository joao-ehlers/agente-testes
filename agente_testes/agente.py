"""Montagem do pipeline e laço de realimentação (Filtro 6 -> Filtro 2)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple

from .contratos import ArtefatosDeTeste, ConjuntoCenarios, ContextoAnalisado, EntradaAgente
from .llm.cliente import ModeloLinguagem, criar_modelo_a_partir_do_ambiente
from .modelos.dominio import Relatorio
from .pipeline.base import Pipeline
from .pipeline.filtros.f0_normalizacao import NormalizadorDeEntrada
from .pipeline.filtros.f1_contexto import AnalisadorDeContexto
from .pipeline.filtros.f2_cenarios import GeradorDeCenarios
from .pipeline.filtros.f3_estrategia import SeletorDeEstrategia
from .pipeline.filtros.f4_codigo import GeradorDeCodigo
from .pipeline.filtros.f5_execucao import ExecutorDeTestes
from .pipeline.filtros.f6_resultados import AnalisadorDeResultados


@dataclass
class Configuracao:
    executor: str = field(default_factory=lambda: os.getenv("AGENTE_EXECUTOR", "auto"))
    timeout_s: int = field(default_factory=lambda: int(os.getenv("AGENTE_TIMEOUT_S", "300")))
    # Limite por teste: um laço infinito derruba só o teste que o exercita, não a execução inteira.
    timeout_teste_s: int = field(default_factory=lambda: int(os.getenv("AGENTE_TIMEOUT_TESTE_S", "10")))
    cobertura_minima: float = field(default_factory=lambda: float(os.getenv("AGENTE_COBERTURA_MINIMA", "0")))
    max_iteracoes: int = field(default_factory=lambda: int(os.getenv("AGENTE_MAX_ITERACOES", "3")))
    dir_dados: Path = field(default_factory=lambda: Path(os.getenv("AGENTE_DIR_DADOS", ".agente_dados")))
    manter_workspace: Optional[Path] = None


class AgenteDeTestes:
    F_CONTEXTO = "1-analise-contexto"
    F_CENARIOS = "2-geracao-cenarios"
    F_CODIGO = "4-geracao-codigo"

    def __init__(self, llm: Optional[ModeloLinguagem] = None, config: Optional[Configuracao] = None):
        self.llm = llm or criar_modelo_a_partir_do_ambiente()
        self.config = config or Configuracao()

    def montar_pipeline(self) -> Pipeline:
        return Pipeline([
            NormalizadorDeEntrada(),
            AnalisadorDeContexto(self.llm),
            GeradorDeCenarios(self.llm),
            SeletorDeEstrategia(),
            GeradorDeCodigo(self.llm),
            ExecutorDeTestes(self.config.executor, self.config.timeout_s, self.config.manter_workspace,
                             self.config.timeout_teste_s),
            AnalisadorDeResultados(self.config.cobertura_minima, self.llm.nome),
        ])

    def analisar(self, entrada: EntradaAgente) -> Tuple[ConjuntoCenarios, Pipeline]:
        p = self.montar_pipeline()
        return p.executar(entrada, ate=self.F_CENARIOS), p

    def gerar_testes(self, entrada: EntradaAgente) -> Tuple[ArtefatosDeTeste, Pipeline]:
        p = self.montar_pipeline()
        return p.executar(entrada, ate=self.F_CODIGO), p

    def executar(self, entrada: EntradaAgente) -> Relatorio:
        p = self.montar_pipeline()
        ctx: ContextoAnalisado = p.executar(entrada, ate=self.F_CONTEXTO)
        relatorio: Relatorio = p.executar(ctx, a_partir_de=self.F_CENARIOS, iteracao=1)
        iteracao = 1
        # Falhas atribuídas ao próprio teste gerado => regenerar cenários/código com o erro como feedback.
        while iteracao < self.config.max_iteracoes and self.llm.disponivel:
            erros = [a for a in relatorio.achados if a.categoria == "erro_no_teste"]
            if not erros:
                break
            iteracao += 1
            ctx = ctx.model_copy(update={
                "iteracao": iteracao,
                "feedback": [f"{a.cenario_id or a.teste}: {a.explicacao}" for a in erros]})
            relatorio = p.executar(ctx, a_partir_de=self.F_CENARIOS, iteracao=iteracao)
        relatorio.iteracoes = iteracao
        relatorio.auditoria = p.auditoria
        return relatorio
