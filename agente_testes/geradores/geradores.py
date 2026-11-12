"""Padrão Factory Method (GoF) para os geradores de código de teste.

* Produto: `GeradorDeCodigoTeste` (interface comum usada pelo Filtro 4).
* Produtos concretos: unitário, integração, validação de entrada, API e E2E.
* Criador: `CriadorDeGerador`, cujo método-fábrica `criar_gerador` é sobrescrito
  pelos criadores concretos. O núcleo do pipeline só conhece o criador abstrato.

Cada gerador tenta primeiro o LLM (quando configurado) e valida a sintaxe do
código devolvido via adaptador; se falhar, usa templates determinísticos.
"""
from __future__ import annotations

import ast
import json
import re
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

from ..adaptadores.base import AdaptadorFramework
from ..contratos import ContextoAnalisado, EndpointAPI, ItemPlano, UnidadeCodigo
from ..llm.cliente import ErroLLM, ModeloLinguagem
from ..llm.prompts import SISTEMA, RespostaCodigo, prompt_codigo
from ..modelos.dominio import CasoDeTeste, CenarioDeTeste, Linguagem, Origem, TipoCenario, TipoTeste
from ..analise.valores import tipo_base

ResultadoGeracao = Tuple[List[CasoDeTeste], List[str]]  # (casos, ids de cenários sem código)


def nome_teste(c: CenarioDeTeste) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", c.titulo.lower()).strip("_")[:50]
    return f"test_{c.id.lower().replace('-', '_')}_{slug}"


def _docstring(txt: str) -> str:
    return txt.replace("\\", "\\\\").replace('"""', "'''")


# ======================================================================= Produto
class GeradorDeCodigoTeste(ABC):
    tipo: TipoTeste

    def __init__(self, adaptador: AdaptadorFramework, llm: ModeloLinguagem):
        self.adaptador = adaptador
        self.llm = llm
        self.observacoes: List[str] = []

    def gerar(self, item: ItemPlano, cenarios: List[CenarioDeTeste], contexto: ContextoAnalisado) -> ResultadoGeracao:
        """Cenários do LLM -> código do LLM; cenários determinísticos -> templates (arquivo separado)."""
        caminho = self.adaptador.caminho_teste(item.alvo, item.tipo_teste)
        do_llm = [c for c in cenarios if c.origem == Origem.LLM]
        outros = [c for c in cenarios if c.origem != Origem.LLM]
        casos: List[CasoDeTeste] = []
        sem: List[str] = []
        if do_llm and self.llm.disponivel:
            try:
                caso = self._gerar_com_llm(item, do_llm, contexto, caminho)
                if caso:
                    casos.append(caso)
                    do_llm = []
            except ErroLLM as e:
                self.observacoes.append(f"LLM indisponível para {item.alvo}: {e}; usando template")
        restantes = do_llm + outros
        if restantes:
            destino = caminho
            if casos:  # já existe um arquivo do LLM para este item
                base, ext = caminho.rsplit(".", 1)
                destino = f"{base}_deterministico.{ext}"
            caso, sem = self._gerar_template(item, restantes, contexto, destino)
            if caso:
                casos.append(caso)
        return casos, sem

    def _gerar_com_llm(self, item, cenarios, contexto, caminho) -> Optional[CasoDeTeste]:
        unidades = [u for u in contexto.unidades if u.qualificado == item.alvo or u.arquivo == item.alvo]
        codigo = "\n\n".join(f"# {u.arquivo}\n{u.trecho}" for u in unidades) or "\n\n".join(
            f"# {a.caminho}\n{a.conteudo[:6000]}" for a in contexto.entrada.arquivos[:3])
        modulos = "\n".join(sorted({f"- {u.modulo} (arquivo {u.arquivo})" for u in contexto.unidades})) or "-"
        # Cenários são regenerados (novos ids) a cada iteração: o feedback é filtrado pelo alvo/arquivo.
        modulo_teste = caminho.rsplit(".", 1)[0].replace("/", ".")
        feedback = [f for f in contexto.feedback if item.alvo in f or modulo_teste in f] or list(contexto.feedback)
        resp = self.llm.gerar_json(SISTEMA, prompt_codigo(
            self.adaptador.nome, self.adaptador.linguagem.value, item.tipo_teste.value,
            json.dumps([c.model_dump(mode="json") for c in cenarios], ensure_ascii=False, indent=1),
            codigo, modulos, caminho, feedback), RespostaCodigo)
        if not resp.arquivos:
            return None
        conteudo = resp.arquivos[0].conteudo
        erro = self.adaptador.validar_sintaxe(conteudo)
        if erro:
            self.observacoes.append(f"código do LLM para {item.alvo} rejeitado ({erro})")
            return None
        return CasoDeTeste(caminho=caminho, codigo=conteudo, tipo_teste=item.tipo_teste,
                           framework=self.adaptador.nome, cenarios=[c.id for c in cenarios], origem=Origem.LLM)

    def _gerar_template(self, item, cenarios, contexto, caminho) -> ResultadoGeracao:
        if self.adaptador.linguagem != Linguagem.PYTHON:
            self.observacoes.append(f"sem template para {self.adaptador.nome}; {item.alvo} requer LLM")
            return None, [c.id for c in cenarios]
        corpos, sem = [], []
        for c in cenarios:
            corpo = self.template_python(c, contexto) if c.automatizavel else None
            (corpos.append(corpo) if corpo else sem.append(c.id))
        if not corpos:
            return None, sem
        codigo = self.cabecalho_python(item, contexto) + "\n\n" + "\n\n\n".join(corpos) + "\n"
        erro = self.adaptador.validar_sintaxe(codigo)
        if erro:  # pragma: no cover - templates são determinísticos
            raise RuntimeError(f"template inválido: {erro}")
        ids = [c.id for c in cenarios if c.id not in sem]
        return CasoDeTeste(caminho=caminho, codigo=codigo, tipo_teste=item.tipo_teste,
                           framework=self.adaptador.nome, cenarios=ids, origem=Origem.HEURISTICA), sem

    # ---- hooks para templates Python
    def cabecalho_python(self, item: ItemPlano, contexto: ContextoAnalisado) -> str:
        return (f'"""Testes {self.tipo.value} gerados pelo Agente de Testes para {item.alvo}.\n\n'
                'Gerados a partir de cenários (hipóteses); a execução é a fonte da verdade.\n"""\n'
                "import asyncio\n\nimport pytest")

    @abstractmethod
    def template_python(self, c: CenarioDeTeste, contexto: ContextoAnalisado) -> Optional[str]: ...


