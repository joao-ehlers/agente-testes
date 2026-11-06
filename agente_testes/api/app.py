"""Controller (MVC) exposto via FastAPI.

Endpoints apenas validam a requisição (Pydantic), delegam ao `ControladorAgente`
(GRASP Controller) e devolvem JSON — sem lógica de geração ou execução.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import PlainTextResponse

from ..contratos import EntradaAgente, RespostaAgente
from ..controlador import ControladorAgente
from ..modelos.dominio import Relatorio
from ..visoes.markdown import renderizar_markdown

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(
    title="Agente de Testes de Software",
    version="1.0.0",
    description="Analisa código e requisitos, gera cenários e testes automatizados, executa em ambiente "
                "isolado e interpreta os resultados (ODS 9).",
)


@lru_cache
def controlador() -> ControladorAgente:
    return ControladorAgente()


def _erro_entrada(e: Exception) -> HTTPException:
    return HTTPException(status_code=422, detail=str(e))


@app.get("/saude")
def saude(c: ControladorAgente = Depends(controlador)) -> dict:
    return {"status": "ok", "modelo_linguagem": c.modelo, "executor": c.config.executor}


@app.post("/analisar", response_model=RespostaAgente, summary="Analisa contexto e deriva cenários")
async def analisar(entrada: EntradaAgente, c: ControladorAgente = Depends(controlador)) -> RespostaAgente:
    try:
        return await run_in_threadpool(c.analisar, entrada)
    except ValueError as e:
        raise _erro_entrada(e)


@app.post("/gerar-testes", response_model=RespostaAgente, summary="Gera cenários e código de teste (sem executar)")
async def gerar_testes(entrada: EntradaAgente, c: ControladorAgente = Depends(controlador)) -> RespostaAgente:
    try:
        return await run_in_threadpool(c.gerar_testes, entrada)
    except ValueError as e:
        raise _erro_entrada(e)


@app.post("/executar", response_model=Relatorio, summary="Pipeline completo: gera, executa e analisa")
async def executar(entrada: EntradaAgente, c: ControladorAgente = Depends(controlador)) -> Relatorio:
    try:
        return await run_in_threadpool(c.executar, entrada)
    except ValueError as e:
        raise _erro_entrada(e)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/relatorio", summary="Lista relatórios")
def listar(projeto: Optional[str] = None, c: ControladorAgente = Depends(controlador)) -> List[dict]:
    return c.listar_relatorios(projeto)


@app.get("/relatorio/{relatorio_id}", response_model=Relatorio, summary="Obtém um relatório")
def obter(relatorio_id: str, c: ControladorAgente = Depends(controlador)) -> Relatorio:
    r = c.obter_relatorio(relatorio_id)
    if not r:
        raise HTTPException(status_code=404, detail="relatório não encontrado")
    return r


@app.get("/relatorio/{relatorio_id}/markdown", response_class=PlainTextResponse)
def obter_markdown(relatorio_id: str, codigo: bool = Query(False),
                   c: ControladorAgente = Depends(controlador)) -> str:
    r = c.obter_relatorio(relatorio_id)
    if not r:
        raise HTTPException(status_code=404, detail="relatório não encontrado")
    return renderizar_markdown(r, incluir_codigo=codigo)
