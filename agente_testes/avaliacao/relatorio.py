"""Grava os artefatos da avaliação: dados brutos, tabelas no formato do Modelo_Entrega2 e evidências."""
from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path
from typing import Dict, List

from ..modelos.dominio import Relatorio
from ..visoes.markdown import renderizar_markdown
from .casos import EXEMPLOS


def br(x: float, casas: int = 1) -> str:
    return f"{x:,.{casas}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def _tabela_casos(res: Dict) -> List[str]:
    n = res["configuracao"]["repeticoes"]
    linhas = ["| Nº | Cenário testado | Resultado esperado | Resultado obtido |", "|---|---|---|---|"]
    for i, c in enumerate(res["casos"], 1):
        execs = [e for e in res["execucoes"] if e["caso"] == c["id"]]
        acertos = sum(e["ok"] for e in execs)
        selo = (f"✔ conforme o esperado ({acertos}/{n} repetições)" if acertos == len(execs)
                else f"✘ divergiu do esperado em {len(execs) - acertos}/{n} repetições")
        linhas.append(f"| {i} ({c['id']}) | [{c['tipo']}] {c['cenario']} | {c['esperado']} | "
                      f"{execs[0]['obtido']}. {selo} |")
    return linhas


def _tabela_metricas(res: Dict) -> List[str]:
    m, metas = res["metricas"], res["metas"]
    t, d, cob, mut = m["tempo_s"], m["deteccao"], m["cobertura"], m["mutacao"]
    tg = m["testes_gerados"]

    def st(valor: float, meta: float, maior_melhor: bool = True) -> str:
        return "atingida" if (valor >= meta if maior_melhor else valor <= meta) else "não atingida"

    linhas = ["| Métrica | Valor obtido | Meta/critério de aceitação |", "|---|---|---|",
              f"| Taxa de acerto (casos com resultado obtido = esperado) | {br(m['taxa_acerto'])}% "
              f"({len(m['casos_ok'])}/{m['total_casos']} casos; {m['total_execucoes']} execuções) | "
              f"≥ {br(metas['taxa_acerto'], 0)}% — {st(m['taxa_acerto'], metas['taxa_acerto'])} |",
              f"| Precisão na detecção de defeitos | {br(d['precisao'])}% (VP={d['vp']}, FP={d['fp']}) | "
              f"≥ {br(metas['precisao'], 0)}% — {st(d['precisao'], metas['precisao'])} |",
              f"| Tempo médio de resposta (por execução do pipeline) | {br(t['media'], 2)} s ± {br(t['desvio_padrao'], 2)} s "
              f"(IC 95%: ± {br(t['ic95'], 2)} s; mediana {br(t['mediana'], 2)} s; p95 {br(t['p95'], 2)} s) | "
              f"≤ {br(metas['tempo_medio_s'], 0)} s — {st(t['media'], metas['tempo_medio_s'], False)} |",
              f"| Revocação (sensibilidade) na detecção de defeitos | {br(d['revocacao'])}% (VP={d['vp']}, FN={d['fn']}) | "
              f"≥ {br(metas['revocacao'], 0)}% — {st(d['revocacao'], metas['revocacao'])} |",
              f"| F1 (média harmônica de precisão e revocação) | {br(d['f1'])}% | — (derivada) |",
              f"| Falso positivo em código correto | {br(m['falso_positivo_correto'])}% das "
              f"{m['execucoes_codigo_correto']} execuções sem defeito plantado | = 0% — "
              f"{st(m['falso_positivo_correto'], metas['falso_positivo_correto'], False)} |",
              f"| Cobertura de linhas dos testes gerados | {br(cob.get('media', 0))}% em média "
              f"(mín. {br(cob.get('min', 0))}%, máx. {br(cob.get('max', 0))}%) | ≥ {br(metas['cobertura_media'], 0)}% "
              f"— {st(cob.get('media', 0), metas['cobertura_media'])} |",
              f"| Testes gerados e executados por execução | {br(tg.get('media', 0))} em média "
              f"(mín. {tg.get('min', 0):.0f}, máx. {tg.get('max', 0):.0f}) | — (descritiva) |"]
    if mut["escore"] is not None:
        linhas.append(f"| Escore de mutação (defeitos injetados detectados) | {br(mut['escore'])}% "
                      f"({mut['mortos']}/{mut['total']} mutantes) | ≥ {br(metas['escore_mutacao'], 0)}% — "
                      f"{st(mut['escore'], metas['escore_mutacao'])} |")
        linhas.append(f"| Detecção às cegas (agente acionado sobre o código já mutado) | "
                      f"{br(mut['deteccao_cega'])}% ({mut['mortos_cego']}/{mut['total']} mutantes reprovados) | "
                      f"— (diagnóstico do oráculo, sem meta prévia) |")
    return linhas


