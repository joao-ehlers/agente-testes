"""Executa a bancada de avaliação e calcula as métricas da Entrega 2.

Métricas (todas calculadas a partir das execuções reais registradas em `execucoes.csv`):
* taxa de acerto — casos em que o resultado obtido coincidiu com o esperado em todas as repetições;
* precisão / revocação / F1 — achados de defeito comparados ao gabarito de cada caso
  (VP: unidade com defeito real apontada; FP: unidade apontada sem defeito; FN: defeito não apontado);
* taxa de falso positivo em código correto — execuções de casos sem defeito que apontaram algum defeito;
* tempo de resposta — média, desvio-padrão, mediana, p95 e IC 95% (t de Student) por execução;
* cobertura de linhas média dos testes gerados;
* escore de mutação — mutantes mortos / total.
"""
from __future__ import annotations

import logging
import math
import os
import shutil
import socket
import statistics
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..agente import AgenteDeTestes, Configuracao
from ..contratos import ArquivoFonte, EntradaAgente
from ..llm.cliente import ModeloLinguagem, SemModelo, criar_modelo_a_partir_do_ambiente
from ..adaptadores.frameworks import obter_adaptador
from ..execucao.executores import escolher_executor
from ..modelos.dominio import CasoDeTeste, Relatorio, Requisito, StatusResultado
from .casos import CASOS, CORPUS, EXEMPLOS, CasoAvaliacao, Contexto, chaves_sinalizadas
from .mutacao import gerar_mutantes

log = logging.getLogger("agente_testes.avaliacao")

# Critérios de aceitação. A Entrega 1 não fixou valores numéricos; estes foram definidos no início da
# Entrega 2, antes das medições, e são justificados no relatório (ver entrega2/).
METAS = {
    "taxa_acerto": 90.0,          # % de casos com resultado obtido = esperado
    "precisao": 80.0,             # % dos achados de defeito que são defeitos reais
    "revocacao": 90.0,            # % dos defeitos reais que foram apontados
    "falso_positivo_correto": 0.0,  # % de execuções em código correto com algum falso defeito
    "tempo_medio_s": 60.0,        # orçamento por execução no CI (gatilho por PR)
    "cobertura_media": 70.0,      # mesmo limiar do portão no workflow (AGENTE_COBERTURA_MINIMA)
    "escore_mutacao": 60.0,       # % de mutantes mortos
}

# t de Student bicaudal 95% para gl = 1..30 (acima disso, 1,96)
_T95 = [12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262, 2.228, 2.201, 2.179, 2.160, 2.145,
        2.131, 2.120, 2.110, 2.101, 2.093, 2.086, 2.080, 2.074, 2.069, 2.064, 2.060, 2.056, 2.052, 2.048,
        2.045, 2.042]

FILTROS = ["0-normalizacao", "1-analise-contexto", "2-geracao-cenarios", "3-selecao-estrategia",
           "4-geracao-codigo", "5-execucao", "6-analise-resultados"]


@dataclass
class Execucao:
    caso: str
    tipo: str
    repeticao: int
    tempo_s: float
    ok: bool
    obtido: str
    testes: int = 0
    aprovados: int = 0
    reprovados: int = 0
    erros: int = 0
    cobertura: Optional[float] = None
    portao_aprovado: Optional[bool] = None
    sinalizadas: List[str] = field(default_factory=list)
    vp: int = 0
    fp: int = 0
    fn: int = 0
    iteracoes: int = 0
    tempo_por_filtro: Dict[str, float] = field(default_factory=dict)
    modelo: str = ""


@dataclass
class ResultadoMutante:
    """`morto`: a suíte gerada a partir do código correto falha no mutante (análise de mutação clássica).
    `morto_cego`: o agente, acionado diretamente sobre o código mutado, reprova o portão."""

    id: str
    operador: str
    linha: int
    descricao: str
    morto: bool
    motivo: str
    morto_cego: bool
    motivo_cego: str
    tempo_s: float


def estatisticas(xs: List[float]) -> Dict[str, float]:
    if not xs:
        return {}
    n = len(xs)
    media = statistics.fmean(xs)
    dp = statistics.stdev(xs) if n > 1 else 0.0
    t = _T95[n - 2] if 1 < n <= 31 else 1.96
    ordenado = sorted(xs)
    p95 = ordenado[min(n - 1, math.ceil(0.95 * n) - 1)]
    return {"n": n, "media": media, "desvio_padrao": dp, "mediana": statistics.median(xs), "p95": p95,
            "min": ordenado[0], "max": ordenado[-1], "ic95": t * dp / math.sqrt(n) if n > 1 else 0.0}


