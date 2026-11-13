"""Bancada da Entrega 2 e ajustes que ela motivou (limite válido, tempo esgotado, rede bloqueada)."""
from pathlib import Path

from agente_testes.agente import AgenteDeTestes
from agente_testes.analise.cenarios_heuristicos import cenarios_heuristicos
from agente_testes.avaliacao.casos import CASOS, CORPUS
from agente_testes.avaliacao.executar import Execucao, ResultadoMutante, calcular_metricas, estatisticas
from agente_testes.avaliacao.mutacao import gerar_mutantes
from agente_testes.contratos import ArquivoFonte, EntradaAgente
from agente_testes.llm.cliente import SemModelo
from agente_testes.pipeline.filtros.f0_normalizacao import NormalizadorDeEntrada
from agente_testes.pipeline.filtros.f1_contexto import AnalisadorDeContexto


def _entrada(nome_corpus: str, caminho: str) -> EntradaAgente:
    return EntradaAgente(arquivos=[ArquivoFonte(caminho=caminho, conteudo=(CORPUS / nome_corpus).read_text())])


def test_cenarios_de_limite_valido_dos_dois_lados_da_fronteira():
    ctx = AnalisadorDeContexto(SemModelo()).processar(NormalizadorDeEntrada().processar(_entrada("precos.py", "precos.py")))
    cen = [c for c in cenarios_heuristicos(ctx) if c.alvo == "precos.calcular_desconto"]
    validos = {(k, v) for c in cen if c.nao_deve_lancar for k, v in c.entradas.items() if k in c.titulo}
    rejeitados = {c.entradas["percentual"] for c in cen if c.excecao_esperada == "ValueError" and "percentual" in c.titulo}
    assert ("valor", 0) in validos and ("percentual", 0) in validos and ("percentual", 100) in validos
    assert rejeitados == {-0.5, 100.5}


def test_laco_infinito_vira_tempo_esgotado_na_unidade(config):
    config.timeout_teste_s = 2
    r = AgenteDeTestes(SemModelo(), config).executar(_entrada("laco_infinito.py", "fila.py"))
    assert {a.categoria for a in r.achados} == {"tempo_esgotado"}
    assert {a.alvo for a in r.achados} == {"fila.processar"}


def test_rede_bloqueada_e_dependencia_externa_e_nao_defeito(config):
    r = AgenteDeTestes(SemModelo(), config).executar(_entrada("cotacao_rede.py", "cotacao.py"))
    cats = {a.categoria for a in r.achados}
    assert "dependencia_externa" in cats and "defeito_suspeito" not in cats


def test_mutantes_unicos_e_compilaveis():
    ms = gerar_mutantes((CORPUS / "precos.py").read_text())
    assert len(ms) == len({m.codigo for m in ms}) == 30
    assert {m.operador for m in ms} == {"ROR", "AOR", "CRP", "RVR"}
    for m in ms:
        compile(m.codigo, m.id, "exec")


def test_casos_cobrem_tipicos_e_borda_com_minimo_de_cinco():
    tipos = [c.tipo for c in CASOS]
    assert len(CASOS) >= 5 and tipos.count("típico") >= 5 and tipos.count("borda") >= 5
    assert len({c.id for c in CASOS}) == len(CASOS)


def test_metricas_calculadas_a_partir_das_execucoes():
    ex = [Execucao("A", "típico", 1, 1.0, True, "", portao_aprovado=False, vp=2, fp=1, fn=0, cobertura=80.0),
          Execucao("A", "típico", 2, 3.0, True, "", portao_aprovado=False, vp=2, fp=1, fn=0, cobertura=90.0),
          Execucao("B", "borda", 1, 2.0, False, "", portao_aprovado=True, fp=1),
          Execucao("B", "borda", 2, 2.0, True, "", portao_aprovado=True)]
    mut = [ResultadoMutante("M1", "ROR", 1, "", True, "", False, "", 0.1),
           ResultadoMutante("M2", "AOR", 1, "", False, "", False, "", 0.1)]
    m = calcular_metricas(ex, mut)
    assert m["taxa_acerto"] == 50.0 and m["casos_falhos"] == ["B"]
    assert m["deteccao"]["vp"] == 4 and m["deteccao"]["fp"] == 3
    assert round(m["deteccao"]["precisao"], 2) == 57.14 and m["deteccao"]["revocacao"] == 100.0
    assert m["falso_positivo_correto"] == 50.0  # 1 das 2 execuções de B (sem defeito) apontou defeito
    assert m["tempo_s"]["media"] == 2.0 and m["cobertura"]["media"] == 85.0
    assert m["mutacao"]["escore"] == 50.0 and m["mutacao"]["deteccao_cega"] == 0.0


def test_estatisticas_ic95_t_student():
    e = estatisticas([1.0, 2.0, 3.0])
    assert e["media"] == 2.0 and e["desvio_padrao"] == 1.0 and round(e["ic95"], 3) == round(4.303 / 3 ** 0.5, 3)
