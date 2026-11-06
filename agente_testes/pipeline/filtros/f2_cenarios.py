"""Filtro 2 — Gerador de Cenários de Teste (sucesso, falha e borda)."""
from __future__ import annotations

from ...analise.cenarios_heuristicos import cenarios_de_endpoint, cenarios_heuristicos
from ...contratos import ConjuntoCenarios, ContextoAnalisado
from ...llm.cliente import ErroLLM, ModeloLinguagem
from ...llm.prompts import SISTEMA, RespostaCenarios, prompt_cenarios
from ...modelos.dominio import CenarioDeTeste, Origem, Risco, Severidade, TipoCenario
from ..base import Filtro
from .f1_contexto import resumo_codigo, texto_requisitos

# Exceções aceitáveis como rejeição de entrada inválida mesmo sem `raise` explícito no código.
_EXCECOES_DE_VALIDACAO = {"TypeError", "ValueError", "TypeError|ValueError"}


class GeradorDeCenarios(Filtro[ContextoAnalisado, ConjuntoCenarios]):
    nome = "2-geracao-cenarios"
    tipo_entrada = ContextoAnalisado
    tipo_saida = ConjuntoCenarios

    def __init__(self, llm: ModeloLinguagem):
        super().__init__()
        self.llm = llm

    def processar(self, ctx: ContextoAnalisado) -> ConjuntoCenarios:
        cenarios = []
        alteradas = [u for u in ctx.unidades if u.alterada]
        if self.llm.disponivel and alteradas:
            try:
                alvos = [u.qualificado for u in alteradas] + [f"{e.metodo} {e.caminho}" for e in ctx.endpoints]
                r = self.llm.gerar_json(SISTEMA, prompt_cenarios(
                    resumo_codigo(alteradas), texto_requisitos(ctx.entrada.requisitos), ctx.intencao or "",
                    alvos, ctx.feedback), RespostaCenarios)
                validos = set(alvos)
                unidades = {u.qualificado: u for u in alteradas}
                for c in r.cenarios:
                    if c.alvo not in validos:
                        self.anotar(f"cenário do LLM descartado: alvo inexistente '{c.alvo}'")
                        continue
                    u = unidades.get(c.alvo)
                    exc = (c.excecao_esperada or "").strip()
                    if u and exc and exc not in u.excecoes and exc not in _EXCECOES_DE_VALIDACAO:
                        # Hipótese que "legitima" uma exceção acidental: tratada como defeito potencial.
                        self.anotar(f"cenário do LLM rejeitado: espera {exc}, que {c.alvo} não lança deliberadamente")
                        ctx.riscos.append(Risco(
                            descricao=f"{exc} acidental em '{c.titulo}': o código não trata este caso "
                                      f"explicitamente (possível defeito; ver cenários de borda)",
                            severidade=Severidade.ALTA, alvo=c.alvo, origem=Origem.LLM))
                        continue
                    try:
                        cenarios.append(CenarioDeTeste(origem=Origem.LLM, **c.model_dump()))
                    except ValueError as ex:
                        self.anotar(f"cenário do LLM inválido descartado: {ex}")
                self.anotar(f"LLM propôs {len(cenarios)} cenário(s) válidos")
            except ErroLLM as ex:
                self.anotar(f"LLM indisponível: {ex}; usando heurística")

        if not cenarios:
            cenarios = cenarios_heuristicos(ctx)
            self.anotar(f"{len(cenarios)} cenário(s) derivados por heurística (AST/contrato)")
        else:
            # Defesa em profundidade: cenários determinísticos de borda/validação/condições sempre
            # complementam os do LLM (não dependem da interpretação do modelo).
            complementares = [c for c in cenarios_heuristicos(ctx)
                              if c.tipo != TipoCenario.SUCESSO and not c.alvo.split(" ", 1)[0].isupper()]
            cenarios += complementares
            self.anotar(f"{len(complementares)} cenário(s) heurísticos complementares (borda/falha/validação)")
            com_alvo = {c.alvo for c in cenarios}  # contrato OpenAPI é determinístico: sempre complementa
            for e in ctx.endpoints:
                if f"{e.metodo} {e.caminho}" not in com_alvo:
                    cenarios += cenarios_de_endpoint(e)

        if ctx.feedback and ctx.iteracao > 1:
            self.anotar(f"iteração {ctx.iteracao}: {len(ctx.feedback)} feedback(s) considerados")

        # Rastreabilidade requisito -> cenário
        cobertos = {c.requisito_id for c in cenarios if c.requisito_id}
        for r in ctx.entrada.requisitos:
            if r.id not in cobertos:
                ctx.riscos.append(Risco(
                    descricao=f"requisito {r.id} sem cenário automatizado associado (validar manualmente ou usar LLM)",
                    severidade=Severidade.MEDIA, alvo=r.id))
        por_tipo = {t: sum(1 for c in cenarios if c.tipo.value == t) for t in ("sucesso", "falha", "borda")}
        self.anotar(f"cenários por tipo: {por_tipo}")
        return ConjuntoCenarios(contexto=ctx, cenarios=cenarios)
