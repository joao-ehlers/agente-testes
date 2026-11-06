"""Contratos de dados entre os filtros do pipeline (validados por Pydantic).

Cada filtro recebe exatamente um contrato e devolve o contrato seguinte. É isso
que garante o baixo acoplamento (GRASP Low Coupling): filtros só se conhecem
através destes esquemas.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, model_validator

from .modelos.dominio import (
    Achado,
    CasoDeTeste,
    CenarioDeTeste,
    EtapaAuditoria,
    ExecucaoDeTeste,
    Linguagem,
    Projeto,
    Requisito,
    Risco,
    TipoTeste,
)


# ---------------------------------------------------------------- entrada
class ArquivoFonte(BaseModel):
    caminho: str = Field(min_length=1)
    conteudo: str
    linguagem: Optional[Linguagem] = None


class EntradaAgente(BaseModel):
    """Contrato público de entrada (API REST, CLI e outros agentes)."""

    projeto: str = "projeto"
    arquivos: List[ArquivoFonte] = Field(default_factory=list)
    diff: Optional[str] = Field(None, description="Diff unificado (git diff)")
    requisitos: List[Requisito] = Field(default_factory=list)
    descricao_funcionalidade: Optional[str] = None
    casos_de_uso: List[str] = Field(default_factory=list)
    contrato_openapi: Optional[Union[str, Dict[str, Any]]] = None
    testes_existentes: List[ArquivoFonte] = Field(default_factory=list)
    relatorios_anteriores: List[Dict[str, Any]] = Field(default_factory=list)
    framework: Optional[str] = Field(None, description="pytest | junit | jest | newman")
    tipos_teste: Optional[List[TipoTeste]] = Field(None, description="Força estratégias específicas")
    api_base_url: Optional[str] = Field(None, description="URL da API para testes de contrato")

    @model_validator(mode="after")
    def _tem_algo_para_testar(self) -> "EntradaAgente":
        if not (self.arquivos or self.diff or self.contrato_openapi):
            raise ValueError("informe ao menos 'arquivos', 'diff' ou 'contrato_openapi'")
        return self


# ---------------------------------------------------------------- filtro 0 -> 1
class EntradaNormalizada(BaseModel):
    projeto: Projeto
    arquivos: List[ArquivoFonte]
    linhas_alteradas: Dict[str, List[int]] = Field(default_factory=dict)
    requisitos: List[Requisito] = Field(default_factory=list)
    descricao_funcionalidade: Optional[str] = None
    casos_de_uso: List[str] = Field(default_factory=list)
    openapi: Optional[Dict[str, Any]] = None
    testes_existentes: List[ArquivoFonte] = Field(default_factory=list)
    relatorios_anteriores: List[Dict[str, Any]] = Field(default_factory=list)
    tipos_teste: Optional[List[TipoTeste]] = None
    api_base_url: Optional[str] = None


# ---------------------------------------------------------------- filtro 1 -> 2
class Parametro(BaseModel):
    nome: str
    anotacao: Optional[str] = None
    default: Optional[str] = None
    obrigatorio: bool = True


class Condicao(BaseModel):
    """Condição simples `param <op> constante` que leva a um `raise`."""

    parametro: str
    operador: str
    valor: Any = None
    excecao: str


class UnidadeCodigo(BaseModel):
    nome: str
    qualificado: str  # modulo.Classe.metodo
    arquivo: str
    modulo: str
    tipo: str  # funcao | metodo | classe
    classe: Optional[str] = None
    construtor_sem_args: bool = True
    parametros: List[Parametro] = Field(default_factory=list)
    retorno: Optional[str] = None
    excecoes: List[str] = Field(default_factory=list)
    condicoes_excecao: List[Condicao] = Field(default_factory=list)
    docstring: Optional[str] = None
    linha_inicio: int = 0
    linha_fim: int = 0
    complexidade: int = 1
    assincrona: bool = False
    alterada: bool = True
    chamadas_internas: List[str] = Field(default_factory=list)
    trecho: str = ""


class EndpointAPI(BaseModel):
    metodo: str
    caminho: str
    operation_id: Optional[str] = None
    resumo: Optional[str] = None
    parametros: List[Dict[str, Any]] = Field(default_factory=list)
    corpo_obrigatorio: bool = False
    exemplo_corpo: Optional[Any] = None
    respostas: List[str] = Field(default_factory=list)


class ContextoAnalisado(BaseModel):
    entrada: EntradaNormalizada
    unidades: List[UnidadeCodigo] = Field(default_factory=list)
    endpoints: List[EndpointAPI] = Field(default_factory=list)
    intencao: Optional[str] = None
    riscos: List[Risco] = Field(default_factory=list)
    unidades_sem_teste: List[str] = Field(default_factory=list)
    testes_instaveis: List[str] = Field(default_factory=list)
    feedback: List[str] = Field(default_factory=list, description="Retorno do Filtro 6 para regeneração")
    iteracao: int = 1


# ---------------------------------------------------------------- filtro 2 -> 3
class ConjuntoCenarios(BaseModel):
    contexto: ContextoAnalisado
    cenarios: List[CenarioDeTeste] = Field(default_factory=list)


# ---------------------------------------------------------------- filtro 3 -> 4
class ItemPlano(BaseModel):
    tipo_teste: TipoTeste
    alvo: str
    cenarios: List[str]


class PlanoDeTeste(BaseModel):
    conjunto: ConjuntoCenarios
    framework: str
    itens: List[ItemPlano] = Field(default_factory=list)


# ---------------------------------------------------------------- filtro 4 -> 5
class ArtefatosDeTeste(BaseModel):
    plano: PlanoDeTeste
    casos: List[CasoDeTeste] = Field(default_factory=list)
    cenarios_sem_codigo: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------- filtro 5 -> 6
class ResultadoPipelineExecucao(BaseModel):
    artefatos: ArtefatosDeTeste
    execucao: ExecucaoDeTeste


# ---------------------------------------------------------------- saída final
class SaidaAnalise(BaseModel):
    contexto: ContextoAnalisado
    cenarios: List[CenarioDeTeste]


class RespostaAgente(BaseModel):
    relatorio_id: Optional[str] = None
    aprovado: Optional[bool] = None
    dados: Dict[str, Any]
    auditoria: List[EtapaAuditoria] = Field(default_factory=list)


__all__ = [n for n in dir() if not n.startswith("_")] + ["Achado"]
