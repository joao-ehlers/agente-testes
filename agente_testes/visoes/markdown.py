"""View (MVC): apresentação do relatório em Markdown (CLI e resumo do GitHub Actions).

Na API REST, a View é o próprio JSON consumido pelos clientes.
"""
from __future__ import annotations

from ..modelos.dominio import Relatorio, StatusResultado, TipoCenario

_ICONE = {StatusResultado.APROVADO: "✅", StatusResultado.REPROVADO: "❌",
          StatusResultado.ERRO: "💥", StatusResultado.IGNORADO: "⏭️"}


def renderizar_markdown(r: Relatorio, incluir_codigo: bool = False) -> str:
    s = r.resumo
    cob = f"{r.cobertura.percentual:.1f}%" if r.cobertura else "n/d"
    status = "✅ APROVADO" if r.aprovado else "❌ REPROVADO"
    out = [
        f"# Relatório do Agente de Testes — {r.projeto.nome}",
        "",
        f"**Portão de qualidade:** {status}" + (f" — {'; '.join(r.motivo_reprovacao)}" if r.motivo_reprovacao else ""),
        "",
        f"| Total | Aprovados | Reprovados | Erros | Ignorados | Cobertura |",
        f"|---|---|---|---|---|---|",
        f"| {s.total} | {s.aprovados} | {s.reprovados} | {s.erros} | {s.ignorados} | {cob} |",
        "",
        f"Relatório `{r.id}` · linguagem `{r.projeto.linguagem.value}` · framework `{r.projeto.framework}` · "
        f"executor `{r.execucao.executor if r.execucao else 'n/d'}` · modelo `{r.modelo_linguagem}` · "
        f"iterações {r.iteracoes}",
    ]
    if r.achados:
        out += ["", "## Achados", "", "| Categoria | Teste | Explicação |", "|---|---|---|"]
        for a in r.achados:
            out.append(f"| {a.categoria} | `{a.teste.split('::')[-1]}` | {a.explicacao.replace('|', '/')} |")

    cont = {t: sum(1 for c in r.cenarios if c.tipo == t) for t in TipoCenario}
    out += ["", f"## Cenários ({len(r.cenarios)}: {cont[TipoCenario.SUCESSO]} sucesso, "
                f"{cont[TipoCenario.FALHA]} falha, {cont[TipoCenario.BORDA]} borda)", ""]
    status_por_cen = {}
    for x in (r.execucao.resultados if r.execucao else []):
        if x.cenario_id:
            status_por_cen[x.cenario_id] = x.status
    for c in r.cenarios:
        icone = _ICONE.get(status_por_cen.get(c.id), "➖")
        req = f" [{c.requisito_id}]" if c.requisito_id else ""
        out.append(f"- {icone} **{c.tipo.value}** `{c.alvo}`{req}: {c.descricao}")

    if r.trechos_nao_cobertos:
        out += ["", "## Trechos não cobertos", ""] + [f"- `{t}`" for t in r.trechos_nao_cobertos]
    if r.riscos:
        out += ["", "## Riscos", ""] + [
            f"- **{x.severidade.value}** {('`' + x.alvo + '`: ') if x.alvo else ''}{x.descricao}" for x in r.riscos]
    if incluir_codigo and r.casos:
        out += ["", "## Testes gerados"]
        for c in r.casos:
            lang = "json" if c.caminho.endswith(".json") else c.caminho.rsplit(".", 1)[-1]
            out += ["", f"### `{c.caminho}` ({c.tipo_teste.value}, {c.origem.value})", "",
                    f"```{lang}", c.codigo.rstrip(), "```"]
    out += ["", "<details><summary>Trilha de auditoria do pipeline</summary>", ""]
    for e in r.auditoria:
        out.append(f"- **{e.filtro}** (iteração {e.iteracao}, {e.duracao_s}s): " + "; ".join(e.observacoes))
    out += ["", "</details>", ""]
    return "\n".join(out)
