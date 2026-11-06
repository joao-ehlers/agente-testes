"""Leitura de contratos OpenAPI 3 (JSON ou YAML)."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Union

import yaml

from ..contratos import EndpointAPI

_METODOS = ("get", "post", "put", "patch", "delete")


def carregar_openapi(fonte: Union[str, Dict[str, Any], None]) -> Optional[Dict[str, Any]]:
    if fonte is None:
        return None
    if isinstance(fonte, dict):
        return fonte
    try:
        return json.loads(fonte)
    except json.JSONDecodeError:
        dados = yaml.safe_load(fonte)
        if not isinstance(dados, dict):
            raise ValueError("contrato OpenAPI inválido")
        return dados


def _resolver(spec: Dict[str, Any], no: Any) -> Any:
    if isinstance(no, dict) and "$ref" in no:
        alvo: Any = spec
        for parte in no["$ref"].lstrip("#/").split("/"):
            alvo = alvo.get(parte, {})
        return _resolver(spec, alvo)
    return no


def exemplo_de_esquema(spec: Dict[str, Any], esquema: Any, profundidade: int = 0) -> Any:
    esquema = _resolver(spec, esquema) or {}
    if "example" in esquema:
        return esquema["example"]
    if "enum" in esquema:
        return esquema["enum"][0]
    tipo = esquema.get("type", "object" if "properties" in esquema else "string")
    if profundidade > 4:
        return None
    if tipo == "object":
        return {k: exemplo_de_esquema(spec, v, profundidade + 1)
                for k, v in esquema.get("properties", {}).items()}
    if tipo == "array":
        return [exemplo_de_esquema(spec, esquema.get("items", {}), profundidade + 1)]
    if tipo == "integer":
        return max(1, esquema.get("minimum", 1))
    if tipo == "number":
        return float(max(1, esquema.get("minimum", 1)))
    if tipo == "boolean":
        return True
    if esquema.get("format") == "email":
        return "teste@exemplo.com"
    return "texto"


def extrair_endpoints(spec: Optional[Dict[str, Any]]) -> List[EndpointAPI]:
    if not spec:
        return []
    out = []
    for caminho, ops in (spec.get("paths") or {}).items():
        comuns = ops.get("parameters", [])
        for metodo in _METODOS:
            op = ops.get(metodo)
            if not op:
                continue
            params = [_resolver(spec, p) for p in comuns + op.get("parameters", [])]
            corpo = _resolver(spec, op.get("requestBody")) or {}
            exemplo = None
            conteudo = (corpo.get("content") or {}).get("application/json")
            if conteudo:
                exemplo = conteudo.get("example") or exemplo_de_esquema(spec, conteudo.get("schema", {}))
            for p in params:
                p.setdefault("exemplo", exemplo_de_esquema(spec, p.get("schema", {})))
            out.append(EndpointAPI(
                metodo=metodo.upper(), caminho=caminho, operation_id=op.get("operationId"),
                resumo=op.get("summary"), parametros=params,
                corpo_obrigatorio=bool(corpo.get("required")), exemplo_corpo=exemplo,
                respostas=sorted(str(c) for c in (op.get("responses") or {}).keys())))
    return out