# ----------------------------------------------------------- helpers de código Python
def _unidade(contexto: ContextoAnalisado, alvo: str) -> Optional[UnidadeCodigo]:
    return next((u for u in contexto.unidades if u.qualificado == alvo), None)


def _chamada(u: UnidadeCodigo, entradas: Dict[str, object]) -> Tuple[str, str]:
    """(import, expressão de chamada)."""
    args = ", ".join(f"{k}={v!r}" for k, v in entradas.items())
    if u.classe:
        imp = f"from {u.modulo} import {u.classe}"
        alvo = f"{u.classe}.{u.nome}" if u.tipo == "funcao" else f"{u.classe}().{u.nome}"
    else:
        imp = f"from {u.modulo} import {u.nome}"
        alvo = u.nome
    expr = f"{alvo}({args})"
    return imp, (f"asyncio.run({expr})" if u.assincrona else expr)


def _excecoes(nomes: List[str]) -> Tuple[str, List[str]]:
    """Tupla Python de exceções; nomes não-builtin são importados do módulo."""
    builtins_ = __builtins__ if isinstance(__builtins__, dict) else vars(__builtins__)
    validos = [n for n in nomes if n]
    return ("(" + ", ".join(validos) + ("," if len(validos) == 1 else "") + ")") if validos else "()", \
        [n for n in validos if n not in builtins_]


def _imports_excecoes(u: UnidadeCodigo, externas: List[str]) -> str:
    return "".join(f"    from {u.modulo} import {n}\n" for n in externas)


def _assert_tipo(u: UnidadeCodigo) -> str:
    base, opcional = tipo_base(u.retorno)
    py = {"int": "int", "float": "(int, float)", "str": "str", "bool": "bool", "list": "list", "dict": "dict",
          "tuple": "tuple", "set": "(set, frozenset)"}.get(base or "")
    if not py:
        return "    assert True  # retorno sem tipo verificável; o teste valida ausência de erro inesperado\n"
    cond = f"resultado is None or isinstance(resultado, {py})" if opcional else f"isinstance(resultado, {py})"
    return f"    assert {cond}, f'retorno inesperado: {{resultado!r}}'\n"