def _porta_livre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class ApiDeExemplo:
    """Sobe exemplos/loja/api_loja.py (uvicorn) para os testes de contrato."""

    def __init__(self) -> None:
        self.porta = _porta_livre()
        self.proc: Optional[subprocess.Popen] = None

    @property
    def url(self) -> str:
        return f"http://localhost:{self.porta}"

    def __enter__(self) -> "ApiDeExemplo":
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "exemplos.loja.api_loja:app", "--port", str(self.porta),
             "--host", "0.0.0.0", "--log-level", "warning"], cwd=EXEMPLOS.parent,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(50):
            try:
                with socket.create_connection(("127.0.0.1", self.porta), timeout=0.2):
                    return self
            except OSError:
                time.sleep(0.2)
        raise RuntimeError("API de exemplo não subiu")

    def __exit__(self, *exc) -> None:
        if self.proc:
            self.proc.terminate()
            self.proc.wait(timeout=10)


class Bancada:
    def __init__(self, modo: str = "heuristico", executor: str = "auto", repeticoes: int = 5,
                 timeout_teste_s: int = 3, saida: Path = Path("entrega2/resultados")):
        self.modo = modo
        self.executor = executor
        self.repeticoes = repeticoes
        self.timeout_teste_s = timeout_teste_s
        self.saida = saida

    def _llm(self, caso: Optional[CasoAvaliacao] = None) -> ModeloLinguagem:
        if caso and caso.llm_fixo:
            return caso.llm_fixo()
        if self.modo == "llm":
            llm = criar_modelo_a_partir_do_ambiente()
            if not llm.disponivel:
                raise RuntimeError("modo llm exige GEMINI_API_KEY ou LLM_BASE_URL configurados")
            return llm
        return SemModelo()

    def _config(self, dados: Path, workspace: Optional[Path] = None) -> Configuracao:
        return Configuracao(executor=self.executor, timeout_s=120, timeout_teste_s=self.timeout_teste_s,
                            cobertura_minima=0, max_iteracoes=3, dir_dados=dados, manter_workspace=workspace)

    def executar_caso(self, caso: CasoAvaliacao, rep: int, ctx: Contexto, dados: Path,
                      workspace: Optional[Path] = None) -> Tuple[Execucao, Optional[Relatorio]]:
        llm = self._llm(caso)
        relatorio, erro = None, None
        t0 = time.perf_counter()
        try:
            entrada = caso.montar(ctx)
            relatorio = AgenteDeTestes(llm, self._config(dados, workspace)).executar(entrada)
        except Exception as e:  # noqa: BLE001 — o próprio erro é o resultado observado do caso
            erro = e
        tempo = time.perf_counter() - t0
        v = caso.verificar(relatorio, erro)
        ex = Execucao(caso=caso.id, tipo=caso.tipo, repeticao=rep, tempo_s=round(tempo, 3), ok=v.ok,
                      obtido=v.obtido, modelo=llm.nome)
        if relatorio is not None:
            s = relatorio.resumo
            sin = chaves_sinalizadas(relatorio)
            ex.testes, ex.aprovados, ex.reprovados, ex.erros = s.total, s.aprovados, s.reprovados, s.erros
            ex.cobertura = relatorio.cobertura.percentual if relatorio.cobertura else None
            ex.portao_aprovado = relatorio.aprovado
            ex.sinalizadas = sorted(sin)
            ex.vp = len(sin & caso.defeitos_reais)
            ex.fp = len(sin - caso.defeitos_reais)
            ex.fn = len(caso.defeitos_reais - sin)
            ex.iteracoes = relatorio.iteracoes
            for etapa in relatorio.auditoria:
                ex.tempo_por_filtro[etapa.filtro] = round(ex.tempo_por_filtro.get(etapa.filtro, 0) + etapa.duracao_s, 3)
        else:
            ex.fn = len(caso.defeitos_reais)
        return ex, relatorio

    def _rodar_suite(self, codigo: str, casos: List[CasoDeTeste]) -> Tuple[bool, str]:
        """Executa a suíte já gerada contra um código, no mesmo executor isolado do Filtro 5."""
        adaptador = obter_adaptador("pytest")
        ws = Path(tempfile.mkdtemp(prefix="agente-mutante-"))
        try:
            (ws / "precos.py").write_text(codigo, encoding="utf-8")
            for c in casos:
                (ws / c.caminho).parent.mkdir(parents=True, exist_ok=True)
                (ws / c.caminho).write_text(c.codigo, encoding="utf-8")
            adaptador.preparar_workspace(ws)
            (ws / ".resultados").mkdir(exist_ok=True)
            executor = escolher_executor(self.executor, adaptador.imagem_docker)
            saida = executor.executar(ws, adaptador.comando([c.caminho for c in casos]), adaptador.imagem_docker,
                                      120, {"PYTEST_TIMEOUT": str(self.timeout_teste_s)}, False)
            resultados, _ = adaptador.ler_resultados(ws)
            falhos = [r for r in resultados if r.status in (StatusResultado.REPROVADO, StatusResultado.ERRO)]
            if not resultados and saida.codigo != 0:
                return True, "suíte não executou"
            return bool(falhos), (f"{len(falhos)}/{len(resultados)} testes falharam" if falhos else "")
        finally:
            shutil.rmtree(ws, ignore_errors=True)

    def executar_mutacao(self, dados: Path) -> List[ResultadoMutante]:
        codigo = (CORPUS / "precos.py").read_text(encoding="utf-8")
        reqs = [Requisito(id="RF-01", descricao="calcular_desconto aplica percentual entre 0 e 100",
                          criterios_aceite=["Percentual fora de [0, 100] é rejeitado", "Valor negativo é rejeitado"]),
                Requisito(id="RF-02", descricao="calcular_frete por peso e distância",
                          criterios_aceite=["Peso deve ser positivo", "Acima de 30 kg há acréscimo de 20%"])]

        def rodar(fonte: str) -> Relatorio:
            return AgenteDeTestes(self._llm(), self._config(dados)).executar(EntradaAgente(
                projeto="precos", requisitos=reqs, arquivos=[ArquivoFonte(caminho="precos.py", conteudo=fonte)]))

        base = rodar(codigo)
        if not base.aprovado:
            raise RuntimeError(f"código original de precos.py não passou no portão: {base.motivo_reprovacao}")
        suite = [c for c in base.casos if c.framework == "pytest"]
        out = []
        for m in gerar_mutantes(codigo):
            t0 = time.perf_counter()
            morto, motivo = self._rodar_suite(m.codigo, suite)
            r = rodar(m.codigo)
            motivo_cego = "; ".join(sorted({a.categoria for a in r.achados})) or "; ".join(r.motivo_reprovacao)
            out.append(ResultadoMutante(m.id, m.operador, m.linha, m.descricao, morto, motivo,
                                        not r.aprovado, motivo_cego if not r.aprovado else "",
                                        round(time.perf_counter() - t0, 3)))
            log.info("mutante %s %s: suíte %s, agente às cegas %s", m.id, m.descricao,
                     "matou" if morto else "não matou", "reprovou" if not r.aprovado else "aprovou")
        return out

    def rodar(self, com_mutacao: bool = True, progresso=print) -> Dict:
        self.saida.mkdir(parents=True, exist_ok=True)
        dados = Path(tempfile.mkdtemp(prefix="agente-avaliacao-"))
        execucoes: List[Execucao] = []
        evidencia: Optional[Relatorio] = None
        ws_evidencia = self.saida / "evidencias" / "workspace_depois"
        try:
            with ApiDeExemplo() as api:
                ctx = Contexto(api_base_url=api.url)
                for caso in CASOS:
                    for rep in range(1, self.repeticoes + 1):
                        guardar = caso.guardar_evidencia and rep == 1
                        if guardar:
                            shutil.rmtree(ws_evidencia, ignore_errors=True)
                        ex, rel = self.executar_caso(caso, rep, ctx, dados, ws_evidencia if guardar else None)
                        if guardar:
                            evidencia = rel
                        execucoes.append(ex)
                        progresso(f"{caso.id} rep {rep}/{self.repeticoes}: {'OK' if ex.ok else 'FALHOU'} "
                                  f"em {ex.tempo_s:.2f}s — {ex.obtido}")
            mutantes = self.executar_mutacao(dados) if com_mutacao else []
            if mutantes:
                progresso(f"mutação: suíte gerada matou {sum(m.morto for m in mutantes)}/{len(mutantes)}; agente "
                          f"às cegas reprovou {sum(m.morto_cego for m in mutantes)}/{len(mutantes)}")
        finally:
            shutil.rmtree(dados, ignore_errors=True)
        resultado = {
            "configuracao": {"modo": self.modo, "executor": self.executor, "repeticoes": self.repeticoes,
                             "timeout_teste_s": self.timeout_teste_s, "python": sys.version.split()[0],
                             "plataforma": sys.platform, "data": time.strftime("%Y-%m-%d %H:%M:%S"),
                             "modelo": sorted({e.modelo for e in execucoes})},
            "casos": [{"id": c.id, "tipo": c.tipo, "cenario": c.cenario, "esperado": c.esperado,
                       "defeitos_reais": sorted(c.defeitos_reais)} for c in CASOS],
            "execucoes": [asdict(e) for e in execucoes],
            "mutantes": [asdict(m) for m in mutantes],
            "metricas": calcular_metricas(execucoes, mutantes),
            "metas": METAS,
        }
        if evidencia is not None:
            resultado["evidencia_relatorio"] = evidencia.model_dump(mode="json")
        return resultado


