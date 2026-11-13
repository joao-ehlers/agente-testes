"""Model (MVC): entidades de domínio do Agente de Testes.

Concentram estado e validações de consistência. Nenhuma regra de geração ou
execução de testes vive aqui — apenas o que o domínio considera válido.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


def _novo_id(prefixo: str) -> str:
    return f"{prefixo}-{uuid.uuid4().hex[:10]}"


def _agora() -> datetime:
    return datetime.now(timezone.utc)


class Linguagem(str, Enum):
    PYTHON = "python"
    JAVA = "java"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    DESCONHECIDA = "desconhecida"


class TipoCenario(str, Enum):
    SUCESSO = "sucesso"
    FALHA = "falha"
    BORDA = "borda"


class TipoTeste(str, Enum):
    UNITARIO = "unitario"
    INTEGRACAO = "integracao"
    API = "api"
    VALIDACAO_ENTRADA = "validacao_entrada"
    E2E = "e2e"


class StatusResultado(str, Enum):
    APROVADO = "aprovado"
    REPROVADO = "reprovado"
    ERRO = "erro"
    IGNORADO = "ignorado"


class Origem(str, Enum):
    LLM = "llm"
    HEURISTICA = "heuristica"
    CONTRATO = "contrato"
    EXISTENTE = "existente"


class Severidade(str, Enum):
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"


class Projeto(BaseModel):
    nome: str = Field(min_length=1)
    linguagem: Linguagem = Linguagem.DESCONHECIDA
    framework: Optional[str] = None


class Requisito(BaseModel):
    id: str = Field(min_length=1)
    descricao: str = Field(min_length=1)
    criterios_aceite: List[str] = Field(default_factory=list)


class Risco(BaseModel):
    descricao: str
    severidade: Severidade = Severidade.MEDIA
    alvo: Optional[str] = None
    origem: Origem = Origem.HEURISTICA


class CenarioDeTeste(BaseModel):
    """Cenário em linguagem natural. É uma *hipótese* sobre o comportamento."""

    id: str = Field(default_factory=lambda: _novo_id("CEN"))
    titulo: str = Field(min_length=3)
    tipo: TipoCenario
    descricao: str = Field(min_length=3, description="Dado/Quando/Então")
    alvo: str = Field(min_length=1, description="Unidade (modulo.funcao) ou endpoint (GET /x)")
    requisito_id: Optional[str] = None
    entradas: Dict[str, object] = Field(default_factory=dict)
    resultado_esperado: str = ""
    excecao_esperada: Optional[str] = None
    nao_deve_lancar: bool = Field(False, description="Valor-limite válido: qualquer exceção reprova o teste")
    tipo_teste_sugerido: Optional[TipoTeste] = None
    automatizavel: bool = True
    origem: Origem = Origem.HEURISTICA

    @model_validator(mode="after")
    def _falha_precisa_de_expectativa(self) -> "CenarioDeTeste":
        if self.tipo == TipoCenario.FALHA and not (self.excecao_esperada or self.resultado_esperado):
            raise ValueError("cenário de falha precisa de exceção ou resultado esperado")
        return self


class CasoDeTeste(BaseModel):
    """Artefato executável gerado (um arquivo de teste no framework do projeto)."""

    id: str = Field(default_factory=lambda: _novo_id("CASO"))
    caminho: str = Field(min_length=1)
    codigo: str = Field(min_length=1)
    tipo_teste: TipoTeste
    framework: str
    cenarios: List[str] = Field(default_factory=list)
    origem: Origem = Origem.HEURISTICA

    @field_validator("caminho")
    @classmethod
    def _caminho_relativo_seguro(cls, v: str) -> str:
        if v.startswith("/") or ".." in v.split("/"):
            raise ValueError("caminho de teste deve ser relativo e sem '..'")
        return v


class ResultadoDeTeste(BaseModel):
    nome: str
    arquivo: Optional[str] = None
    status: StatusResultado
    duracao_s: float = 0.0
    mensagem: Optional[str] = None
    detalhe: Optional[str] = None
    cenario_id: Optional[str] = None


class Cobertura(BaseModel):
    percentual: float = Field(ge=0, le=100)
    por_arquivo: Dict[str, float] = Field(default_factory=dict)
    linhas_nao_cobertas: Dict[str, List[int]] = Field(default_factory=dict)


class ExecucaoDeTeste(BaseModel):
    id: str = Field(default_factory=lambda: _novo_id("EXEC"))
    iniciada_em: datetime = Field(default_factory=_agora)
    executor: str
    framework: str
    comando: str
    codigo_saida: int
    duracao_s: float = 0.0
    resultados: List[ResultadoDeTeste] = Field(default_factory=list)
    cobertura: Optional[Cobertura] = None
    saida: str = ""


class ResumoExecucao(BaseModel):
    total: int = 0
    aprovados: int = 0
    reprovados: int = 0
    erros: int = 0
    ignorados: int = 0

    @classmethod
    def de(cls, resultados: List[ResultadoDeTeste]) -> "ResumoExecucao":
        r = cls(total=len(resultados))
        for x in resultados:
            if x.status == StatusResultado.APROVADO:
                r.aprovados += 1
            elif x.status == StatusResultado.REPROVADO:
                r.reprovados += 1
            elif x.status == StatusResultado.ERRO:
                r.erros += 1
            else:
                r.ignorados += 1
        return r


class Achado(BaseModel):
    """Interpretação de um resultado: defeito suspeito, risco ou erro do próprio teste."""

    # defeito_suspeito | validacao_ausente | tempo_esgotado | dependencia_externa | erro_no_teste |
    # regressao | falha_suite_existente
    categoria: str
    teste: str
    cenario_id: Optional[str] = None
    alvo: Optional[str] = None
    explicacao: str


class EtapaAuditoria(BaseModel):
    filtro: str
    iteracao: int = 1
    duracao_s: float
    observacoes: List[str] = Field(default_factory=list)


class Relatorio(BaseModel):
    id: str = Field(default_factory=lambda: _novo_id("REL"))
    criado_em: datetime = Field(default_factory=_agora)
    projeto: Projeto
    requisitos: List[Requisito] = Field(default_factory=list)
    cenarios: List[CenarioDeTeste] = Field(default_factory=list)
    casos: List[CasoDeTeste] = Field(default_factory=list)
    execucao: Optional[ExecucaoDeTeste] = None
    resumo: ResumoExecucao = Field(default_factory=ResumoExecucao)
    cobertura: Optional[Cobertura] = None
    riscos: List[Risco] = Field(default_factory=list)
    trechos_nao_cobertos: List[str] = Field(default_factory=list)
    achados: List[Achado] = Field(default_factory=list)
    iteracoes: int = 1
    aprovado: bool = False
    motivo_reprovacao: List[str] = Field(default_factory=list)
    modelo_linguagem: str = "nenhum"
    auditoria: List[EtapaAuditoria] = Field(default_factory=list)

    @model_validator(mode="after")
    def _resumo_consistente(self) -> "Relatorio":
        if self.execucao is not None and self.resumo.total != len(self.execucao.resultados):
            raise ValueError("resumo inconsistente com os resultados da execução")
        return self