def _literal(txt: str):
    try:
        return True, ast.literal_eval(txt.strip())
    except Exception:
        return False, None


# ===================================================================== Produtos concretos
class GeradorTesteUnitario(GeradorDeCodigoTeste):
    tipo = TipoTeste.UNITARIO

    def template_python(self, c, contexto):
        u = _unidade(contexto, c.alvo)
        if not u:
            return None
        imp, chamada = _chamada(u, c.entradas)
        cab = f'def {nome_teste(c)}():\n    """{_docstring(c.descricao)}"""\n    {imp}\n'
        if c.tipo == TipoCenario.FALHA and c.excecao_esperada:
            tupla, ext = _excecoes(c.excecao_esperada.split("|"))
            return cab + _imports_excecoes(u, ext) + f"    with pytest.raises({tupla}):\n        {chamada}\n"
        if c.nao_deve_lancar:
            return cab + f"    resultado = {chamada}\n" + _assert_tipo(u)
        ok, esperado = _literal(c.resultado_esperado)
        if ok and c.origem == Origem.LLM:
            return cab + f"    resultado = {chamada}\n    assert resultado == {esperado!r}\n"
        tupla, ext = _excecoes(u.excecoes)
        return (cab + _imports_excecoes(u, ext)
                + f"    try:\n        resultado = {chamada}\n"
                + f"    except {tupla}:\n        return  # exceção documentada pelo código: comportamento aceito\n"
                + _assert_tipo(u))


class GeradorTesteIntegracao(GeradorTesteUnitario):
    """Mesmo template, mas sem dublês: os colaboradores reais são exercitados juntos."""

    tipo = TipoTeste.INTEGRACAO


class GeradorTesteValidacaoEntrada(GeradorTesteUnitario):
    tipo = TipoTeste.VALIDACAO_ENTRADA

    def template_python(self, c, contexto):
        u = _unidade(contexto, c.alvo)
        if not u:
            return None
        imp, chamada = _chamada(u, c.entradas)
        tupla, ext = _excecoes(sorted(set((c.excecao_esperada or "TypeError|ValueError").split("|") + u.excecoes)))
        return (f'def {nome_teste(c)}():\n    """{_docstring(c.descricao)}"""\n    {imp}\n'
                + _imports_excecoes(u, ext)
                + f"    with pytest.raises({tupla}):\n        resultado = {chamada}\n"
                + "        pytest.fail(f'entrada inválida aceita sem validação; retorno: {resultado!r}')\n")


class GeradorTesteAPI(GeradorDeCodigoTeste):
    tipo = TipoTeste.API

    def cabecalho_python(self, item, contexto):
        base = contexto.entrada.api_base_url or ""
        return (f'"""Testes de contrato de API gerados a partir do OpenAPI para {item.alvo}."""\n'
                "import os\n\nimport httpx\nimport pytest\n\n"
                f"BASE_URL = os.getenv('API_BASE_URL', {base!r})\n"
                "pytestmark = pytest.mark.skipif(not BASE_URL, reason='API_BASE_URL não definida')")

    def template_python(self, c, contexto):
        metodo, caminho = c.alvo.split(" ", 1)
        params = dict(c.entradas.get("parametros") or {})
        ep: Optional[EndpointAPI] = next((e for e in contexto.endpoints if f"{e.metodo} {e.caminho}" == c.alvo), None)
        em_path = {p["name"] for p in (ep.parametros if ep else []) if p.get("in") == "path"}
        url = caminho
        for n in em_path:
            url = url.replace("{" + n + "}", str(params.pop(n, 1)))
        corpo = c.entradas.get("corpo")
        esperado = c.resultado_esperado
        if "4xx" in esperado:
            check = "    assert 400 <= r.status_code < 500, r.text\n"
        else:
            m = re.search(r"(\d{3})", esperado)
            check = f"    assert r.status_code == {int(m.group(1)) if m else 200}, r.text\n"
        return (f'def {nome_teste(c)}():\n    """{_docstring(c.descricao)}"""\n'
                f"    r = httpx.request({metodo!r}, BASE_URL.rstrip('/') + {url!r}, params={params!r}, "
                f"json={corpo!r}, timeout=10)\n" + check)