def _tabela_mutantes(res: Dict) -> List[str]:
    linhas = ["| Mutante | Operador | Linha | Alteração | Suíte gerada do código correto | Agente às cegas |",
              "|---|---|---|---|---|---|"]
    for x in res["mutantes"]:
        linhas.append(f"| {x['id']} | {x['operador']} | {x['linha']} | `{x['descricao']}` | "
                      f"{'morto (' + x['motivo'] + ')' if x['morto'] else '**sobreviveu**'} | "
                      f"{'reprovou (' + x['motivo_cego'] + ')' if x['morto_cego'] else '**aprovou**'} |")
    return linhas


def gravar(res: Dict, saida: Path, graficos: List[Path]) -> Dict[str, Path]:
    saida.mkdir(parents=True, exist_ok=True)
    arquivos: Dict[str, Path] = {}
    arquivos["json"] = saida / "resultados.json"
    arquivos["json"].write_text(json.dumps(res, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    arquivos["csv"] = saida / "execucoes.csv"
    with arquivos["csv"].open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["caso", "tipo", "repeticao", "tempo_s", "ok", "testes", "aprovados", "reprovados", "erros",
                    "cobertura", "portao_aprovado", "vp", "fp", "fn", "sinalizadas", "obtido"])
        for e in res["execucoes"]:
            w.writerow([e["caso"], e["tipo"], e["repeticao"], e["tempo_s"], e["ok"], e["testes"], e["aprovados"],
                        e["reprovados"], e["erros"], e["cobertura"], e["portao_aprovado"], e["vp"], e["fp"],
                        e["fn"], ";".join(e["sinalizadas"]), e["obtido"]])
    if res["mutantes"]:
        arquivos["mutantes"] = saida / "mutantes.csv"
        with arquivos["mutantes"].open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            campos = ["id", "operador", "linha", "descricao", "morto", "motivo", "morto_cego", "motivo_cego", "tempo_s"]
            w.writerow(campos)
            for x in res["mutantes"]:
                w.writerow([x[c] for c in campos])

    m, cfg = res["metricas"], res["configuracao"]
    md = [f"# Resultados da avaliação — Agente de Testes de Software", "",
          f"Gerado por `agente-testes avaliar` em {cfg['data']} · modo `{cfg['modo']}` · executor `{cfg['executor']}` · "
          f"{cfg['repeticoes']} repetições por caso · limite por teste {cfg['timeout_teste_s']} s · "
          f"Python {cfg['python']} · modelo(s): {', '.join(cfg['modelo'])}.", "",
          f"## Casos de teste executados ({m['total_casos']}: {m['casos_tipicos']} típicos, {m['casos_borda']} de borda)",
          "", *_tabela_casos(res), "",
          "## Métricas e estatísticas coletadas", "", *_tabela_metricas(res), "",
          "## Linha para a Consolidação Estatística Geral (seção 4 do modelo)", "",
          "| Agente | Nº de testes | Taxa de sucesso | Tempo médio (s) |", "|---|---|---|---|",
          f"| Agente de Testes de Software | {m['total_casos']} casos ({m['total_execucoes']} execuções) | "
          f"{br(m['taxa_acerto'])}% | {br(m['tempo_s']['media'], 2)} |", ""]
    if res["mutantes"]:
        md += ["## Detalhe do teste de mutação (`corpus/precos.py`)", "", *_tabela_mutantes(res), ""]
    md += ["## Gráficos", ""] + [f"![{g.stem}](graficos/{g.name})" for g in graficos] + [""]
    arquivos["md"] = saida / "RESULTADOS.md"
    arquivos["md"].write_text("\n".join(md), encoding="utf-8")

    # Evidência antes/depois (caso C02)
    if res.get("evidencia_relatorio"):
        ev = saida / "evidencias"
        (ev / "antes").mkdir(parents=True, exist_ok=True)
        shutil.copy(EXEMPLOS / "loja" / "loja.py", ev / "antes" / "loja.py")
        shutil.copy(EXEMPLOS / "loja" / "requisitos.yaml", ev / "antes" / "requisitos.yaml")
        (ev / "antes" / "LEIA-ME.md").write_text(
            "# Estado antes da atuação do agente\n\n"
            "`loja.py` e `requisitos.yaml` exatamente como entregues ao agente: **nenhum teste automatizado**, "
            "cobertura de 0% e nenhum defeito conhecido. Os defeitos plantados (`ticket_medio([])` e "
            "`aplicar_cupom(total=None)`) só aparecem quando o código é exercitado.\n", encoding="utf-8")
        rel = Relatorio.model_validate(res["evidencia_relatorio"])
        (ev / "depois_relatorio.md").write_text(renderizar_markdown(rel, incluir_codigo=True), encoding="utf-8")
        ws = ev / "workspace_depois"
        if ws.exists():  # remove o que não é evidência (cópias do código e caches)
            for lixo in [ws / "loja.py", ws / ".coveragerc", ws / ".pytest_cache"]:
                shutil.rmtree(lixo, ignore_errors=True) if lixo.is_dir() else lixo.unlink(missing_ok=True)
        arquivos["evidencias"] = ev
    return arquivos
