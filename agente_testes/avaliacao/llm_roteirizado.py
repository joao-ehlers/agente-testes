"""LLM simulado com respostas roteirizadas.

Usado nos casos de borda que medem a robustez do pipeline a saídas ruins do LLM
(JSON inválido, alvo alucinado, exceção acidental tratada como esperada). Um LLM
real não produz essas falhas sob demanda, então elas são injetadas.
"""
from __future__ import annotations

import json
from typing import Dict, List, Union

from ..llm.cliente import ModeloLinguagem


class LLMRoteirizado(ModeloLinguagem):
    nome = "simulado (roteirizado)"

    def __init__(self, respostas: Dict[str, List[Union[str, dict]]]):
        self.respostas = {k: list(v) for k, v in respostas.items()}
        self.chamadas: List[str] = []

    def _completar(self, sistema: str, usuario: str) -> str:
        chave = ("codigo" if "Escreva testes" in usuario else
                 "cenarios" if "Derive cenários" in usuario else "intencao")
        self.chamadas.append(chave)
        fila = self.respostas[chave]
        r = fila.pop(0) if len(fila) > 1 else fila[0]
        return r if isinstance(r, str) else json.dumps(r)
