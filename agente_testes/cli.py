"""Linha de comando: operação independente e acionamento pelo CI/CD.

Exemplos:
  agente-testes executar exemplos/loja/loja.py --requisitos exemplos/loja/requisitos.yaml
  agente-testes executar --diff-base origin/main --raiz . --saida-md relatorio.md
  agente-testes analisar src/app.py
  agente-testes servir --porta 8000
"""
from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

import yaml

from .agente import Configuracao
from .contratos import ArquivoFonte, EntradaAgente
from .controlador import ControladorAgente
from .modelos.dominio import Requisito, TipoTeste
from .pipeline.filtros.f0_normalizacao import detectar_linguagem
from .visoes.markdown import renderizar_markdown

_IGNORAR = {".git", ".venv", "venv", "node_modules", "__pycache__", "build", "dist", "target", ".agente_dados"}


def _eh_teste(caminho: str) -> bool:
    nome = caminho.rsplit("/", 1)[-1]
    return (nome.startswith("test_") or nome.endswith("_test.py") or ".test." in nome or ".spec." in nome
            or nome.endswith("Test.java") or "/tests/" in f"/{caminho}" or "/test/" in f"/{caminho}")


def _coletar(caminhos: List[str], raiz: Path) -> List[Path]:
    out = []
    for c in caminhos:
        p = Path(c)
        if p.is_dir():
            out += [x for x in sorted(p.rglob("*")) if x.is_file()
                    and not (set(x.relative_to(p).parts) & _IGNORAR)]
        elif p.is_file():
            out.append(p)
    return [p for p in out if detectar_linguagem(p.name).value != "desconhecida"]


def _rel(p: Path, raiz: Path) -> str:
    try:
        return str(p.resolve().relative_to(raiz.resolve()))
    except ValueError:
        return p.name


def montar_entrada(args) -> EntradaAgente:
    raiz = Path(args.raiz)
    diff = None
    caminhos = list(args.caminhos)
    if args.diff_base:
        diff = subprocess.run(["git", "diff", "--unified=0", f"{args.diff_base}...HEAD"], cwd=raiz,
                              capture_output=True, text=True, check=True).stdout
        alterados = subprocess.run(["git", "diff", "--name-only", "--diff-filter=AM", f"{args.diff_base}...HEAD"],
                                   cwd=raiz, capture_output=True, text=True, check=True).stdout.split()
        caminhos += [str(raiz / a) for a in alterados]
    arquivos = _coletar(caminhos, raiz)
    fontes = [p for p in arquivos if not _eh_teste(_rel(p, raiz))]
    testes = [p for p in arquivos if _eh_teste(_rel(p, raiz))]
    for t in args.testes_existentes or []:
        testes += _coletar([t], raiz)
    # Para projetos Python, inclui módulos irmãos para que os imports funcionem no workspace isolado.
    contexto_extra = []
    if args.incluir_projeto:
        contexto_extra = [p for p in _coletar([str(raiz)], raiz) if not _eh_teste(_rel(p, raiz)) and p not in fontes]

    requisitos = []
    if args.requisitos:
        dados = yaml.safe_load(Path(args.requisitos).read_text(encoding="utf-8"))
        requisitos = [Requisito.model_validate(r) for r in (dados.get("requisitos", dados) if isinstance(dados, dict) else dados)]
    relatorios = [json.loads(Path(r).read_text(encoding="utf-8")) for r in (args.relatorio_anterior or [])]
    return EntradaAgente(
        projeto=args.projeto or raiz.resolve().name,
        arquivos=[ArquivoFonte(caminho=_rel(p, raiz), conteudo=p.read_text(encoding="utf-8"))
                  for p in fontes + contexto_extra],
        diff=diff or None,
        requisitos=requisitos,
        descricao_funcionalidade=args.descricao,
        contrato_openapi=Path(args.openapi).read_text(encoding="utf-8") if args.openapi else None,
        testes_existentes=[ArquivoFonte(caminho=_rel(p, raiz), conteudo=p.read_text(encoding="utf-8")) for p in testes],
        relatorios_anteriores=relatorios,
        framework=args.framework,
        tipos_teste=[TipoTeste(t) for t in args.tipos] if args.tipos else None,
        api_base_url=args.api_base_url,
    )


