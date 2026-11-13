"""Casos controlados da avaliação (Entrega 2).

Cada caso define a entrada do agente, o resultado esperado em linguagem natural,
uma verificação objetiva sobre o `Relatorio` e o gabarito de defeitos reais
(`defeitos_reais`). O gabarito foi fixado antes das medições: um achado de defeito
fora dele conta como falso positivo, mesmo que seja discutível.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional, Set

import yaml

from ..contratos import ArquivoFonte, EntradaAgente
from ..llm.cliente import ModeloLinguagem
from ..modelos.dominio import Relatorio, Requisito
from .llm_roteirizado import LLMRoteirizado

CORPUS = Path(__file__).parent / "corpus"
EXEMPLOS = Path(__file__).resolve().parents[2] / "exemplos"

# Categorias de achado que afirmam "há um defeito no código sob teste".
CATEGORIAS_DEFEITO = {"defeito_suspeito", "validacao_ausente", "tempo_esgotado", "regressao"}


@dataclass
class Contexto:
    """Recursos externos que alguns casos usam (ex.: URL da API de exemplo em execução)."""

    api_base_url: Optional[str] = None


@dataclass
class Verificacao:
    ok: bool
    obtido: str


@dataclass
class CasoAvaliacao:
    id: str
    tipo: str  # "típico" | "borda"
    cenario: str
    esperado: str
    montar: Callable[[Contexto], EntradaAgente]
    verificar: Callable[[Optional[Relatorio], Optional[Exception]], Verificacao]
    defeitos_reais: Set[str] = field(default_factory=set)
    llm_fixo: Optional[Callable[[], ModeloLinguagem]] = None  # LLM simulado (casos de robustez)
    requer_api: bool = False
    guardar_evidencia: bool = False


def chaves_sinalizadas(r: Relatorio) -> Set[str]:
    """Unidades (ou testes, no caso de regressão) que o agente afirmou estarem com defeito."""
    return {a.alvo or a.teste for a in r.achados if a.categoria in CATEGORIAS_DEFEITO}


def _arq(caminho: str, nome_corpus: str) -> ArquivoFonte:
    return ArquivoFonte(caminho=caminho, conteudo=(CORPUS / nome_corpus).read_text(encoding="utf-8"))


def _cats(r: Relatorio) -> str:
    cont: dict = {}
    for a in r.achados:
        cont[a.categoria] = cont.get(a.categoria, 0) + 1
    return ", ".join(f"{k}×{v}" for k, v in sorted(cont.items())) or "nenhum achado"


def _cob(r: Relatorio) -> str:
    return f"{r.cobertura.percentual:.0f}%" if r.cobertura else "n/d"


def _portao(r: Relatorio) -> str:
    return "aprovado" if r.aprovado else "reprovado"


def _sem_excecao(f):
    def verificar(r, e):
        if e is not None:
            return Verificacao(False, f"exceção inesperada: {type(e).__name__}: {str(e)[:120]}")
        return f(r)
    return verificar


# ------------------------------------------------------------------ típicos
def _c01_montar(_: Contexto) -> EntradaAgente:
    return EntradaAgente(projeto="calc", arquivos=[_arq("calc.py", "calc_correto.py")], requisitos=[
        Requisito(id="RF-10", descricao="Divisão (dividir) rejeita divisor zero."),
        Requisito(id="RF-11", descricao="Média (media) de lista vazia é 0.0."),
        Requisito(id="RF-12", descricao="limitar restringe o valor ao intervalo informado.")])


@_sem_excecao
def _c01_verificar(r: Relatorio) -> Verificacao:
    pct = r.cobertura.percentual if r.cobertura else 0
    ok = r.aprovado and not chaves_sinalizadas(r) and pct >= 70
    return Verificacao(ok, f"Portão {_portao(r)}; {r.resumo.total} testes "
                           f"({r.resumo.aprovados} aprovados); {_cats(r)}; cobertura {_cob(r)}")


def _c02_montar(_: Contexto) -> EntradaAgente:
    loja = EXEMPLOS / "loja"
    reqs = yaml.safe_load((loja / "requisitos.yaml").read_text(encoding="utf-8"))["requisitos"]
    return EntradaAgente(projeto="loja", requisitos=[Requisito.model_validate(x) for x in reqs], arquivos=[
        ArquivoFonte(caminho="loja.py", conteudo=(loja / "loja.py").read_text(encoding="utf-8"))])


@_sem_excecao
def _c02_verificar(r: Relatorio) -> Verificacao:
    sin = chaves_sinalizadas(r)
    plantados = {"loja.ticket_medio", "loja.aplicar_cupom"}
    ok = plantados <= sin and not r.aprovado
    return Verificacao(ok, f"Portão {_portao(r)}; {r.resumo.total} testes; defeitos apontados em "
                           f"{', '.join(sorted(x.split('.', 1)[1] for x in sin)) or 'nenhuma unidade'}; "
                           f"cobertura {_cob(r)}")


def _c03_montar(_: Contexto) -> EntradaAgente:
    return EntradaAgente(projeto="calc-diff", arquivos=[_arq("calc.py", "calc_incremental.py")],
                         diff=(CORPUS / "calc_incremental.diff").read_text(encoding="utf-8"))


@_sem_excecao
def _c03_verificar(r: Relatorio) -> Verificacao:
    alvos = sorted({c.alvo for c in r.cenarios})
    ok = alvos == ["calc.dividir"] and r.aprovado
    return Verificacao(ok, f"Unidades com cenários: {', '.join(alvos) or 'nenhuma'}; "
                           f"{r.resumo.total} testes; portão {_portao(r)}")


def _c04_montar(_: Contexto) -> EntradaAgente:
    return EntradaAgente(
        projeto="calc-regressao", arquivos=[_arq("calc.py", "dobro_regressao.py")],
        testes_existentes=[_arq("tests/test_calc.py", "test_dobro_existente.py")],
        relatorios_anteriores=[{"casos": [{"nome": "tests.test_calc::test_dobro", "status": "aprovado"}]}])


@_sem_excecao
def _c04_verificar(r: Relatorio) -> Verificacao:
    reg = [a.teste for a in r.achados if a.categoria == "regressao"]
    ok = bool(reg) and not r.aprovado
    return Verificacao(ok, f"Regressão apontada em {', '.join(reg) or 'nenhum teste'}; portão {_portao(r)}; "
                           f"{_cats(r)}")


def _c05_montar(ctx: Contexto) -> EntradaAgente:
    return EntradaAgente(projeto="loja-api", api_base_url=ctx.api_base_url,
                         contrato_openapi=(EXEMPLOS / "loja" / "openapi.yaml").read_text(encoding="utf-8"))


@_sem_excecao
def _c05_verificar(r: Relatorio) -> Verificacao:
    api = [c for c in r.casos if c.tipo_teste.value == "api"]
    ok = bool(api) and r.resumo.total > 0 and r.aprovado
    return Verificacao(ok, f"{len(api)} arquivo(s) de teste de API; {r.resumo.aprovados}/{r.resumo.total} "
                           f"requisições conforme o contrato; portão {_portao(r)}")


# ------------------------------------------------------------------ borda
def _b01_montar(_: Contexto) -> EntradaAgente:
    return EntradaAgente(projeto="vazio")  # sem arquivos, diff ou OpenAPI


def _b01_verificar(r, e) -> Verificacao:
    if e is None:
        return Verificacao(False, "entrada vazia foi aceita e o pipeline executou")
    ok = isinstance(e, ValueError) and "informe ao menos" in str(e)
    return Verificacao(ok, f"Rejeitada na validação do contrato ({type(e).__name__}: informe ao menos "
                           f"'arquivos', 'diff' ou 'contrato_openapi'); pipeline não executado")


def _b02_montar(_: Contexto) -> EntradaAgente:
    return EntradaAgente(projeto="sintaxe", arquivos=[_arq("pedido.py", "sintaxe_invalida.py")])


@_sem_excecao
def _b02_verificar(r: Relatorio) -> Verificacao:
    risco = [x for x in r.riscos if "não compila" in x.descricao]
    ok = bool(risco) and risco[0].severidade.value == "alta" and not r.aprovado
    return Verificacao(ok, f"Risco {'ALTA “não compila” registrado' if risco else 'não registrado'}; "
                           f"{r.resumo.total} testes; portão {_portao(r)}")


def _b03_montar(_: Contexto) -> EntradaAgente:
    return EntradaAgente(projeto="laco", arquivos=[_arq("fila.py", "laco_infinito.py")])


@_sem_excecao
def _b03_verificar(r: Relatorio) -> Verificacao:
    tempo = [a for a in r.achados if a.categoria == "tempo_esgotado"]
    alvos = sorted({a.alvo or a.teste for a in tempo})
    ok = alvos == ["fila.processar"] and not r.aprovado
    return Verificacao(ok, f"{len(tempo)} teste(s) interrompido(s) por tempo em {', '.join(alvos) or '—'}; "
                           f"portão {_portao(r)}")


def _b04_montar(_: Contexto) -> EntradaAgente:
    return EntradaAgente(projeto="cotacao", arquivos=[_arq("cotacao.py", "cotacao_rede.py")])


@_sem_excecao
def _b04_verificar(r: Relatorio) -> Verificacao:
    dep = [a for a in r.achados if a.categoria == "dependencia_externa"]
    falso_defeito = chaves_sinalizadas(r)
    ok = bool(dep) and not falso_defeito and not r.aprovado
    return Verificacao(ok, f"{len(dep)} achado(s) dependencia_externa; "
                           f"{len(falso_defeito)} unidade(s) apontada(s) como defeito; portão {_portao(r)}")


def _b05_llm() -> ModeloLinguagem:
    return LLMRoteirizado({"intencao": ["isto não é JSON"], "cenarios": ['{"cenarios": "formato errado"}'],
                           "codigo": ["{}"]})


def _b05_montar(_: Contexto) -> EntradaAgente:
    return EntradaAgente(projeto="calc-llm-invalido", arquivos=[_arq("calc.py", "calc_correto.py")])


@_sem_excecao
def _b05_verificar(r: Relatorio) -> Verificacao:
    origens = {c.origem.value for c in r.cenarios}
    ok = r.resumo.total > 0 and origens == {"heuristica"} and r.aprovado
    return Verificacao(ok, f"Respostas do LLM rejeitadas pelo esquema; cenários de origem "
                           f"{', '.join(sorted(origens)) or '—'}; {r.resumo.total} testes; portão {_portao(r)}")


def _b06_llm() -> ModeloLinguagem:
    ruim = {"titulo": "lista vazia", "tipo": "falha", "descricao": "Dado [] então ZeroDivisionError",
            "alvo": "estat.media", "entradas": {"valores": []}, "excecao_esperada": "ZeroDivisionError"}
    alucinado = {"titulo": "mediana", "tipo": "sucesso", "descricao": "Dado [1,2,3] então 2",
                 "alvo": "estat.mediana", "entradas": {"valores": [1, 2, 3]}, "resultado_esperado": "2"}
    teste = ("import pytest\nfrom estat import media\n\n\ndef test_vazia():\n"
             "    with pytest.raises(ZeroDivisionError):\n        media([])\n")
    return LLMRoteirizado({
        "intencao": [{"intencao": "calcula a média", "riscos": []}],
        "cenarios": [{"cenarios": [ruim, alucinado]}],
        "codigo": [{"arquivos": [{"caminho": "test_llm.py", "conteudo": teste}]}]})


def _b06_montar(_: Contexto) -> EntradaAgente:
    return EntradaAgente(projeto="estat-llm-alucina", arquivos=[_arq("estat.py", "media_defeituosa.py")],
                         requisitos=[Requisito(id="RF-20", descricao="media de lista vazia retorna 0.0")])


@_sem_excecao
def _b06_verificar(r: Relatorio) -> Verificacao:
    alucinado = any(c.alvo == "estat.mediana" for c in r.cenarios)
    legitimou = any(c.excecao_esperada == "ZeroDivisionError" for c in r.cenarios)
    apontou = "estat.media" in chaves_sinalizadas(r)
    ok = not alucinado and not legitimou and apontou and not r.aprovado
    return Verificacao(ok, f"Alvo inexistente {'mantido' if alucinado else 'descartado'}; ZeroDivisionError "
                           f"{'aceito como esperado' if legitimou else 'rejeitado como hipótese'}; defeito em "
                           f"media {'apontado' if apontou else 'não apontado'}; portão {_portao(r)}")


def _b07_montar(_: Contexto) -> EntradaAgente:
    return EntradaAgente(projeto="sem-tipos", arquivos=[_arq("util.py", "sem_anotacoes.py")])


@_sem_excecao
def _b07_verificar(r: Relatorio) -> Verificacao:
    risco = any("anotação de tipo" in x.descricao for x in r.riscos)
    # Sem testes executáveis o portão não pode aprovar; com testes (ex.: gerados pelo LLM), eles decidem.
    ok = risco and (r.resumo.total > 0 or not r.aprovado)
    return Verificacao(ok, f"Risco de testabilidade {'registrado' if risco else 'ausente'}; "
                           f"{r.resumo.total} testes; portão {_portao(r)}"
                           + (f" ({'; '.join(r.motivo_reprovacao)})" if r.motivo_reprovacao else ""))


CASOS: List[CasoAvaliacao] = [
    CasoAvaliacao("C01", "típico", "Código correto com requisitos (sem defeito plantado)",
                  "Portão aprovado, nenhum achado de defeito e cobertura ≥ 70%",
                  _c01_montar, _c01_verificar),
    CasoAvaliacao("C02", "típico", "Módulo da loja com 2 defeitos plantados (ticket_medio, aplicar_cupom)",
                  "Os 2 defeitos plantados apontados e portão reprovado",
                  _c02_montar, _c02_verificar, defeitos_reais={"loja.ticket_medio", "loja.aplicar_cupom"},
                  guardar_evidencia=True),
    CasoAvaliacao("C03", "típico", "Análise incremental: diff altera só a função dividir",
                  "Cenários apenas para dividir e portão aprovado",
                  _c03_montar, _c03_verificar),
    CasoAvaliacao("C04", "típico", "Regressão: suíte existente passava e a mudança a quebrou",
                  "Achado “regressao” em test_dobro e portão reprovado",
                  _c04_montar, _c04_verificar, defeitos_reais={"tests.test_calc::test_dobro"}),
    CasoAvaliacao("C05", "típico", "Contrato OpenAPI com a API da loja em execução",
                  "Testes de API gerados do contrato, executados contra a API e aprovados",
                  _c05_montar, _c05_verificar, requer_api=True),
    CasoAvaliacao("B01", "borda", "Entrada vazia (sem código, diff ou contrato)",
                  "Rejeição na validação do contrato, sem executar o pipeline",
                  _b01_montar, _b01_verificar),
    CasoAvaliacao("B02", "borda", "Código-fonte que não compila",
                  "Risco ALTA “não compila”, nenhum teste e portão reprovado",
                  _b02_montar, _b02_verificar),
    CasoAvaliacao("B03", "borda", "Laço infinito plantado em fila.processar",
                  "Testes interrompidos pelo limite por teste, achado “tempo_esgotado” e portão reprovado",
                  _b03_montar, _b03_verificar, defeitos_reais={"fila.processar"}),
    CasoAvaliacao("B04", "borda", "Código que acessa a rede (bloqueada no isolamento)",
                  "Achado “dependencia_externa”, nenhum falso defeito e portão reprovado",
                  _b04_montar, _b04_verificar),
    CasoAvaliacao("B05", "borda", "LLM devolve respostas fora do esquema JSON",
                  "Respostas rejeitadas, queda para heurística e pipeline concluído",
                  _b05_montar, _b05_verificar, llm_fixo=_b05_llm),
    CasoAvaliacao("B06", "borda", "LLM alucina alvo inexistente e legitima ZeroDivisionError",
                  "Alvo inexistente descartado, exceção acidental rejeitada e defeito apontado",
                  _b06_montar, _b06_verificar, defeitos_reais={"estat.media"}, llm_fixo=_b06_llm),
    CasoAvaliacao("B07", "borda", "Código sem anotações de tipo e classe com construtor com argumentos",
                  "Risco de testabilidade registrado; portão não aprova sem evidência executada",
                  _b07_montar, _b07_verificar),
]
