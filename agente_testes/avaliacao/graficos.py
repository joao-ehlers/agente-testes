"""Gráficos da Entrega 2 (PNG, para inserir no documento .pdf).

Requer matplotlib (`pip install -e .[avaliacao]`). Paleta: azul e laranja da paleta
categórica de referência; metas em cinza escuro; textos em tinta neutra.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

AZUL, LARANJA = "#2a78d6", "#eb6834"
TINTA, TINTA_2, GRADE, META = "#0b0b0b", "#52514e", "#e6e5e0", "#3d3c39"
FUNDO = "#ffffff"


def _br(x: float, casas: int = 1) -> str:
    return f"{x:.{casas}f}".replace(".", ",")
NOMES_FILTRO = {"0-normalizacao": "F0 Normalização", "1-analise-contexto": "F1 Análise de contexto",
                "2-geracao-cenarios": "F2 Geração de cenários", "3-selecao-estrategia": "F3 Seleção da estratégia",
                "4-geracao-codigo": "F4 Geração de código", "5-execucao": "F5 Execução isolada",
                "6-analise-resultados": "F6 Análise de resultados"}


def _estilo() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": GRADE, "axes.labelcolor": TINTA_2,
        "xtick.color": TINTA_2, "ytick.color": TINTA, "axes.titlesize": 12, "axes.titleweight": "bold",
        "axes.titlecolor": TINTA, "axes.titlelocation": "left", "figure.facecolor": FUNDO,
        "axes.facecolor": FUNDO, "savefig.dpi": 200, "savefig.bbox": "tight"})


def _limpar(ax, eixo_grade: str = "x") -> None:
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.grid(axis=eixo_grade, color=GRADE, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def tempo_por_caso(res: Dict, destino: Path) -> Path:
    casos = res["casos"]
    est = res["metricas"]["tempo_por_caso"]
    rotulos = [f"{c['id']}  {c['cenario'][:46]}{'…' if len(c['cenario']) > 46 else ''}" for c in casos][::-1]
    medias = [est[c["id"]]["media"] for c in casos][::-1]
    dps = [est[c["id"]]["desvio_padrao"] for c in casos][::-1]
    cores = [AZUL if c["tipo"] == "típico" else LARANJA for c in casos][::-1]
    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.barh(rotulos, medias, xerr=dps, color=cores, height=0.6,
            error_kw={"ecolor": TINTA_2, "elinewidth": 1, "capsize": 3})
    for y, (m, d) in enumerate(zip(medias, dps)):
        ax.text(m + d + max(medias) * 0.01, y, f"{_br(m, 2)} s", va="center", fontsize=8.5, color=TINTA)
    ax.set_xlabel("Tempo de resposta por execução (s) — média ± desvio-padrão")
    ax.set_title(f"Tempo de resposta por caso ({res['configuracao']['repeticoes']} repetições cada)")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=AZUL, label="Cenário típico"), Patch(color=LARANJA, label="Cenário de borda")],
              loc="lower right", frameon=False)
    _limpar(ax)
    return _salvar(fig, destino / "g1_tempo_por_caso.png")


def metricas_vs_metas(res: Dict, destino: Path) -> Path:
    m, metas = res["metricas"], res["metas"]
    itens = [("Taxa de acerto dos casos", m["taxa_acerto"], metas["taxa_acerto"]),
             ("Precisão na detecção de defeitos", m["deteccao"]["precisao"], metas["precisao"]),
             ("Revocação na detecção de defeitos", m["deteccao"]["revocacao"], metas["revocacao"]),
             ("Cobertura de linhas média", m["cobertura"].get("media", 0), metas["cobertura_media"])]
    if m["mutacao"]["escore"] is not None:
        itens.append(("Escore de mutação", m["mutacao"]["escore"], metas["escore_mutacao"]))
    itens = itens[::-1]
    fig, ax = plt.subplots(figsize=(8.5, 3.8))
    ys = range(len(itens))
    ax.barh([i[0] for i in itens], [i[1] for i in itens], color=AZUL, height=0.55)
    for y, (_, valor, meta) in zip(ys, itens):
        ax.plot([meta, meta], [y - 0.38, y + 0.38], color=META, linewidth=2)
        ax.text(max(min(valor, 100), meta) + 1.5, y, f"{_br(valor)}%", va="center", fontsize=9, color=TINTA)
    ax.plot([], [], color=META, linewidth=2, label="Meta (critério de aceitação)")
    ax.set_xlim(0, 112)
    ax.set_xlabel("%")
    ax.set_title("Métricas obtidas × metas")
    ax.legend(loc="lower right", frameon=False, bbox_to_anchor=(1, -0.32))
    _limpar(ax)
    return _salvar(fig, destino / "g2_metricas_vs_metas.png")


def tempo_por_filtro(res: Dict, destino: Path) -> Path:
    est = res["metricas"]["tempo_por_filtro"]
    itens = [(NOMES_FILTRO[f], e.get("media", 0.0)) for f, e in est.items()][::-1]
    total = sum(v for _, v in itens) or 1
    fig, ax = plt.subplots(figsize=(8.5, 3.6))
    ax.barh([i[0] for i in itens], [i[1] for i in itens], color=AZUL, height=0.55)
    for y, (_, v) in enumerate(itens):
        ax.text(v + total * 0.01, y, f"{_br(v, 3)} s ({100 * v / total:.0f}%)", va="center", fontsize=8.5, color=TINTA)
    ax.set_xlabel("Tempo médio por execução (s)")
    ax.set_title("Onde o tempo é gasto: filtros do pipeline (Pipe-and-Filter)")
    ax.set_xlim(0, max(v for _, v in itens) * 1.3 or 1)
    _limpar(ax)
    return _salvar(fig, destino / "g3_tempo_por_filtro.png")


def mutacao(res: Dict, destino: Path) -> Path:
    from .mutacao import NOMES
    por_op = res["metricas"]["mutacao"]["por_operador"]
    ops = [o for o in ("RVR", "ROR", "CRP", "AOR") if o in por_op][::-1]
    rotulos = [f"{NOMES[o]}  (n={por_op[o]['total']})" for o in ops]
    suite = [100 * por_op[o]["mortos"] / por_op[o]["total"] for o in ops]
    cego = [100 * por_op[o]["mortos_cego"] / por_op[o]["total"] for o in ops]
    fig, ax = plt.subplots(figsize=(8.5, 4))
    ys = list(range(len(ops)))
    h = 0.36
    ax.barh([y + h / 2 for y in ys], suite, height=h, color=AZUL, edgecolor=FUNDO, linewidth=2,
            label="Suíte gerada do código correto, rodada no mutante")
    ax.barh([y - h / 2 for y in ys], cego, height=h, color=LARANJA, edgecolor=FUNDO, linewidth=2,
            label="Agente acionado diretamente sobre o código mutado")
    for y, (a, b) in enumerate(zip(suite, cego)):
        ax.text(a + 1, y + h / 2, f"{a:.0f}%", va="center", fontsize=8.5, color=TINTA)
        ax.text(b + 1, y - h / 2, f"{b:.0f}%", va="center", fontsize=8.5, color=TINTA)
    ax.set_yticks(ys)
    ax.set_yticklabels(rotulos)
    m = res["metricas"]["mutacao"]
    ax.axvline(res["metas"]["escore_mutacao"], color=META, linewidth=1.5, linestyle="--",
               label=f"Meta do escore de mutação ({res['metas']['escore_mutacao']:.0f}%)")
    ax.set_title(f"Teste de mutação ({m['total']} mutantes)\nescore {_br(m['escore'])}% · "
                 f"detecção às cegas {_br(m['deteccao_cega'])}%")
    ax.set_xlabel("% de mutantes detectados")
    ax.set_xlim(0, 112)
    ax.legend(loc="upper center", frameon=False, bbox_to_anchor=(0.45, -0.18), ncol=1)
    _limpar(ax)
    return _salvar(fig, destino / "g4_mutacao.png")


def antes_depois(res: Dict, destino: Path) -> Path:
    rel = res.get("evidencia_relatorio")
    if not rel:
        return Path()
    depois = {"Testes automatizados": rel["resumo"]["total"],
              "Cobertura de linhas (%)": (rel.get("cobertura") or {}).get("percentual", 0),
              "Unidades com defeito apontado": len({a.get("alvo") for a in rel["achados"]
                                                    if a["categoria"] in ("defeito_suspeito", "validacao_ausente")})}
    fig, axes = plt.subplots(1, 3, figsize=(9, 3))
    for ax, (nome, valor) in zip(axes, depois.items()):
        ax.bar(["Antes", "Depois"], [0, valor], color=[TINTA_2, AZUL], width=0.55)
        ax.text(0, 0, "0", ha="center", va="bottom", fontsize=10, color=TINTA)
        ax.text(1, valor, f"{valor:.0f}", ha="center", va="bottom", fontsize=10, color=TINTA)
        ax.set_title(nome, fontsize=10, loc="center")
        ax.set_ylim(0, valor * 1.2 or 1)
        ax.set_yticks([])
        _limpar(ax, "y")
        ax.spines["bottom"].set_color(GRADE)
    fig.suptitle("Módulo loja.py antes e depois da atuação do agente (caso C02)", x=0.01, ha="left",
                 fontweight="bold", color=TINTA)
    fig.tight_layout()
    return _salvar(fig, destino / "g5_antes_depois.png")


def _salvar(fig, caminho: Path) -> Path:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(caminho)
    plt.close(fig)
    return caminho


def gerar_todos(res: Dict, destino: Path) -> List[Path]:
    _estilo()
    feitos = [tempo_por_caso(res, destino), metricas_vs_metas(res, destino), tempo_por_filtro(res, destino),
              antes_depois(res, destino)]
    if res["mutantes"]:
        feitos.append(mutacao(res, destino))
    return [f for f in feitos if f.name]
