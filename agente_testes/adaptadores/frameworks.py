"""Adaptadores concretos: Pytest, JUnit 5, Jest/Vitest e Newman."""
from __future__ import annotations

import ast
import json
import re
import shlex
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..modelos.dominio import Cobertura, Linguagem, ResultadoDeTeste, StatusResultado, TipoTeste
from .base import AdaptadorFramework, ler_cobertura_xml_cobertura, ler_junit_xml


def _slug(txt: str) -> str:
    return re.sub(r"[^0-9a-zA-Z]+", "_", txt).strip("_").lower() or "alvo"


class AdaptadorPytest(AdaptadorFramework):
    nome = "pytest"
    linguagem = Linguagem.PYTHON
    imagem_docker = "agente-testes-runner-python:latest"

    def caminho_teste(self, alvo: str, tipo: TipoTeste) -> str:
        return f"tests_gerados/test_{_slug(alvo)}_{tipo.value}.py"

    def preparar_workspace(self, workspace: Path) -> None:
        (workspace / ".coveragerc").write_text(
            "[run]\nbranch = True\nomit =\n    tests_gerados/*\n    */test_*.py\n    */conftest.py\n",
            encoding="utf-8")
        (workspace / "tests_gerados").mkdir(exist_ok=True)
        (workspace / "tests_gerados" / "conftest.py").write_text(
            "import os, sys\nraiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))\n"
            "for p in (raiz, os.path.join(raiz, 'src'), os.path.join(raiz, 'lib')):\n"
            "    if os.path.isdir(p) and p not in sys.path:\n        sys.path.insert(0, p)\n",
            encoding="utf-8")

    def comando(self, arquivos_teste: List[str]) -> str:
        alvos = " ".join(shlex.quote(a) for a in arquivos_teste) or "tests_gerados"
        return ("python -m pytest -q -p no:cacheprovider --rootdir=. "
                "--junitxml=.resultados/junit.xml --cov=. --cov-config=.coveragerc "
                f"--cov-report=xml:.resultados/cobertura.xml {alvos}")

    def ler_resultados(self, workspace: Path) -> Tuple[List[ResultadoDeTeste], Optional[Cobertura]]:
        resultados = ler_junit_xml(workspace / ".resultados" / "junit.xml")
        for r in resultados:  # pytest grava classname como caminho.pontuado.do.modulo
            # (falhas de coleta vêm sem classname e com o módulo no nome)
            if not r.arquivo or not (workspace / r.arquivo).exists():
                partes = r.nome.split("::")[0].split(".")
                for i in range(len(partes), 0, -1):
                    cand = "/".join(partes[:i]) + ".py"
                    if (workspace / cand).exists():
                        r.arquivo = cand
                        break
        return resultados, ler_cobertura_xml_cobertura(workspace / ".resultados" / "cobertura.xml")

    def validar_sintaxe(self, codigo: str) -> Optional[str]:
        try:
            ast.parse(codigo)
        except SyntaxError as e:
            return f"SyntaxError linha {e.lineno}: {e.msg}"
        return None


class AdaptadorJUnit5(AdaptadorFramework):
    nome = "junit"
    linguagem = Linguagem.JAVA
    imagem_docker = "maven:3.9-eclipse-temurin-21"

    def caminho_teste(self, alvo: str, tipo: TipoTeste) -> str:
        classe = "".join(p.capitalize() for p in _slug(alvo).split("_"))
        return f"src/test/java/gerados/{classe}{tipo.value.capitalize()}Test.java"

    def comando(self, arquivos_teste: List[str]) -> str:
        # Requer pom.xml do projeto com jacoco-maven-plugin; -o evita rede (dependências em cache/imagem).
        return ("mvn -q -o -B test jacoco:report -Dmaven.test.failure.ignore=true; "
                "mkdir -p .resultados && cp target/surefire-reports/*.xml .resultados/ 2>/dev/null; "
                "cp target/site/jacoco/jacoco.xml .resultados/ 2>/dev/null; true")

    def ler_resultados(self, workspace: Path) -> Tuple[List[ResultadoDeTeste], Optional[Cobertura]]:
        resultados: List[ResultadoDeTeste] = []
        for xml in sorted((workspace / ".resultados").glob("TEST-*.xml")):
            resultados.extend(ler_junit_xml(xml))
        return resultados, self._jacoco(workspace / ".resultados" / "jacoco.xml")

    @staticmethod
    def _jacoco(arq: Path) -> Optional[Cobertura]:
        if not arq.exists():
            return None
        raiz = ET.parse(arq).getroot()
        cob, perdidas = 0, 0
        por_arquivo: Dict[str, float] = {}
        faltantes: Dict[str, List[int]] = {}
        for pacote in raiz.iter("package"):
            for sf in pacote.iter("sourcefile"):
                nome = f"{pacote.get('name')}/{sf.get('name')}"
                for c in sf.findall("counter"):
                    if c.get("type") == "LINE":
                        m, cv = int(c.get("missed")), int(c.get("covered"))
                        por_arquivo[nome] = round(100 * cv / max(1, m + cv), 1)
                faltantes[nome] = [int(l.get("nr")) for l in sf.iter("line") if l.get("ci") == "0"]
        for c in raiz.findall("counter"):
            if c.get("type") == "LINE":
                perdidas, cob = int(c.get("missed")), int(c.get("covered"))
        return Cobertura(percentual=round(100 * cob / max(1, cob + perdidas), 1), por_arquivo=por_arquivo,
                         linhas_nao_cobertas={k: v for k, v in faltantes.items() if v})


