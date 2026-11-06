"""Filtro 3 — Seleção da Estratégia de teste (padrão Strategy)."""
from __future__ import annotations

from collections import OrderedDict
from typing import List, Optional

from ...contratos import ConjuntoCenarios, ItemPlano, PlanoDeTeste
from ...estrategias.estrategias import TODAS, EstrategiaDeTeste
from ..base import Filtro


class SeletorDeEstrategia(Filtro[ConjuntoCenarios, PlanoDeTeste]):
    nome = "3-selecao-estrategia"
    tipo_entrada = ConjuntoCenarios
    tipo_saida = PlanoDeTeste

    def __init__(self, estrategias: Optional[List[EstrategiaDeTeste]] = None):
        super().__init__()
        self.estrategias = estrategias or TODAS

    def processar(self, conj: ConjuntoCenarios) -> PlanoDeTeste:
        ctx = conj.contexto
        ativas = [e for e in self.estrategias if e.ativa(ctx)]
        self.anotar("estratégias ativas: " + ", ".join(e.tipo.value for e in ativas))
        grupos: "OrderedDict[tuple, List[str]]" = OrderedDict()
        sem_estrategia = 0
        for c in conj.cenarios:
            estrategia = next((e for e in ativas if e.aplicavel(c, ctx)), None)
            if estrategia is None:
                sem_estrategia += 1
                continue
            # Agrupa por arquivo-fonte (unidades) ou por recurso (endpoints) => um arquivo de teste por grupo
            unidade = next((u for u in ctx.unidades if u.qualificado == c.alvo), None)
            alvo = unidade.modulo if unidade else c.alvo.split(" ", 1)[-1].strip("/").split("/")[0] or c.alvo
            grupos.setdefault((estrategia.tipo, alvo), []).append(c.id)
        if sem_estrategia:
            self.anotar(f"{sem_estrategia} cenário(s) sem estratégia ativa aplicável")
        itens = [ItemPlano(tipo_teste=t, alvo=a, cenarios=ids) for (t, a), ids in grupos.items()]
        for i in itens:
            self.anotar(f"{i.tipo_teste.value} -> {i.alvo}: {len(i.cenarios)} cenário(s)")
        return PlanoDeTeste(conjunto=conj, framework=ctx.entrada.projeto.framework or "pytest", itens=itens)
