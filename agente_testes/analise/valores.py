"""Valores de teste derivados de anotações de tipo (heurística determinística)."""
from __future__ import annotations

import ast
import re
from typing import Any, List, Optional, Tuple

from ..contratos import Condicao, Parametro

_SEM_VALOR = object()

TIPICOS = {"int": 7, "float": 2.5, "str": "abc", "bool": True, "list": [1, 2, 3], "dict": {"a": 1},
           "tuple": [1, 2], "set": [1, 2]}
BORDAS = {"int": [0, -1, 10 ** 12], "float": [0.0, -0.01, 1e12], "str": ["", " " * 3, "ç" * 256],
          "list": [[], [0]], "dict": [{}], "bool": [False], "tuple": [[]], "set": [[]]}
_ALIASES = {"List": "list", "Sequence": "list", "Iterable": "list", "Dict": "dict", "Mapping": "dict",
            "Tuple": "tuple", "Set": "set", "FrozenSet": "set"}


def tipo_base(anotacao: Optional[str]) -> Tuple[Optional[str], bool]:
    """('int', aceita_none) a partir de 'Optional[int]', 'int | None', 'List[int]'..."""
    if not anotacao:
        return None, False
    a = anotacao.replace("typing.", "").strip().strip("'\"")
    opcional = False
    m = re.fullmatch(r"Optional\[(.*)\]", a)
    if m:
        a, opcional = m.group(1), True
    if "|" in a:
        partes = [p.strip() for p in a.split("|")]
        opcional = opcional or "None" in partes
        partes = [p for p in partes if p != "None"]
        a = partes[0] if partes else "None"
    base = a.split("[", 1)[0].strip()
    base = _ALIASES.get(base, base)
    return (base if base in TIPICOS else None), opcional


def valor_tipico(p: Parametro) -> Any:
    base, _ = tipo_base(p.anotacao)
    if base:
        return TIPICOS[base]
    if p.default is not None:
        try:
            return ast.literal_eval(p.default)
        except Exception:
            return _SEM_VALOR
    return _SEM_VALOR


def valores_borda(p: Parametro) -> List[Any]:
    base, opcional = tipo_base(p.anotacao)
    vals = list(BORDAS.get(base, [])) if base else []
    if opcional:
        vals.append(None)
    return vals


def resolver_condicao(c: Condicao, p: Parametro) -> Any:
    """Valor que satisfaz a condição que leva ao `raise` (ex.: `x < 0` -> -1)."""
    base, _ = tipo_base(p.anotacao)
    v = c.valor
    num = isinstance(v, (int, float)) and not isinstance(v, bool)
    passo = 0.5 if (base == "float" or isinstance(v, float)) else 1
    if c.operador == "falsy":
        return {"int": 0, "float": 0.0, "str": "", "list": [], "dict": {}, "bool": False}.get(base or "", None)
    if c.operador in ("is", "==") and v is None:
        return None
    if c.operador == "is not":
        return _SEM_VALOR
    if c.operador.startswith("len") and isinstance(v, int):
        op = c.operador[3:]
        n = {"==": v, "<": v - 1, "<=": v, ">": v + 1, ">=": v, "!=": v + 1}.get(op, _SEM_VALOR)
        if n is _SEM_VALOR or n < 0:
            return _SEM_VALOR
        return "x" * n if base == "str" else [0] * n
    if not num:
        if c.operador == "==":
            return v
        return _SEM_VALOR
    return {"<": v - passo, "<=": v, ">": v + passo, ">=": v, "==": v, "!=": v + passo}.get(c.operador, _SEM_VALOR)


def _passo(c: Condicao, p: Parametro) -> float:
    base, _ = tipo_base(p.anotacao)
    return 0.5 if (base == "float" or isinstance(c.valor, float)) else 1


def limite_valido(c: Condicao, p: Parametro) -> Any:
    """Valor mais próximo da fronteira que NÃO dispara o `raise` (análise de valor-limite, lado válido).

    Ex.: `x < 0` -> 0; `x > 100` -> 100; `x <= 0` -> 1 (int) ou 0.5 (float).
    """
    v = c.valor
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        return _SEM_VALOR
    passo = _passo(c, p)
    return {"<": v, "<=": v + passo, ">": v, ">=": v - passo}.get(c.operador, _SEM_VALOR)


def satisfaz(c: Condicao, x: Any) -> bool:
    """A condição numérica `x <op> valor` é verdadeira? (falso para condições não numéricas)."""
    v = c.valor
    if not isinstance(v, (int, float)) or isinstance(v, bool) or not isinstance(x, (int, float)):
        return False
    return {"<": x < v, "<=": x <= v, ">": x > v, ">=": x >= v, "==": x == v, "!=": x != v}.get(c.operador, False)


def eh_sem_valor(v: Any) -> bool:
    return v is _SEM_VALOR
