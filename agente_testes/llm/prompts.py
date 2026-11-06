"""Prompts e esquemas de resposta (contratos estruturados com o LLM)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..modelos.dominio import Severidade, TipoCenario, TipoTeste

SISTEMA = (
    "Você é um engenheiro de testes de software sênior. Analisa código e requisitos e "
    "propõe testes objetivos. Nunca invente APIs que não existem no código fornecido. "
    "Suas respostas são hipóteses que serão verificadas executando os testes. "
    "Escreva textos em português do Brasil."
)


class RiscoLLM(BaseModel):
    descricao: str
    severidade: Severidade = Severidade.MEDIA
    alvo: Optional[str] = None


class RespostaIntencao(BaseModel):
    intencao: str = Field(description="O que a funcionalidade pretende fazer, em 1-3 frases")
    riscos: List[RiscoLLM] = Field(default_factory=list)


class CenarioLLM(BaseModel):
    titulo: str
    tipo: TipoCenario
    descricao: str = Field(description="Formato Dado/Quando/Então")
    alvo: str = Field(description="Nome qualificado exato da unidade ou 'METODO /caminho'")
    requisito_id: Optional[str] = None
    entradas: Dict[str, Any] = Field(default_factory=dict)
    resultado_esperado: str = ""
    excecao_esperada: Optional[str] = None
    tipo_teste_sugerido: Optional[TipoTeste] = None


class RespostaCenarios(BaseModel):
    cenarios: List[CenarioLLM]


class ArquivoTesteLLM(BaseModel):
    caminho: str
    conteudo: str
    cenarios: List[str] = Field(default_factory=list, description="IDs dos cenários cobertos")


class RespostaCodigo(BaseModel):
    arquivos: List[ArquivoTesteLLM]


def prompt_intencao(resumo_codigo: str, requisitos: str, descricao: str) -> str:
    return (
        "Analise o código e os requisitos abaixo. Descreva a intenção da funcionalidade e "
        "aponte riscos de defeito (entradas não validadas, divisão por zero, estados inválidos, "
        "concorrência, arredondamento, etc.).\n\n"
        f"## Descrição\n{descricao or '(não informada)'}\n\n## Requisitos\n{requisitos or '(nenhum)'}\n\n"
        f"## Código\n{resumo_codigo}")


def prompt_cenarios(resumo_codigo: str, requisitos: str, intencao: str, alvos: List[str],
                    feedback: List[str]) -> str:
    fb = ("\n## Feedback da execução anterior (corrija estes cenários)\n" + "\n".join(f"- {f}" for f in feedback)
          if feedback else "")
    return (
        "Derive cenários de teste de SUCESSO, FALHA e BORDA para as unidades listadas. Para cada "
        "critério de aceite, ao menos um cenário deve referenciar o requisito_id. Use valores concretos "
        "em 'entradas' (nome do parâmetro -> valor JSON) e um 'resultado_esperado' verificável. "
        "Em cenários de falha, use 'excecao_esperada' com o nome exato da exceção lançada no código.\n"
        "IMPORTANTE: o resultado esperado vem dos REQUISITOS, critérios de aceite e documentação — NUNCA do "
        "comportamento atual da implementação. Se o código contradiz um requisito (ex.: lança erro onde o "
        "critério exige retornar 0), escreva o cenário com o comportamento EXIGIDO pelo requisito; o teste deve "
        "falhar e expor o defeito. Nunca espere exceções acidentais (ZeroDivisionError, KeyError, IndexError, "
        "AttributeError) que o código não lança deliberadamente.\n\n"
        f"## Intenção\n{intencao}\n\n## Requisitos\n{requisitos or '(nenhum)'}\n\n"
        f"## Alvos permitidos\n" + "\n".join(f"- {a}" for a in alvos) + f"\n\n## Código\n{resumo_codigo}{fb}")


def prompt_codigo(framework: str, linguagem: str, tipo: str, cenarios_json: str, codigo: str,
                  modulos: str, caminho_sugerido: str, feedback: List[str]) -> str:
    fb = ("\n## Erros da execução anterior destes testes (corrija)\n" + "\n".join(f"- {f}" for f in feedback)
          if feedback else "")
    return (
        f"Escreva testes {tipo} em {linguagem} usando {framework} para os cenários abaixo. Regras:\n"
        "- Um teste por cenário; o nome do teste deve conter o id do cenário em minúsculas com '_' "
        "(ex.: CEN-ab12 -> test_cen_ab12_descricao).\n"
        "- Importe o código pelos módulos indicados; não reimplemente o código sob teste.\n"
        "- Não acesse rede nem disco fora do diretório temporário do teste.\n"
        "- Asserções devem verificar o resultado esperado de forma objetiva.\n"
        f"- Grave em um único arquivo: {caminho_sugerido}\n\n"
        f"## Módulos importáveis\n{modulos}\n\n## Cenários (JSON)\n{cenarios_json}\n\n## Código sob teste\n{codigo}{fb}")
