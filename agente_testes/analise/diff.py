"""Interpretação de diffs unificados (saída de `git diff`)."""
from __future__ import annotations

import re
from typing import Dict, List, Tuple

_HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def interpretar_diff(diff: str) -> Tuple[Dict[str, List[int]], Dict[str, str]]:
    """Devolve (linhas alteradas por arquivo, conteúdo de arquivos novos)."""
    alteradas: Dict[str, List[int]] = {}
    novos: Dict[str, List[str]] = {}
    atual = None
    novo_arquivo = False
    linha = 0
    for raw in diff.splitlines():
        if raw.startswith("--- "):
            novo_arquivo = raw.strip() == "--- /dev/null"
            continue
        if raw.startswith("+++ "):
            caminho = raw[4:].strip()
            if caminho == "/dev/null":
                atual = None
                continue
            atual = caminho[2:] if caminho.startswith("b/") else caminho
            alteradas.setdefault(atual, [])
            if novo_arquivo:
                novos[atual] = []
            continue
        m = _HUNK.match(raw)
        if m:
            linha = int(m.group(3))
            continue
        if atual is None or raw.startswith("diff ") or raw.startswith("index "):
            continue
        if raw.startswith("+"):
            alteradas[atual].append(linha)
            if atual in novos:
                novos[atual].append(raw[1:])
            linha += 1
        elif raw.startswith("-"):
            continue
        else:
            linha += 1
    return alteradas, {k: "\n".join(v) + "\n" for k, v in novos.items()}
