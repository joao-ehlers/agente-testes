"""Filtro 4 — Gerador de Código de Teste (Factory Method + Adapter)."""
from __future__ import annotations

from typing import Dict

from ...adaptadores.frameworks import obter_adaptador
from ...contratos import ArtefatosDeTeste, PlanoDeTeste
from ...geradores.geradores import CRIADORES, CriadorDeGerador
from ...llm.cliente import ModeloLinguagem
from ...modelos.dominio import Linguagem, TipoTeste
from ..base import Filtro


class GeradorDeCodigo(Filtro[PlanoDeTeste, ArtefatosDeTeste]):
    nome = "4-geracao-codigo"
    tipo_entrada = PlanoDeTeste
    tipo_saida = ArtefatosDeTeste

    def __init__(self, llm: ModeloLinguagem, criadores: Dict[TipoTeste, CriadorDeGerador] = None):
        super().__init__()
        self.llm = llm
        self.criadores = criadores or CRIADORES

    def processar(self, plano: PlanoDeTeste) -> ArtefatosDeTeste:
        ctx = plano.conjunto.contexto
        por_id = {c.id: c for c in plano.conjunto.cenarios}
        adaptador_projeto = obter_adaptador(plano.framework)
        # Testes de API de projetos não-Python usam coleções Newman (independem da linguagem).
        adaptador_api = adaptador_projeto if adaptador_projeto.linguagem == Linguagem.PYTHON \
            or adaptador_projeto.nome == "newman" else obter_adaptador("newman")

        casos, sem_codigo = [], []
        for item in plano.itens:
            adaptador = adaptador_api if item.tipo_teste == TipoTeste.API else adaptador_projeto
            criador = self.criadores[item.tipo_teste]
            (gerados, sem), obs = criador.produzir(item, [por_id[i] for i in item.cenarios], ctx, adaptador, self.llm)
            for o in obs:
                self.anotar(o)
            sem_codigo += sem
            for caso in gerados:
                casos.append(caso)
                self.anotar(f"{caso.caminho}: {len(caso.cenarios)} teste(s) [{caso.origem.value}]")
        if sem_codigo:
            self.anotar(f"{len(sem_codigo)} cenário(s) sem código automatizado")
        return ArtefatosDeTeste(plano=plano, casos=casos, cenarios_sem_codigo=sem_codigo)
