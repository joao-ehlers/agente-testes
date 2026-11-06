"""Filtro 1 — Analisador de Contexto (análise estática + interpretação pelo LLM)."""
from __future__ import annotations

from ...analise.estatica_generica import analisar_generico
from ...analise.estatica_python import analisar_python, nomes_testados
from ...analise.openapi import extrair_endpoints
from ...contratos import ContextoAnalisado, EntradaNormalizada
from ...llm.cliente import ErroLLM, ModeloLinguagem
from ...llm.prompts import SISTEMA, RespostaIntencao, prompt_intencao
from ...modelos.dominio import Linguagem, Origem, Risco, Severidade
from ..base import Filtro


def resumo_codigo(contexto_unidades, limite: int = 24000) -> str:
    partes, total = [], 0
    for u in contexto_unidades:
        bloco = f"# {u.qualificado} ({u.arquivo}:{u.linha_inicio})\n{u.trecho}\n"
        if total + len(bloco) > limite:
            partes.append("# ... (truncado)")
            break
        partes.append(bloco)
        total += len(bloco)
    return "\n".join(partes)


def texto_requisitos(requisitos) -> str:
    return "\n".join(f"- [{r.id}] {r.descricao}" + "".join(f"\n    - {c}" for c in r.criterios_aceite)
                     for r in requisitos)


class AnalisadorDeContexto(Filtro[EntradaNormalizada, ContextoAnalisado]):
    nome = "1-analise-contexto"
    tipo_entrada = EntradaNormalizada
    tipo_saida = ContextoAnalisado

    def __init__(self, llm: ModeloLinguagem):
        super().__init__()
        self.llm = llm

    def processar(self, e: EntradaNormalizada) -> ContextoAnalisado:
        unidades, riscos = [], []
        for a in e.arquivos:
            try:
                if a.linguagem == Linguagem.PYTHON:
                    unidades += analisar_python(a.caminho, a.conteudo, e.linhas_alteradas.get(a.caminho))
                else:
                    unidades += analisar_generico(a.caminho, a.conteudo, a.linguagem.value,
                                                  e.linhas_alteradas.get(a.caminho))
            except SyntaxError as ex:
                riscos.append(Risco(descricao=f"{a.caminho} não compila: {ex}", severidade=Severidade.ALTA,
                                    alvo=a.caminho))
        endpoints = extrair_endpoints(e.openapi)
        alteradas = [u for u in unidades if u.alterada]
        self.anotar(f"{len(unidades)} unidade(s) ({len(alteradas)} no escopo da mudança), {len(endpoints)} endpoint(s)")

        # Riscos determinísticos
        testados = nomes_testados([t.conteudo for t in e.testes_existentes])
        sem_teste = [u.qualificado for u in alteradas if u.nome not in testados]
        for u in alteradas:
            if u.complexidade >= 8:
                riscos.append(Risco(descricao=f"complexidade ciclomática alta ({u.complexidade})",
                                    severidade=Severidade.ALTA if u.complexidade >= 12 else Severidade.MEDIA,
                                    alvo=u.qualificado))
            if any(p.anotacao is None for p in u.parametros) and u.arquivo.endswith(".py"):
                riscos.append(Risco(descricao="parâmetros sem anotação de tipo dificultam inferir entradas",
                                    severidade=Severidade.BAIXA, alvo=u.qualificado))
            if u.tipo == "metodo" and not u.construtor_sem_args:
                riscos.append(Risco(descricao="classe exige argumentos no construtor; testes heurísticos não "
                                    "instanciam automaticamente", severidade=Severidade.BAIXA, alvo=u.qualificado))
        if e.testes_existentes and sem_teste:
            riscos.append(Risco(descricao=f"{len(sem_teste)} unidade(s) alterada(s) sem referência na suíte existente",
                                severidade=Severidade.MEDIA, alvo=", ".join(sem_teste[:10])))

        instaveis = []
        for rel in e.relatorios_anteriores:
            casos = rel.get("casos") or (rel.get("execucao") or {}).get("resultados") or []
            instaveis += [c.get("nome") for c in casos if c.get("status") in ("reprovado", "erro")]
        if instaveis:
            riscos.append(Risco(descricao=f"{len(set(instaveis))} teste(s) falharam em execuções anteriores",
                                severidade=Severidade.MEDIA, alvo=", ".join(sorted(set(instaveis))[:10])))

        contexto = ContextoAnalisado(entrada=e, unidades=unidades, endpoints=endpoints, riscos=riscos,
                                     unidades_sem_teste=sem_teste, testes_instaveis=sorted(set(instaveis)))

        # Interpretação por LLM (hipótese)
        if self.llm.disponivel and (alteradas or endpoints):
            try:
                r = self.llm.gerar_json(SISTEMA, prompt_intencao(
                    resumo_codigo(alteradas), texto_requisitos(e.requisitos), e.descricao_funcionalidade or ""),
                    RespostaIntencao)
                contexto.intencao = r.intencao
                contexto.riscos += [Risco(descricao=x.descricao, severidade=x.severidade, alvo=x.alvo,
                                          origem=Origem.LLM) for x in r.riscos]
                self.anotar(f"LLM inferiu intenção e {len(r.riscos)} risco(s)")
            except ErroLLM as ex:
                self.anotar(f"LLM indisponível na análise de contexto: {ex}")
        if not contexto.intencao:
            contexto.intencao = e.descricao_funcionalidade or "; ".join(
                f"{u.qualificado}: {(u.docstring or '').splitlines()[0]}" for u in alteradas if u.docstring) or None
        return contexto
