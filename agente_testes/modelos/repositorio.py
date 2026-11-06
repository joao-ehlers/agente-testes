"""Model (MVC): persistência dos relatórios em arquivos JSON."""
from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import List, Optional

from .dominio import Relatorio


class RepositorioRelatorios:
    def __init__(self, diretorio: Path):
        self._dir = Path(diretorio)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _arquivo(self, relatorio_id: str) -> Path:
        if not relatorio_id.replace("-", "").isalnum():
            raise ValueError("id de relatório inválido")
        return self._dir / f"{relatorio_id}.json"

    def salvar(self, relatorio: Relatorio) -> None:
        with self._lock:
            self._arquivo(relatorio.id).write_text(relatorio.model_dump_json(indent=2), encoding="utf-8")

    def obter(self, relatorio_id: str) -> Optional[Relatorio]:
        try:
            arq = self._arquivo(relatorio_id)
        except ValueError:
            return None
        if not arq.exists():
            return None
        return Relatorio.model_validate_json(arq.read_text(encoding="utf-8"))

    def listar(self, projeto: Optional[str] = None, limite: int = 50) -> List[dict]:
        itens = []
        for arq in sorted(self._dir.glob("REL-*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            dados = json.loads(arq.read_text(encoding="utf-8"))
            if projeto and dados["projeto"]["nome"] != projeto:
                continue
            itens.append({
                "id": dados["id"],
                "projeto": dados["projeto"]["nome"],
                "criado_em": dados["criado_em"],
                "aprovado": dados["aprovado"],
                "resumo": dados["resumo"],
            })
            if len(itens) >= limite:
                break
        return itens
