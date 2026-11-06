"""Integração com o Agente de Documentação de Software (contrato JSON sobre REST).

Opcional: se AGENTE_DOCUMENTACAO_URL não estiver definida, as chamadas não fazem nada,
permitindo que o Agente de Testes opere de forma independente.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

import httpx

from ..modelos.dominio import Relatorio

log = logging.getLogger("agente_testes.integracoes")


def resultado_consolidado(r: Relatorio) -> Dict[str, Any]:
    """Contrato enviado ao Agente de Documentação."""
    return {
        "origem": "agente-testes",
        "versao_contrato": "1.0",
        "relatorio_id": r.id,
        "projeto": r.projeto.nome,
        "gerado_em": r.criado_em.isoformat(),
        "aprovado": r.aprovado,
        "resumo": r.resumo.model_dump(),
        "cobertura_percentual": r.cobertura.percentual if r.cobertura else None,
        "requisitos": [{
            "id": q.id,
            "cenarios": [c.id for c in r.cenarios if c.requisito_id == q.id],
            "validado": bool([c for c in r.cenarios if c.requisito_id == q.id]) and not any(
                a.cenario_id in {c.id for c in r.cenarios if c.requisito_id == q.id} for a in r.achados),
        } for q in r.requisitos],
        "achados": [a.model_dump() for a in r.achados],
    }


class ClienteAgenteDocumentacao:
    def __init__(self, base_url: Optional[str] = None, timeout: float = 10.0):
        self.base_url = (base_url or os.getenv("AGENTE_DOCUMENTACAO_URL") or "").rstrip("/")
        self.timeout = timeout

    @property
    def configurado(self) -> bool:
        return bool(self.base_url)

    def enviar_resultado(self, relatorio: Relatorio) -> bool:
        if not self.configurado:
            return False
        try:
            httpx.post(f"{self.base_url}/resultados-testes", json=resultado_consolidado(relatorio),
                       timeout=self.timeout).raise_for_status()
            return True
        except httpx.HTTPError as e:
            log.warning("falha ao enviar resultado ao Agente de Documentação: %s", e)
            return False

    def consultar_especificacao(self, projeto: str) -> Optional[Dict[str, Any]]:
        if not self.configurado:
            return None
        try:
            r = httpx.get(f"{self.base_url}/especificacoes/{projeto}", timeout=self.timeout)
            r.raise_for_status()
            return r.json()
        except httpx.HTTPError as e:
            log.warning("falha ao consultar especificação: %s", e)
            return None