class GeradorTesteE2E(GeradorDeCodigoTeste):
    """Playwright: depende do LLM (fluxos de interface não são inferíveis por AST)."""

    tipo = TipoTeste.E2E

    def template_python(self, c, contexto):
        return None


class GeradorColecaoNewman(GeradorDeCodigoTeste):
    """Gera uma coleção Postman (framework 'newman') a partir dos cenários de API."""

    tipo = TipoTeste.API

    def _gerar_template(self, item, cenarios, contexto, caminho):
        itens = []
        for c in cenarios:
            metodo, url = c.alvo.split(" ", 1)
            for k, v in (c.entradas.get("parametros") or {}).items():
                url = url.replace("{" + k + "}", str(v))
            m = re.search(r"(\d{3})", c.resultado_esperado)
            teste = ("pm.expect(pm.response.code).to.be.within(400,499);" if "4xx" in c.resultado_esperado
                     else f"pm.response.to.have.status({int(m.group(1)) if m else 200});")
            req = {"method": metodo, "url": "{{baseUrl}}" + url, "header": [
                {"key": "Content-Type", "value": "application/json"}]}
            if c.entradas.get("corpo") is not None:
                req["body"] = {"mode": "raw", "raw": json.dumps(c.entradas["corpo"])}
            itens.append({"name": nome_teste(c), "request": req, "event": [{"listen": "test", "script": {
                "exec": [f"pm.test({c.titulo!r}, function () {{ {teste} }});"]}}]})
        colecao = {"info": {"name": f"Agente de Testes - {item.alvo}",
                            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"},
                   "item": itens}
        return CasoDeTeste(caminho=caminho, codigo=json.dumps(colecao, indent=2, ensure_ascii=False),
                           tipo_teste=TipoTeste.API, framework="newman", cenarios=[c.id for c in cenarios],
                           origem=Origem.CONTRATO), []

    def template_python(self, c, contexto):  # pragma: no cover - não usado
        return None


# ======================================================================= Criadores
class CriadorDeGerador(ABC):
    @abstractmethod
    def criar_gerador(self, adaptador: AdaptadorFramework, llm: ModeloLinguagem) -> GeradorDeCodigoTeste:
        """Factory Method."""

    def produzir(self, item: ItemPlano, cenarios: List[CenarioDeTeste], contexto: ContextoAnalisado,
                 adaptador: AdaptadorFramework, llm: ModeloLinguagem) -> Tuple[ResultadoGeracao, List[str]]:
        gerador = self.criar_gerador(adaptador, llm)
        resultado = gerador.gerar(item, cenarios, contexto)
        return resultado, gerador.observacoes


class CriadorUnitario(CriadorDeGerador):
    def criar_gerador(self, adaptador, llm):
        return GeradorTesteUnitario(adaptador, llm)


class CriadorIntegracao(CriadorDeGerador):
    def criar_gerador(self, adaptador, llm):
        return GeradorTesteIntegracao(adaptador, llm)


class CriadorValidacaoEntrada(CriadorDeGerador):
    def criar_gerador(self, adaptador, llm):
        return GeradorTesteValidacaoEntrada(adaptador, llm)


class CriadorAPI(CriadorDeGerador):
    def criar_gerador(self, adaptador, llm):
        if adaptador.nome == "newman":
            return GeradorColecaoNewman(adaptador, llm)
        return GeradorTesteAPI(adaptador, llm)


class CriadorE2E(CriadorDeGerador):
    def criar_gerador(self, adaptador, llm):
        return GeradorTesteE2E(adaptador, llm)


CRIADORES: Dict[TipoTeste, CriadorDeGerador] = {
    TipoTeste.UNITARIO: CriadorUnitario(),
    TipoTeste.INTEGRACAO: CriadorIntegracao(),
    TipoTeste.VALIDACAO_ENTRADA: CriadorValidacaoEntrada(),
    TipoTeste.API: CriadorAPI(),
    TipoTeste.E2E: CriadorE2E(),
}
