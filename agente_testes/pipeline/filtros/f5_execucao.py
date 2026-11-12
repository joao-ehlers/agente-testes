"""Filtro 5 — Executor em ambiente isolado (Docker)."""
from __future__ import annotations

import re
import shutil
import tempfile
from collections import OrderedDict
from pathlib import Path
from typing import Dict, List, Optional

from ...adaptadores.frameworks import obter_adaptador
from ...contratos import ArtefatosDeTeste, ResultadoPipelineExecucao
from ...execucao.executores import escolher_executor
from ...modelos.dominio import Cobertura, ExecucaoDeTeste, Linguagem, ResultadoDeTeste, StatusResultado
from ..base import Filtro

_ID_CENARIO = re.compile(r"cen_([0-9a-f]{10})", re.I)


def _seguro(base: Path, relativo: str) -> Path:
    destino = (base / relativo).resolve()
    if not str(destino).startswith(str(base.resolve())):
        raise ValueError(f"caminho fora do workspace: {relativo}")
    return destino


class ExecutorDeTestes(Filtro[ArtefatosDeTeste, ResultadoPipelineExecucao]):
    nome = "5-execucao"
    tipo_entrada = ArtefatosDeTeste
    tipo_saida = ResultadoPipelineExecucao

    def __init__(self, preferencia_executor: str = "auto", timeout_s: int = 300,
                 manter_workspace: Optional[Path] = None, timeout_teste_s: int = 10):
        super().__init__()
        self.timeout_teste_s = timeout_teste_s
        self.preferencia = preferencia_executor
        self.timeout_s = timeout_s
        self.manter_workspace = manter_workspace

    def processar(self, art: ArtefatosDeTeste) -> ResultadoPipelineExecucao:
        entrada = art.plano.conjunto.contexto.entrada
        workspace = Path(tempfile.mkdtemp(prefix="agente-testes-"))
        try:
            for a in entrada.arquivos:
                _seguro(workspace, a.caminho).parent.mkdir(parents=True, exist_ok=True)
                _seguro(workspace, a.caminho).write_text(a.conteudo, encoding="utf-8")
            existentes = []
            for t in entrada.testes_existentes:
                destino = _seguro(workspace, t.caminho)
                destino.parent.mkdir(parents=True, exist_ok=True)
                destino.write_text(t.conteudo, encoding="utf-8")
                existentes.append(t.caminho)
            (workspace / ".resultados").mkdir()

            grupos: "OrderedDict[str, List[str]]" = OrderedDict()
            for caso in art.casos:
                destino = _seguro(workspace, caso.caminho)
                destino.parent.mkdir(parents=True, exist_ok=True)
                destino.write_text(caso.codigo, encoding="utf-8")
                grupos.setdefault(caso.framework, []).append(caso.caminho)
            principal = entrada.projeto.framework or "pytest"
            if existentes:
                grupos.setdefault(principal, [])
                grupos[principal] = existentes + grupos[principal]

            if not grupos:
                self.anotar("nenhum teste para executar")
                return ResultadoPipelineExecucao(artefatos=art, execucao=ExecucaoDeTeste(
                    executor="nenhum", framework=principal, comando="", codigo_saida=0))

            resultados: List[ResultadoDeTeste] = []
            cobertura: Optional[Cobertura] = None
            saidas, comandos, executores, codigo_final, duracao = [], [], set(), 0, 0.0
            # Lido pelo plugin pytest-timeout (local e na imagem Docker).
            env: Dict[str, str] = {"PYTEST_TIMEOUT": str(self.timeout_teste_s)}
            if entrada.api_base_url:
                env["API_BASE_URL"] = entrada.api_base_url
            for framework, arquivos in grupos.items():
                adaptador = obter_adaptador(framework)
                adaptador.preparar_workspace(workspace)
                executor = escolher_executor(self.preferencia, adaptador.imagem_docker)
                rede = framework == "newman" or any("_api" in a for a in arquivos)
                if executor.nome == "local" and adaptador.linguagem != Linguagem.PYTHON \
                        and not shutil.which(adaptador.comando([]).split()[0]):
                    self.anotar(f"{framework}: ferramenta ausente localmente; use Docker")
                    continue
                url_api = env.get("API_BASE_URL", "")
                if executor.nome == "docker" and ("localhost" in url_api or "127.0.0.1" in url_api):
                    env["API_BASE_URL"] = url_api.replace("localhost", "host.docker.internal") \
                        .replace("127.0.0.1", "host.docker.internal")
                saida = executor.executar(workspace, adaptador.comando(arquivos), adaptador.imagem_docker,
                                          self.timeout_s, env, rede)
                executores.add(executor.nome)
                self.anotar(f"{framework} via {executor.nome}: código {saida.codigo} em {saida.duracao_s:.1f}s")
                if executor.nome == "local":
                    self.anotar("ATENÇÃO: execução sem isolamento (Docker indisponível ou desabilitado)")
                rs, cob = adaptador.ler_resultados(workspace)
                if not rs and saida.codigo not in (0, 5):
                    msg = (f"tempo limite total de {self.timeout_s}s excedido" if saida.codigo == 124
                           else "framework não produziu resultados")
                    rs = [ResultadoDeTeste(nome=f"{framework}::execucao", status=StatusResultado.ERRO,
                                           mensagem=msg, detalhe=saida.saida[-3000:])]
                resultados += rs
                cobertura = cobertura or cob
                saidas.append(saida.saida)
                comandos.append(saida.comando)
                codigo_final = codigo_final or saida.codigo
                duracao += saida.duracao_s

            for r in resultados:
                m = _ID_CENARIO.search(r.nome)
                if m:
                    r.cenario_id = f"CEN-{m.group(1).lower()}"
            if cobertura:
                raiz = str(workspace.resolve())
                cobertura.por_arquivo = {k.replace(raiz + "/", ""): v for k, v in cobertura.por_arquivo.items()}
                cobertura.linhas_nao_cobertas = {k.replace(raiz + "/", ""): v
                                                 for k, v in cobertura.linhas_nao_cobertas.items()}
            execucao = ExecucaoDeTeste(
                executor="+".join(sorted(executores)) or "nenhum", framework="+".join(grupos), comando=" && ".join(comandos),
                codigo_saida=codigo_final, duracao_s=round(duracao, 2), resultados=resultados, cobertura=cobertura,
                saida="\n".join(saidas)[-20000:])
            self.anotar(f"{len(resultados)} resultado(s); cobertura={cobertura.percentual if cobertura else 'n/d'}%")
            return ResultadoPipelineExecucao(artefatos=art, execucao=execucao)
        finally:
            if self.manter_workspace:
                shutil.copytree(workspace, self.manter_workspace, dirs_exist_ok=True)
            shutil.rmtree(workspace, ignore_errors=True)
