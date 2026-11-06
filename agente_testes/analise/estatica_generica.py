"""Análise estática leve (por expressões regulares) para Java e JavaScript/TypeScript.

Não substitui um parser completo: serve para localizar as unidades públicas e dar
ao LLM um mapa do código. A geração de testes para essas linguagens depende do LLM.
"""
from __future__ import annotations

import re
from typing import List, Optional

from ..contratos import Parametro, UnidadeCodigo

_JAVA_CLASSE = re.compile(r"\b(?:public\s+)?(?:final\s+|abstract\s+)?class\s+(\w+)")
_JAVA_METODO = re.compile(
    r"^\s*public\s+(?:static\s+)?(?:final\s+)?([\w<>\[\],\s]+?)\s+(\w+)\s*\(([^)]*)\)\s*(?:throws\s+([\w.,\s]+))?\s*\{",
    re.M)
_JS_FUNCAO = re.compile(
    r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s*(\w+)\s*\(([^)]*)\)", re.M)
_JS_ARROW = re.compile(
    r"^\s*(?:export\s+)?(?:const|let)\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*(?::\s*[\w<>\[\]|]+\s*)?=>", re.M)
_JS_THROW = re.compile(r"throw\s+new\s+(\w+)")


def _linha(codigo: str, pos: int) -> int:
    return codigo.count("\n", 0, pos) + 1


def _fim_bloco(codigo: str, pos: int) -> int:
    abre = codigo.find("{", pos)
    if abre < 0:
        return _linha(codigo, pos)
    prof = 0
    for i in range(abre, len(codigo)):
        if codigo[i] == "{":
            prof += 1
        elif codigo[i] == "}":
            prof -= 1
            if prof == 0:
                return _linha(codigo, i)
    return _linha(codigo, len(codigo))


def _params(txt: str, java: bool) -> List[Parametro]:
    out = []
    for p in [x.strip() for x in txt.split(",") if x.strip()]:
        if java:
            partes = p.replace("final ", "").rsplit(" ", 1)
            out.append(Parametro(nome=partes[-1], anotacao=partes[0] if len(partes) > 1 else None))
        else:
            nome, _, resto = p.partition("=")
            nome, _, tipo = nome.partition(":")
            out.append(Parametro(nome=nome.strip(), anotacao=tipo.strip() or None,
                                 default=resto.strip() or None, obrigatorio=not resto))
    return out


def analisar_generico(caminho: str, codigo: str, linguagem: str,
                      linhas_alteradas: Optional[List[int]] = None) -> List[UnidadeCodigo]:
    alteradas = set(linhas_alteradas or [])
    modulo = caminho.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    unidades: List[UnidadeCodigo] = []
    linhas = codigo.splitlines()

    def add(nome, params, retorno, inicio_pos, excecoes, classe=None):
        ini = _linha(codigo, inicio_pos)
        fim = _fim_bloco(codigo, inicio_pos)
        trecho = "\n".join(linhas[ini - 1: fim])
        unidades.append(UnidadeCodigo(
            nome=nome, qualificado=f"{classe or modulo}.{nome}", arquivo=caminho, modulo=modulo,
            tipo="metodo" if classe else "funcao", classe=classe, parametros=params, retorno=retorno,
            excecoes=excecoes or sorted(set(_JS_THROW.findall(trecho))),
            linha_inicio=ini, linha_fim=fim, complexidade=1 + len(re.findall(r"\b(if|for|while|case|catch)\b|&&|\|\|", trecho)),
            alterada=(not alteradas) or bool(alteradas & set(range(ini, fim + 1))), trecho=trecho))

    if linguagem == "java":
        m = _JAVA_CLASSE.search(codigo)
        classe = m.group(1) if m else modulo
        for mm in _JAVA_METODO.finditer(codigo):
            if mm.group(2) == classe:
                continue
            exc = [e.strip().rsplit(".", 1)[-1] for e in (mm.group(4) or "").split(",") if e.strip()]
            add(mm.group(2), _params(mm.group(3), True), mm.group(1).strip(), mm.start(), exc, classe)
    else:
        for rx in (_JS_FUNCAO, _JS_ARROW):
            for mm in rx.finditer(codigo):
                add(mm.group(1), _params(mm.group(2), False), None, mm.start(), [])
    return unidades