def calcular_metricas(execucoes: List[Execucao], mutantes: List[ResultadoMutante]) -> Dict:
    por_caso: Dict[str, List[Execucao]] = {}
    for e in execucoes:
        por_caso.setdefault(e.caso, []).append(e)
    casos_ok = [c for c, es in por_caso.items() if all(e.ok for e in es)]
    vp, fp, fn = (sum(getattr(e, k) for e in execucoes) for k in ("vp", "fp", "fn"))
    precisao = 100 * vp / (vp + fp) if vp + fp else 0.0
    revocacao = 100 * vp / (vp + fn) if vp + fn else 0.0
    f1 = 2 * precisao * revocacao / (precisao + revocacao) if precisao + revocacao else 0.0
    # Execuções de código sem defeito plantado que de fato rodaram o pipeline.
    corretos = [e for e in execucoes if e.portao_aprovado is not None and e.vp + e.fn == 0]
    fp_corretos = [e for e in corretos if e.fp]
    coberturas = [e.cobertura for e in execucoes if e.cobertura is not None]
    filtros = {f: estatisticas([e.tempo_por_filtro.get(f, 0.0) for e in execucoes if e.tempo_por_filtro])
               for f in FILTROS}
    tempos_caso = {c: estatisticas([e.tempo_s for e in es]) for c, es in por_caso.items()}
    por_operador: Dict[str, Dict[str, int]] = {}
    for m in mutantes:
        d = por_operador.setdefault(m.operador, {"total": 0, "mortos": 0, "mortos_cego": 0})
        d["total"] += 1
        d["mortos"] += m.morto
        d["mortos_cego"] += m.morto_cego
    return {
        "total_casos": len(por_caso),
        "casos_tipicos": len({e.caso for e in execucoes if e.tipo == "típico"}),
        "casos_borda": len({e.caso for e in execucoes if e.tipo == "borda"}),
        "total_execucoes": len(execucoes),
        "casos_ok": sorted(casos_ok),
        "casos_falhos": sorted(set(por_caso) - set(casos_ok)),
        "taxa_acerto": 100 * len(casos_ok) / len(por_caso) if por_caso else 0.0,
        "taxa_acerto_execucoes": 100 * sum(e.ok for e in execucoes) / len(execucoes) if execucoes else 0.0,
        "deteccao": {"vp": vp, "fp": fp, "fn": fn, "precisao": precisao, "revocacao": revocacao, "f1": f1},
        "falso_positivo_correto": 100 * len(fp_corretos) / len(corretos) if corretos else 0.0,
        "execucoes_codigo_correto": len(corretos),
        "tempo_s": estatisticas([e.tempo_s for e in execucoes]),
        "tempo_por_caso": tempos_caso,
        "tempo_por_filtro": filtros,
        "cobertura": estatisticas(coberturas),
        "testes_gerados": estatisticas([float(e.testes) for e in execucoes if e.portao_aprovado is not None]),
        "mutacao": {
            "total": len(mutantes), "mortos": sum(m.morto for m in mutantes),
            "escore": 100 * sum(m.morto for m in mutantes) / len(mutantes) if mutantes else None,
            "mortos_cego": sum(m.morto_cego for m in mutantes),
            "deteccao_cega": 100 * sum(m.morto_cego for m in mutantes) / len(mutantes) if mutantes else None,
            "por_operador": por_operador,
        },
    }


def ambiente_executor(preferencia: str) -> str:
    from ..adaptadores.frameworks import AdaptadorPytest
    from ..execucao.executores import escolher_executor
    return escolher_executor(preferencia, AdaptadorPytest.imagem_docker).nome


def configurar_log(verboso: bool) -> None:
    logging.basicConfig(level=logging.INFO if verboso else logging.WARNING,
                        format="%(levelname)s %(name)s: %(message)s")
    os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
