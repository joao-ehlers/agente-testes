"""Derivação determinística de cenários (usada sem LLM ou como complemento)."""
from __future__ import annotations

import re
from typing import Dict, List, Optional

from ..contratos import ContextoAnalisado, EndpointAPI, UnidadeCodigo
from ..modelos.dominio import CenarioDeTeste, Origem, Requisito, TipoCenario, TipoTeste
from .valores import (eh_sem_valor, limite_valido, resolver_condicao, satisfaz, tipo_base, valor_tipico,
                      valores_borda)

MAX_BORDAS_POR_UNIDADE = 6


def _requisito_para(u: UnidadeCodigo, requisitos: List[Requisito]) -> Optional[str]:
    if len(requisitos) == 1:
        return requisitos[0].id
    alvo = {u.nome.lower(), u.nome.lower().replace("_", " ")}
    for r in requisitos:
        texto = (r.descricao + " " + " ".join(r.criterios_aceite)).lower()
        if any(a in texto for a in alvo):
            return r.id
    return None


def _entradas_tipicas(u: UnidadeCodigo) -> Optional[Dict[str, object]]:
    entradas: Dict[str, object] = {}
    for p in u.parametros:
        v = valor_tipico(p)
        if eh_sem_valor(v):
            if p.obrigatorio:
                return None
            continue
        entradas[p.nome] = v
    return entradas


def _fmt(entradas: Dict[str, object]) -> str:
    return ", ".join(f"{k}={v!r}" if len(repr(v)) < 40 else f"{k}=<{type(v).__name__} len {len(v)}>"
                     for k, v in entradas.items()) or "sem argumentos"


def cenarios_de_unidade(u: UnidadeCodigo, requisitos: List[Requisito]) -> List[CenarioDeTeste]:
    req = _requisito_para(u, requisitos)
    out: List[CenarioDeTeste] = []
    automatizavel = u.tipo == "funcao" or u.construtor_sem_args
    base = _entradas_tipicas(u)
    retorno = f"um valor do tipo {u.retorno}" if u.retorno and u.retorno != "None" else "sem erro"
    exc_doc = f" (ou uma exceção documentada: {', '.join(u.excecoes)})" if u.excecoes else ""

    if base is None:
        out.append(CenarioDeTeste(
            titulo=f"{u.nome}: entradas típicas", tipo=TipoCenario.SUCESSO, alvo=u.qualificado, requisito_id=req,
            descricao=f"Dado parâmetros sem tipo inferível, quando {u.nome} é chamada, então deve concluir sem erro.",
            resultado_esperado="requer definição de entradas (anote os tipos ou use o LLM)",
            automatizavel=False))
        return out

    out.append(CenarioDeTeste(
        titulo=f"{u.nome}: entradas típicas", tipo=TipoCenario.SUCESSO, alvo=u.qualificado, requisito_id=req,
        descricao=f"Dado {_fmt(base)}, quando {u.nome} é executada, então retorna {retorno}.",
        entradas=base, resultado_esperado=retorno, automatizavel=automatizavel))

    bordas = 0
    for p in u.parametros:
        for v in valores_borda(p):
            if bordas >= MAX_BORDAS_POR_UNIDADE:
                break
            entradas = dict(base, **{p.nome: v})
            rotulo = repr(v) if len(repr(v)) < 30 else f"{type(v).__name__} de tamanho {len(v)}"
            out.append(CenarioDeTeste(
                titulo=f"{u.nome}: {p.nome}={rotulo}", tipo=TipoCenario.BORDA, alvo=u.qualificado, requisito_id=req,
                descricao=(f"Dado {p.nome}={rotulo} (valor-limite), quando {u.nome} é executada, então não deve "
                           f"lançar exceção inesperada; retorna {retorno}{exc_doc}."),
                entradas=entradas, resultado_esperado=retorno, automatizavel=automatizavel))
            bordas += 1

    vistos = set()
    for c in u.condicoes_excecao:
        p = next((x for x in u.parametros if x.nome == c.parametro), None)
        if p is None:
            continue
        v = resolver_condicao(c, p)
        if eh_sem_valor(v) or (c.parametro, repr(v)) in vistos:
            continue
        vistos.add((c.parametro, repr(v)))
        cond = f"{c.parametro} {c.operador} {c.valor!r}" if c.operador != "falsy" else f"{c.parametro} vazio/falso"
        out.append(CenarioDeTeste(
            titulo=f"{u.nome}: rejeita {cond}", tipo=TipoCenario.FALHA, alvo=u.qualificado, requisito_id=req,
            descricao=f"Dado {c.parametro}={v!r} (viola '{cond}'), quando {u.nome} é executada, então lança {c.excecao}.",
            entradas=dict(base, **{c.parametro: v}), excecao_esperada=c.excecao,
            resultado_esperado=f"lança {c.excecao}", automatizavel=automatizavel))

    # Valor-limite do lado válido: na fronteira de cada `raise`, o valor permitido não pode ser rejeitado.
    validos = set()
    for c in u.condicoes_excecao:
        p = next((x for x in u.parametros if x.nome == c.parametro), None)
        if p is None:
            continue
        v = limite_valido(c, p)
        conds_param = [x for x in u.condicoes_excecao if x.parametro == c.parametro]
        if eh_sem_valor(v) or any(satisfaz(x, v) for x in conds_param) or (c.parametro, repr(v)) in validos:
            continue
        validos.add((c.parametro, repr(v)))
        cond = f"{c.parametro} {c.operador} {c.valor!r}"
        out.append(CenarioDeTeste(
            titulo=f"{u.nome}: aceita {c.parametro}={v!r} (limite de '{cond}')", tipo=TipoCenario.BORDA,
            alvo=u.qualificado, requisito_id=req,
            descricao=(f"Dado {c.parametro}={v!r} (fronteira válida de '{cond}'), quando {u.nome} é executada, "
                       f"então não lança exceção e retorna {retorno}."),
            entradas=dict(base, **{c.parametro: v}), resultado_esperado=retorno, nao_deve_lancar=True,
            automatizavel=automatizavel))

    for p in u.parametros:  # validação de entrada: None onde o tipo não admite None
        b, opcional = tipo_base(p.anotacao)
        if b and not opcional and p.obrigatorio and b != "bool":
            out.append(CenarioDeTeste(
                titulo=f"{u.nome}: {p.nome}=None é rejeitado", tipo=TipoCenario.FALHA, alvo=u.qualificado,
                requisito_id=req, tipo_teste_sugerido=TipoTeste.VALIDACAO_ENTRADA,
                descricao=(f"Dado {p.nome}=None (tipo declarado {p.anotacao}), quando {u.nome} é executada, então "
                           f"deve rejeitar a entrada com TypeError/ValueError{exc_doc} em vez de prosseguir."),
                entradas=dict(base, **{p.nome: None}), excecao_esperada="TypeError|ValueError",
                resultado_esperado="entrada inválida rejeitada", automatizavel=automatizavel))
            break

    if u.chamadas_internas:
        out.append(CenarioDeTeste(
            titulo=f"{u.nome}: fluxo integrado com {', '.join(u.chamadas_internas)}", tipo=TipoCenario.SUCESSO,
            alvo=u.qualificado, requisito_id=req, tipo_teste_sugerido=TipoTeste.INTEGRACAO,
            descricao=(f"Dado os colaboradores reais ({', '.join(u.chamadas_internas)}) sem dublês, quando "
                       f"{u.nome} é executada com {_fmt(base)}, então o fluxo completo retorna {retorno}."),
            entradas=base, resultado_esperado=retorno, automatizavel=automatizavel))
    for c in out:
        c.origem = Origem.HEURISTICA
    return out