def _args_entrada(p: argparse.ArgumentParser) -> None:
    p.add_argument("caminhos", nargs="*", help="arquivos ou diretórios de código-fonte")
    p.add_argument("--raiz", default=".", help="raiz do projeto (caminhos relativos e git diff)")
    p.add_argument("--projeto", help="nome do projeto")
    p.add_argument("--diff-base", help="ref git base; analisa apenas o que mudou (ex.: origin/main)")
    p.add_argument("--incluir-projeto", action="store_true", help="copia o restante do projeto para o workspace")
    p.add_argument("--requisitos", help="YAML/JSON com lista de requisitos {id, descricao, criterios_aceite}")
    p.add_argument("--descricao", help="descrição da funcionalidade")
    p.add_argument("--openapi", help="contrato OpenAPI (YAML/JSON)")
    p.add_argument("--api-base-url", help="URL da API para os testes de contrato")
    p.add_argument("--testes-existentes", nargs="*", help="arquivos/diretórios da suíte existente")
    p.add_argument("--relatorio-anterior", nargs="*", help="relatórios JSON de execuções anteriores")
    p.add_argument("--framework", choices=["pytest", "junit", "jest", "vitest", "newman"])
    p.add_argument("--tipos", nargs="*", choices=[t.value for t in TipoTeste], help="força estratégias")


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="agente-testes", description="Agente Inteligente de Testes de Software")
    ap.add_argument("-v", "--verboso", action="store_true")
    sub = ap.add_subparsers(dest="comando", required=True)

    pa = sub.add_parser("analisar", help="analisa contexto e deriva cenários (filtros 0-2)")
    _args_entrada(pa)
    pg = sub.add_parser("gerar", help="gera código de teste sem executar (filtros 0-4)")
    _args_entrada(pg)
    pg.add_argument("--destino", help="grava os testes gerados neste diretório")
    pe = sub.add_parser("executar", help="pipeline completo (filtros 0-6)")
    _args_entrada(pe)
    pe.add_argument("--saida-json", help="grava o relatório JSON")
    pe.add_argument("--saida-md", help="grava o relatório Markdown")
    pe.add_argument("--com-codigo", action="store_true", help="inclui o código dos testes no Markdown")
    pe.add_argument("--cobertura-minima", type=float, help="percentual mínimo para aprovar")
    pe.add_argument("--executor", choices=["auto", "docker", "local"])
    pe.add_argument("--manter-workspace", help="copia o workspace de execução para este diretório")
    pe.add_argument("--nao-falhar", action="store_true", help="código de saída 0 mesmo se reprovado")
    pv = sub.add_parser("avaliar", help="bancada da Entrega 2: casos controlados, métricas, gráficos e evidências")
    pv.add_argument("--modo", choices=["heuristico", "llm"], default="heuristico",
                    help="llm usa o modelo configurado (GEMINI_API_KEY ou LLM_BASE_URL)")
    pv.add_argument("--executor", choices=["auto", "docker", "local"], default="auto")
    pv.add_argument("--repeticoes", type=int, default=5, help="execuções por caso (estatística de tempo)")
    pv.add_argument("--timeout-teste", type=int, default=3, help="limite por teste, em segundos")
    pv.add_argument("--sem-mutacao", action="store_true", help="pula o teste de mutação")
    pv.add_argument("--saida", default="entrega2/resultados", help="diretório dos resultados")
    ps = sub.add_parser("servir", help="sobe a API REST")
    ps.add_argument("--host", default="0.0.0.0")
    ps.add_argument("--porta", type=int, default=8000)

    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verboso else logging.WARNING,
                        format="%(levelname)s %(name)s: %(message)s")

    if args.comando == "servir":
        import uvicorn
        uvicorn.run("agente_testes.api.app:app", host=args.host, port=args.porta)
        return 0

    if args.comando == "avaliar":
        return _avaliar(args)

    config = Configuracao()
    if getattr(args, "cobertura_minima", None) is not None:
        config.cobertura_minima = args.cobertura_minima
    if getattr(args, "executor", None):
        config.executor = args.executor
    if getattr(args, "manter_workspace", None):
        config.manter_workspace = Path(args.manter_workspace)
    ctrl = ControladorAgente(config=config)
    try:
        entrada = montar_entrada(args)
    except ValueError as e:
        print(f"erro na entrada: {e}", file=sys.stderr)
        return 2

    if args.comando == "analisar":
        print(ctrl.analisar(entrada).model_dump_json(indent=2))
        return 0
    if args.comando == "gerar":
        resp = ctrl.gerar_testes(entrada)
        if args.destino:
            for c in resp.dados["casos"]:
                destino = Path(args.destino) / c["caminho"]
                destino.parent.mkdir(parents=True, exist_ok=True)
                destino.write_text(c["codigo"], encoding="utf-8")
                print(f"gravado: {destino}")
        else:
            print(resp.model_dump_json(indent=2))
        return 0

    relatorio = ctrl.executar(entrada)
    md = renderizar_markdown(relatorio, incluir_codigo=args.com_codigo)
    if args.saida_json:
        Path(args.saida_json).write_text(relatorio.model_dump_json(indent=2), encoding="utf-8")
    if args.saida_md:
        Path(args.saida_md).write_text(md, encoding="utf-8")
    print(md)
    return 0 if relatorio.aprovado or args.nao_falhar else 1


def _avaliar(args) -> int:
    from .avaliacao.executar import Bancada, ambiente_executor
    try:
        from .avaliacao import graficos
    except ImportError:
        print("a avaliação precisa do matplotlib: pip install -e '.[avaliacao]'", file=sys.stderr)
        return 2
    from .avaliacao.relatorio import gravar

    logging.getLogger("agente_testes.llm").setLevel(logging.ERROR)  # rejeições do LLM simulado são esperadas
    executor = ambiente_executor(args.executor)
    print(f"executor efetivo: {executor}" + ("  (ATENÇÃO: sem isolamento Docker)" if executor == "local" else ""))
    saida = Path(args.saida)
    bancada = Bancada(modo=args.modo, executor=executor, repeticoes=args.repeticoes,
                      timeout_teste_s=args.timeout_teste, saida=saida)
    res = bancada.rodar(com_mutacao=not args.sem_mutacao)
    figuras = graficos.gerar_todos(res, saida / "graficos")
    arquivos = gravar(res, saida, figuras)
    m = res["metricas"]
    print(f"\ntaxa de acerto {m['taxa_acerto']:.1f}% | precisão {m['deteccao']['precisao']:.1f}% | "
          f"revocação {m['deteccao']['revocacao']:.1f}% | tempo médio {m['tempo_s']['media']:.2f}s"
          + (f" | mutação {m['mutacao']['escore']:.1f}%" if m["mutacao"]["escore"] is not None else ""))
    print(f"resultados: {arquivos['md']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
