"""Teste de mutação: mede se os testes gerados pelo agente detectam defeitos injetados.

Cada mutante altera um único ponto de `corpus/precos.py` (código correto). O mutante
é "morto" quando o portão do agente reprova; "sobrevive" quando o agente aprova o
código defeituoso. Escore de mutação = mortos / total (Myers et al., 2011; Jia e Harman, 2011).
"""
from __future__ import annotations

import ast
import copy
from dataclasses import dataclass
from typing import List, Tuple

# Operadores clássicos: ROR (relacional), AOR (aritmético), CRP (constante) e RVR (remoção de validação).
_ROR = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt, ast.Eq: ast.NotEq}
_AOR = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.Div, ast.Div: ast.Mult}
NOMES = {"ROR": "Relacional (< ↔ <=)", "AOR": "Aritmético (+ ↔ −, × ↔ ÷)",
         "CRP": "Constante (c → c+1)", "RVR": "Remoção de validação (raise)"}


@dataclass
class Mutante:
    id: str
    operador: str
    linha: int
    descricao: str
    codigo: str


def _pontos(arvore: ast.AST) -> List[Tuple[str, ast.AST]]:
    pontos = []
    for no in ast.walk(arvore):
        if isinstance(no, ast.Compare) and type(no.ops[0]) in _ROR:
            pontos.append(("ROR", no))
        elif isinstance(no, ast.BinOp) and type(no.op) in _AOR:
            pontos.append(("AOR", no))
        elif isinstance(no, ast.AugAssign) and type(no.op) in _AOR:
            pontos.append(("AOR", no))
        elif isinstance(no, ast.Constant) and type(no.value) in (int, float) and not isinstance(no.value, bool):
            pontos.append(("CRP", no))
        elif isinstance(no, ast.If) and any(isinstance(s, ast.Raise) for s in no.body):
            pontos.append(("RVR", no))
    return sorted(pontos, key=lambda p: (p[1].lineno, p[1].col_offset, p[0]))


def gerar_mutantes(codigo: str) -> List[Mutante]:
    original = ast.parse(codigo)
    # Constantes dentro de round(x, 2) só mudam o arredondamento: ficam de fora (mutantes quase equivalentes).
    ignorar = {id(a) for n in ast.walk(original) if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "round"
               for a in n.args[1:]}
    mutantes = []
    pontos_originais = _pontos(original)
    for j, (op, alvo) in enumerate(pontos_originais):
        if id(alvo) in ignorar:
            continue
        arvore = copy.deepcopy(original)
        par = _pontos(arvore)[j][1]  # deepcopy preserva a ordem de ast.walk
        antes = ast.unparse(par).splitlines()[0]
        if op == "ROR":
            par.ops[0] = _ROR[type(par.ops[0])]()
        elif op == "AOR":
            par.op = _AOR[type(par.op)]()
        elif op == "CRP":
            par.value = par.value + 1
        elif op == "RVR":
            par.body = [ast.Pass()]
        depois = "validação removida (raise → pass)" if op == "RVR" else ast.unparse(par).splitlines()[0]
        mutantes.append(Mutante(f"M{len(mutantes) + 1:02d}", op, alvo.lineno, f"{antes}  →  {depois}",
                                ast.unparse(ast.fix_missing_locations(arvore))))
    return mutantes
