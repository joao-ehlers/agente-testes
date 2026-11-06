"""Acesso ao modelo de linguagem.

A saída do LLM é tratada como *hipótese*: toda resposta precisa ser JSON válido
contra um esquema Pydantic antes de seguir no pipeline. Se não for, há uma nova
tentativa com o erro de validação; persistindo, o filtro cai para a heurística.
"""
from __future__ import annotations

import json
import logging
import os
import re
from abc import ABC, abstractmethod
from typing import Optional, Type, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

log = logging.getLogger("agente_testes.llm")
T = TypeVar("T", bound=BaseModel)


class ErroLLM(Exception):
    pass


class ModeloLinguagem(ABC):
    nome: str = "abstrato"
    disponivel: bool = True

    @abstractmethod
    def _completar(self, sistema: str, usuario: str) -> str: ...

    def gerar_json(self, sistema: str, usuario: str, esquema: Type[T], tentativas: int = 2) -> T:
        instrucao = (
            "\n\nResponda SOMENTE com um objeto JSON válido conforme este JSON Schema:\n"
            + json.dumps(esquema.model_json_schema(), ensure_ascii=False))
        prompt = usuario + instrucao
        ultimo_erro: Optional[str] = None
        for _ in range(tentativas):
            texto = self._completar(sistema, prompt if not ultimo_erro else
                                    prompt + f"\n\nSua resposta anterior era inválida: {ultimo_erro}. Corrija.")
            try:
                return esquema.model_validate(json.loads(_extrair_json(texto)))
            except (json.JSONDecodeError, ValidationError) as e:
                ultimo_erro = str(e)[:800]
                log.warning("Resposta do LLM rejeitada pelo esquema: %s", ultimo_erro)
        raise ErroLLM(f"resposta do LLM não passou na validação de esquema: {ultimo_erro}")


def _extrair_json(texto: str) -> str:
    texto = texto.strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", texto, re.S)
    if m:
        return m.group(1)
    ini = texto.find("{")
    fim = texto.rfind("}")
    return texto[ini: fim + 1] if ini >= 0 and fim > ini else texto


class SemModelo(ModeloLinguagem):
    """Usado quando nenhuma chave está configurada: os filtros usam só heurísticas."""

    nome = "nenhum (modo heurístico)"
    disponivel = False

    def _completar(self, sistema: str, usuario: str) -> str:
        raise ErroLLM("nenhum modelo de linguagem configurado")


class ClienteGemini(ModeloLinguagem):
    URL = "https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"
    # 404 vazio e 503 ("high demand") aparecem de forma intermitente na API: são tratados como transitórios.
    TRANSITORIOS = {404, 408, 429, 500, 502, 503, 504}

    def __init__(self, chave: str, modelo: str = "gemini-3.5-flash", timeout: float = 180.0,
                 alternativos: Optional[list] = None, tentativas: int = 4, espera_base: float = 2.0):
        self.chave = chave
        self.modelos = [modelo] + [m for m in (alternativos or []) if m != modelo]
        self.nome = f"gemini:{modelo}"
        self.tentativas = tentativas
        self.espera_base = espera_base
        self._http = httpx.Client(timeout=timeout)

    def _completar(self, sistema: str, usuario: str) -> str:
        import time
        corpo = {
            "systemInstruction": {"parts": [{"text": sistema}]},
            "contents": [{"role": "user", "parts": [{"text": usuario}]}],
            "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"},
        }
        ultimo = "sem resposta"
        for modelo in self.modelos:
            for i in range(self.tentativas):
                try:
                    r = self._http.post(self.URL.format(modelo=modelo), json=corpo,
                                        headers={"x-goog-api-key": self.chave})
                except httpx.HTTPError as e:
                    ultimo = f"{modelo}: {type(e).__name__}"
                else:
                    if r.status_code == 200:
                        try:
                            dados = r.json()
                            return "".join(p.get("text", "") for p in dados["candidates"][0]["content"]["parts"])
                        except (ValueError, KeyError, IndexError) as e:
                            raise ErroLLM(f"resposta inesperada do Gemini: {e}") from e
                    ultimo = f"{modelo}: HTTP {r.status_code} {r.text[:200]}"
                    if r.status_code not in self.TRANSITORIOS:
                        raise ErroLLM(f"falha ao chamar Gemini ({ultimo})")
                log.warning("Gemini indisponível (%s); tentativa %d/%d", ultimo, i + 1, self.tentativas)
                time.sleep(self.espera_base * (2 ** i))
        raise ErroLLM(f"falha ao chamar Gemini após novas tentativas ({ultimo})")


class ClienteCompativelOpenAI(ModeloLinguagem):
    """Qualquer servidor com API compatível (/v1/chat/completions): vLLM, Ollama, etc."""

    def __init__(self, base_url: str, modelo: str, chave: Optional[str] = None, timeout: float = 120.0):
        self.base_url = base_url.rstrip("/")
        self.modelo = modelo
        self.chave = chave
        self.nome = f"compativel:{modelo}"
        self._http = httpx.Client(timeout=timeout)

    def _completar(self, sistema: str, usuario: str) -> str:
        cab = {"Authorization": f"Bearer {self.chave}"} if self.chave else {}
        try:
            r = self._http.post(f"{self.base_url}/chat/completions", headers=cab, json={
                "model": self.modelo, "temperature": 0.2,
                "messages": [{"role": "system", "content": sistema}, {"role": "user", "content": usuario}]})
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except (httpx.HTTPError, KeyError, IndexError) as e:
            raise ErroLLM(f"falha ao chamar modelo compatível: {e}") from e


def criar_modelo_a_partir_do_ambiente() -> ModeloLinguagem:
    if os.getenv("AGENTE_LLM", "").lower() in ("nenhum", "off", "heuristico"):
        return SemModelo()
    chave = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if chave:
        alternativos = [m.strip() for m in os.getenv("GEMINI_MODELOS_ALTERNATIVOS", "gemini-3.8-flash").split(",")
                        if m.strip()]
        return ClienteGemini(chave, os.getenv("GEMINI_MODEL", "gemini-3.5-flash"), alternativos=alternativos)
    base = os.getenv("LLM_BASE_URL")
    if base:
        return ClienteCompativelOpenAI(base, os.getenv("LLM_MODEL", "llama3.1"), os.getenv("LLM_API_KEY"))
    return SemModelo()