class AdaptadorJest(AdaptadorFramework):
    nome = "jest"
    linguagem = Linguagem.JAVASCRIPT
    imagem_docker = "node:20-slim"

    def caminho_teste(self, alvo: str, tipo: TipoTeste) -> str:
        return f"tests_gerados/{_slug(alvo)}.{tipo.value}.test.js"

    def comando(self, arquivos_teste: List[str]) -> str:
        alvos = " ".join(shlex.quote(a) for a in arquivos_teste)
        return ("npx --no-install jest --ci --json --outputFile=.resultados/jest.json "
                f"--coverage --coverageReporters=cobertura --coverageDirectory=.resultados {alvos}; true")

    def ler_resultados(self, workspace: Path) -> Tuple[List[ResultadoDeTeste], Optional[Cobertura]]:
        arq = workspace / ".resultados" / "jest.json"
        out: List[ResultadoDeTeste] = []
        if arq.exists():
            dados = json.loads(arq.read_text(encoding="utf-8"))
            mapa = {"passed": StatusResultado.APROVADO, "failed": StatusResultado.REPROVADO,
                    "pending": StatusResultado.IGNORADO, "skipped": StatusResultado.IGNORADO,
                    "todo": StatusResultado.IGNORADO}
            for suite in dados.get("testResults", []):
                arquivo = str(Path(suite.get("name", "")).relative_to(workspace)) \
                    if suite.get("name", "").startswith(str(workspace)) else suite.get("name")
                if not suite.get("assertionResults") and suite.get("status") == "failed":
                    out.append(ResultadoDeTeste(nome=arquivo or "suite", arquivo=arquivo,
                                                status=StatusResultado.ERRO, mensagem=suite.get("message", "")[:500]))
                for t in suite.get("assertionResults", []):
                    msgs = t.get("failureMessages") or []
                    out.append(ResultadoDeTeste(
                        nome=t.get("fullName") or t.get("title"), arquivo=arquivo,
                        status=mapa.get(t.get("status"), StatusResultado.ERRO),
                        duracao_s=(t.get("duration") or 0) / 1000,
                        mensagem=msgs[0].splitlines()[0] if msgs else None, detalhe="\n".join(msgs)[-4000:] or None))
        return out, ler_cobertura_xml_cobertura(workspace / ".resultados" / "cobertura-coverage.xml")


class AdaptadorNewman(AdaptadorFramework):
    """Testes de API REST a partir de uma coleção Postman gerada do contrato OpenAPI."""

    nome = "newman"
    linguagem = Linguagem.JAVASCRIPT
    imagem_docker = "postman/newman:6-alpine"

    def caminho_teste(self, alvo: str, tipo: TipoTeste) -> str:
        return f"tests_gerados/{_slug(alvo)}.postman_collection.json"

    def comando(self, arquivos_teste: List[str]) -> str:
        return " ; ".join(
            f"newman run {shlex.quote(a)} --env-var baseUrl=$API_BASE_URL -r junit "
            f"--reporter-junit-export .resultados/newman-{i}.xml" for i, a in enumerate(arquivos_teste)) + " ; true"

    def ler_resultados(self, workspace: Path) -> Tuple[List[ResultadoDeTeste], Optional[Cobertura]]:
        out: List[ResultadoDeTeste] = []
        for xml in sorted((workspace / ".resultados").glob("newman-*.xml")):
            out.extend(ler_junit_xml(xml))
        return out, None

    def validar_sintaxe(self, codigo: str) -> Optional[str]:
        try:
            dados = json.loads(codigo)
            if "item" not in dados:
                return "coleção Postman sem 'item'"
        except json.JSONDecodeError as e:
            return f"JSON inválido: {e}"
        return None


ADAPTADORES: Dict[str, AdaptadorFramework] = {
    a.nome: a for a in (AdaptadorPytest(), AdaptadorJUnit5(), AdaptadorJest(), AdaptadorNewman())
}
ADAPTADORES["vitest"] = ADAPTADORES["jest"]  # mesmo formato de saída JSON

PADRAO_POR_LINGUAGEM = {
    Linguagem.PYTHON: "pytest", Linguagem.JAVA: "junit",
    Linguagem.JAVASCRIPT: "jest", Linguagem.TYPESCRIPT: "jest",
}


def obter_adaptador(nome: str) -> AdaptadorFramework:
    try:
        return ADAPTADORES[nome.lower()]
    except KeyError:
        raise ValueError(f"framework não suportado: {nome}. Opções: {', '.join(sorted(ADAPTADORES))}")
