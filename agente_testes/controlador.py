"""GRASP Controller: ponto único que recebe solicitações externas (API REST, CLI,
outros agentes) e delega ao pipeline. Não contém regra de geração ou execução.
"""
from __future__ import annotations

from typing import List, Optional

from .agente import AgenteDeTestes, Configuracao
from .contratos import EntradaAgente, RespostaAgente
from .integracoes.agente_documentacao import ClienteAgenteDocumentacao
from .llm.cliente import ModeloLinguagem
from .modelos.dominio import Relatorio, Requisito
from .modelos.repositorio import RepositorioRelatorios


class ControladorAgente:
    def __init__(self, llm: Optional[ModeloLinguagem] = None, config: Optional[Configuracao] = None,
                 repositorio: Optional[RepositorioRelatorios] = None,
                 documentacao: Optional[ClienteAgenteDocumentacao] = None):
        self.config = config or Configuracao()
        self.agente = AgenteDeTestes(llm, self.config)
        self.repo = repositorio or RepositorioRelatorios(self.config.dir_dados / "relatorios")
        self.documentacao = documentacao or ClienteAgenteDocumentacao()

    @property
    def modelo(self) -> str:
        return self.agente.llm.nome

    def _completar_requisitos(self, entrada: EntradaAgente) -> EntradaAgente:
        """Se não vieram requisitos, tenta a especificação vigente no Agente de Documentação."""
        if entrada.requisitos or not self.documentacao.configurado:
            return entrada
        spec = self.documentacao.consultar_especificacao(entrada.projeto) or {}
        reqs: List[Requisito] = [Requisito.model_validate(r) for r in spec.get("requisitos", [])]
        return entrada.model_copy(update={"requisitos": reqs}) if reqs else entrada

    def analisar(self, entrada: EntradaAgente) -> RespostaAgente:
        conj, p = self.agente.analisar(self._completar_requisitos(entrada))
        ctx = conj.contexto
        return RespostaAgente(dados={
            "projeto": ctx.entrada.projeto.model_dump(),
            "intencao": ctx.intencao,
            "unidades": [{"alvo": u.qualificado, "arquivo": u.arquivo, "linhas": [u.linha_inicio, u.linha_fim],
                          "complexidade": u.complexidade, "excecoes": u.excecoes} for u in ctx.unidades if u.alterada],
            "endpoints": [f"{e.metodo} {e.caminho}" for e in ctx.endpoints],
            "cenarios": [c.model_dump(mode="json") for c in conj.cenarios],
            "riscos": [r.model_dump(mode="json") for r in ctx.riscos],
        }, auditoria=p.auditoria)

    def gerar_testes(self, entrada: EntradaAgente) -> RespostaAgente:
        art, p = self.agente.gerar_testes(self._completar_requisitos(entrada))
        return RespostaAgente(dados={
            "framework": art.plano.framework,
            "plano": [i.model_dump(mode="json") for i in art.plano.itens],
            "cenarios": [c.model_dump(mode="json") for c in art.plano.conjunto.cenarios],
            "casos": [c.model_dump(mode="json") for c in art.casos],
            "cenarios_sem_codigo": art.cenarios_sem_codigo,
            "riscos": [r.model_dump(mode="json") for r in art.plano.conjunto.contexto.riscos],
        }, auditoria=p.auditoria)

    def executar(self, entrada: EntradaAgente) -> Relatorio:
        relatorio = self.agente.executar(self._completar_requisitos(entrada))
        self.repo.salvar(relatorio)
        self.documentacao.enviar_resultado(relatorio)
        return relatorio

    def obter_relatorio(self, relatorio_id: str) -> Optional[Relatorio]:
        return self.repo.obter(relatorio_id)

    def listar_relatorios(self, projeto: Optional[str] = None) -> List[dict]:
        return self.repo.listar(projeto)
