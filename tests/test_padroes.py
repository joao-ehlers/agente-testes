"""Verifica os padrões de projeto exigidos pela especificação."""
import pytest

from agente_testes.adaptadores.base import ler_junit_xml
from agente_testes.adaptadores.frameworks import ADAPTADORES, AdaptadorPytest, obter_adaptador
from agente_testes.contratos import ConjuntoCenarios, EntradaAgente, ArquivoFonte
from agente_testes.estrategias.estrategias import TODAS
from agente_testes.geradores.geradores import (CRIADORES, GeradorColecaoNewman, GeradorTesteAPI,
                                               GeradorTesteUnitario, GeradorTesteValidacaoEntrada)
from agente_testes.llm.cliente import SemModelo
from agente_testes.modelos.dominio import CenarioDeTeste, StatusResultado, TipoCenario, TipoTeste
from agente_testes.pipeline.base import ErroDeContrato, Pipeline
from agente_testes.pipeline.filtros.f0_normalizacao import NormalizadorDeEntrada
from agente_testes.pipeline.filtros.f1_contexto import AnalisadorDeContexto
from agente_testes.pipeline.filtros.f3_estrategia import SeletorDeEstrategia


def test_factory_method_cria_gerador_por_tipo():
    llm = SemModelo()
    assert type(CRIADORES[TipoTeste.UNITARIO].criar_gerador(ADAPTADORES["pytest"], llm)) is GeradorTesteUnitario
    assert type(CRIADORES[TipoTeste.VALIDACAO_ENTRADA].criar_gerador(ADAPTADORES["pytest"], llm)) is GeradorTesteValidacaoEntrada
    assert type(CRIADORES[TipoTeste.API].criar_gerador(ADAPTADORES["pytest"], llm)) is GeradorTesteAPI
    assert type(CRIADORES[TipoTeste.API].criar_gerador(ADAPTADORES["newman"], llm)) is GeradorColecaoNewman


def test_adapter_converte_junit_para_contrato_unico(tmp_path):
    xml = tmp_path / "r.xml"
    xml.write_text('<testsuite><testcase classname="t.m" name="test_a" time="0.1"/>'
                   '<testcase classname="t.m" name="test_b"><failure message="boom">tb</failure></testcase>'
                   '<testcase classname="t.m" name="test_c"><error message="x"/></testcase>'
                   '<testcase classname="t.m" name="test_d"><skipped/></testcase></testsuite>')
    assert [r.status for r in ler_junit_xml(xml)] == [StatusResultado.APROVADO, StatusResultado.REPROVADO,
                                                      StatusResultado.ERRO, StatusResultado.IGNORADO]
    assert set(ADAPTADORES) >= {"pytest", "junit", "jest", "vitest", "newman"}
    with pytest.raises(ValueError):
        obter_adaptador("mocha")
    assert AdaptadorPytest().validar_sintaxe("def x(:") is not None


def test_strategy_selecionada_em_tempo_de_execucao():
    codigo = "def f(x: int) -> int:\n    return x\n"
    ent = EntradaAgente(arquivos=[ArquivoFonte(caminho="m.py", conteudo=codigo)])
    ctx = Pipeline([NormalizadorDeEntrada(), AnalisadorDeContexto(SemModelo())]).executar(ent)
    cen = [
        CenarioDeTeste(titulo="sucesso", tipo=TipoCenario.SUCESSO, descricao="dado x", alvo="m.f"),
        CenarioDeTeste(titulo="nulo", tipo=TipoCenario.FALHA, descricao="dado None", alvo="m.f", entradas={"x": None},
                       excecao_esperada="TypeError"),
    ]
    plano = SeletorDeEstrategia().processar(ConjuntoCenarios(contexto=ctx, cenarios=cen))
    assert {i.tipo_teste for i in plano.itens} == {TipoTeste.UNITARIO, TipoTeste.VALIDACAO_ENTRADA}
    # API não é ativada sem contrato OpenAPI
    assert not [e for e in TODAS if e.tipo == TipoTeste.API][0].ativa(ctx)


def test_pipeline_valida_contrato_entre_filtros():
    ent = EntradaAgente(arquivos=[ArquivoFonte(caminho="m.py", conteudo="x = 1\n")])
    with pytest.raises(ErroDeContrato):
        Pipeline([AnalisadorDeContexto(SemModelo())]).executar(ent)


def test_entrada_vazia_rejeitada():
    with pytest.raises(ValueError):
        EntradaAgente(projeto="x")
