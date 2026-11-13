"""Filtro 6 — Analisador de Resultados e produção do relatório."""
from __future__ import annotations

import re
from typing import Dict, List, Optional

from ...analise.estatica_python import contar_linhas_por_unidade
from ...contratos import ResultadoPipelineExecucao
from ...modelos.dominio import (Achado, CasoDeTeste, Origem, Relatorio, ResultadoDeTeste, ResumoExecucao, Risco,
                                Severidade, StatusResultado, TipoTeste)
from ..base import Filtro

# Erros que indicam problema no próprio teste gerado (e não no código sob teste).
_ERRO_DO_TESTE = re.compile(
    r"(ImportError|ModuleNotFoundError|SyntaxError|IndentationError|fixture '.*' not found|"
    r"NameError: name '\w+' is not defined|collection failure|TypeError: .*(unexpected keyword|missing \d+ required))")

# Teste interrompido por tempo (pytest-timeout) ou execução inteira estourando o limite.
_TEMPO_ESGOTADO = re.compile(r"(Timeout \(?>[\d.]+s\)?|tempo limite total de \d+s excedido)")
# Acesso a rede bloqueado pelo isolamento (--network none): é dependência externa, não defeito do código.
_REDE_BLOQUEADA = re.compile(
    r"(Temporary failure in name resolution|Name or service not known|nodename nor servname|"
    r"Network is unreachable|socket\.gaierror|ConnectionRefusedError|httpx\.ConnectError|"
    r"urllib\.error\.URLError|requests\.exceptions\.ConnectionError)")


def _intervalos(linhas: List[int]) -> str:
    if not linhas:
        return ""
    partes, ini, ant = [], linhas[0], linhas[0]
    for n in linhas[1:] + [None]:
        if n is not None and n == ant + 1:
            ant = n
            continue
        partes.append(f"{ini}" if ini == ant else f"{ini}-{ant}")
        if n is not None:
            ini = ant = n
    return ", ".join(partes)


class AnalisadorDeResultados(Filtro[ResultadoPipelineExecucao, Relatorio]):
    nome = "6-analise-resultados"
    tipo_entrada = ResultadoPipelineExecucao
    tipo_saida = Relatorio

    def __init__(self, cobertura_minima: float = 0.0, modelo: str = "nenhum"):
        super().__init__()
        self.cobertura_minima = cobertura_minima
        self.modelo = modelo

    def _caso_de(self, r: ResultadoDeTeste, casos: List[CasoDeTeste]) -> Optional[CasoDeTeste]:
        for c in casos:
            if (r.cenario_id and r.cenario_id in c.cenarios) or (r.arquivo and r.arquivo == c.caminho):
                return c
        return None

    def processar(self, res: ResultadoPipelineExecucao) -> Relatorio:
        art, exe = res.artefatos, res.execucao
        conj = art.plano.conjunto
        ctx = conj.contexto
        cen_por_id = {c.id: c for c in conj.cenarios}
        achados: List[Achado] = []

        anteriores: Dict[str, str] = {}
        for rel in ctx.entrada.relatorios_anteriores:
            for c in rel.get("casos") or (rel.get("execucao") or {}).get("resultados") or []:
                anteriores[c.get("nome")] = c.get("status")

        for r in exe.resultados:
            if r.status in (StatusResultado.APROVADO, StatusResultado.IGNORADO):
                continue
            caso = self._caso_de(r, art.casos)
            cen = cen_por_id.get(r.cenario_id or "")
            texto = f"{r.mensagem or ''}\n{r.detalhe or ''}"
            alvo = cen.alvo if cen else None
            if _TEMPO_ESGOTADO.search(texto):
                categoria = "tempo_esgotado"
                explic = (f"{alvo or r.nome} não terminou dentro do limite de tempo "
                          f"(possível laço infinito ou bloqueio): {(r.mensagem or '').strip()[:150]}")
            elif _REDE_BLOQUEADA.search(texto) and caso is not None:
                categoria = "dependencia_externa"
                explic = (f"{alvo} depende de rede, bloqueada no ambiente isolado; isole a dependência com um "
                          f"dublê (mock) ou cubra com teste de integração: {(r.mensagem or '').strip()[:150]}")
            elif _ERRO_DO_TESTE.search(texto) and caso is not None:
                categoria = "erro_no_teste"
                explic = f"o teste gerado não executou corretamente ({(r.mensagem or '').strip()[:200]}); será regenerado"
            elif caso is None:
                categoria = "regressao" if anteriores.get(r.nome) == "aprovado" else "falha_suite_existente"
                explic = f"teste da suíte existente falhou: {(r.mensagem or '')[:200]}"
            elif caso.tipo_teste == TipoTeste.VALIDACAO_ENTRADA:
                categoria = "validacao_ausente"
                explic = f"{alvo} aceitou entrada inválida sem rejeitá-la: {(r.mensagem or '')[:200]}"
            else:
                categoria = "defeito_suspeito"
                hip = " (hipótese do LLM: confirme o resultado esperado)" if caso.origem == Origem.LLM else ""
                explic = f"{(r.mensagem or 'falha').strip()[:300]}{hip}"
            if r.nome in ctx.testes_instaveis:
                explic += " | também falhou em execução anterior (falha recorrente)"
            achados.append(Achado(categoria=categoria, teste=r.nome, cenario_id=r.cenario_id, alvo=alvo,
                                  explicacao=explic))

        # Trechos não cobertos, mapeados para as unidades analisadas
        trechos: List[str] = []
        riscos: List[Risco] = list(ctx.riscos)
        if exe.cobertura:
            por_unidade = contar_linhas_por_unidade(
                [u for u in ctx.unidades if u.alterada], exe.cobertura.linhas_nao_cobertas)
            unidades = {u.qualificado: u for u in ctx.unidades}
            for q, linhas in por_unidade.items():
                trechos.append(f"{unidades[q].arquivo}:{_intervalos(linhas)} ({q})")
            for arq, pct in exe.cobertura.por_arquivo.items():
                if pct < 50:
                    riscos.append(Risco(descricao=f"cobertura baixa ({pct}%)", severidade=Severidade.MEDIA, alvo=arq))
        for cid in art.cenarios_sem_codigo:
            c = cen_por_id.get(cid)
            if c:
                riscos.append(Risco(descricao=f"cenário sem teste automatizado: {c.titulo}",
                                    severidade=Severidade.BAIXA, alvo=c.alvo))

        resumo = ResumoExecucao.de(exe.resultados)
        motivos = []
        if resumo.total == 0:
            motivos.append("nenhum teste executado")
        if resumo.reprovados:
            motivos.append(f"{resumo.reprovados} teste(s) reprovado(s)")
        if resumo.erros:
            motivos.append(f"{resumo.erros} teste(s) com erro")
        if exe.cobertura and exe.cobertura.percentual < self.cobertura_minima:
            motivos.append(f"cobertura {exe.cobertura.percentual}% abaixo do mínimo {self.cobertura_minima}%")

        cats = {}
        for a in achados:
            cats[a.categoria] = cats.get(a.categoria, 0) + 1
        self.anotar(f"resumo: {resumo.model_dump()} | achados: {cats or 'nenhum'}")
        return Relatorio(
            projeto=ctx.entrada.projeto, requisitos=ctx.entrada.requisitos, cenarios=conj.cenarios,
            casos=art.casos, execucao=exe, resumo=resumo, cobertura=exe.cobertura, riscos=riscos,
            trechos_nao_cobertos=trechos, achados=achados, iteracoes=ctx.iteracao,
            aprovado=not motivos, motivo_reprovacao=motivos, modelo_linguagem=self.modelo)
