"""API de exemplo que implementa exemplos/loja/openapi.yaml (para os testes de contrato).

Executar: uvicorn exemplos.loja.api_loja:app --port 8001
"""
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="API da Loja")
_PEDIDOS: Dict[int, dict] = {}


class NovoPedido(BaseModel):
    itens: Dict[str, int]
    cupom: Optional[str] = None


@app.post("/pedidos", status_code=201)
def criar_pedido(p: NovoPedido) -> dict:
    pid = len(_PEDIDOS) + 1
    _PEDIDOS[pid] = {"id": pid, **p.model_dump()}
    return _PEDIDOS[pid]


@app.get("/pedidos/{id}")
def obter_pedido(id: int) -> dict:
    if id not in _PEDIDOS:
        raise HTTPException(404, "pedido não encontrado")
    return _PEDIDOS[id]