def _slug(txt: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", txt.lower()).strip("-")


def cenarios_de_endpoint(e: EndpointAPI) -> List[CenarioDeTeste]:
    alvo = f"{e.metodo} {e.caminho}"
    sucesso = next((c for c in e.respostas if c.startswith("2")), "200")
    out = [CenarioDeTeste(
        titulo=f"{alvo}: requisição válida", tipo=TipoCenario.SUCESSO, alvo=alvo, origem=Origem.CONTRATO,
        descricao=f"Dado uma requisição conforme o contrato, quando {alvo} é chamado, então responde {sucesso}.",
        entradas={"corpo": e.exemplo_corpo, "parametros": {p["name"]: p.get("exemplo") for p in e.parametros}},
        resultado_esperado=f"status {sucesso}", tipo_teste_sugerido=TipoTeste.API)]
    erros_4xx = [c for c in e.respostas if c.startswith("4")]
    if e.corpo_obrigatorio:
        out.append(CenarioDeTeste(
            titulo=f"{alvo}: corpo ausente", tipo=TipoCenario.FALHA, alvo=alvo, origem=Origem.CONTRATO,
            descricao=f"Dado uma requisição sem o corpo obrigatório, quando {alvo} é chamado, então responde 4xx.",
            entradas={"corpo": None, "parametros": {p["name"]: p.get("exemplo") for p in e.parametros}},
            resultado_esperado=f"status 4xx ({', '.join(erros_4xx) or '400/422'})", tipo_teste_sugerido=TipoTeste.API))
    for p in e.parametros:
        if p.get("in") == "path":
            out.append(CenarioDeTeste(
                titulo=f"{alvo}: {p['name']} inexistente", tipo=TipoCenario.BORDA, alvo=alvo, origem=Origem.CONTRATO,
                descricao=(f"Dado {p['name']} com valor inexistente/inválido, quando {alvo} é chamado, então "
                           "responde 4xx sem erro de servidor."),
                entradas={"corpo": e.exemplo_corpo, "parametros": {
                    q["name"]: (999999999 if q is p else q.get("exemplo")) for q in e.parametros}},
                resultado_esperado="status 4xx", tipo_teste_sugerido=TipoTeste.API))
            break
    return out


def cenarios_heuristicos(contexto: ContextoAnalisado) -> List[CenarioDeTeste]:
    cen: List[CenarioDeTeste] = []
    for u in contexto.unidades:
        if u.alterada:
            cen.extend(cenarios_de_unidade(u, contexto.entrada.requisitos))
    for e in contexto.endpoints:
        cen.extend(cenarios_de_endpoint(e))
    return cen
