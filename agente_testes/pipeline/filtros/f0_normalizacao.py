"""Filtro 0 — Recebimento e normalização da entrada."""
from __future__ import annotations

from collections import Counter

from ...adaptadores.frameworks import PADRAO_POR_LINGUAGEM, obter_adaptador
from ...analise.diff import interpretar_diff
from ...analise.openapi import carregar_openapi
from ...contratos import ArquivoFonte, EntradaAgente, EntradaNormalizada
from ...modelos.dominio import Linguagem, Projeto
from ..base import Filtro

_EXT = {".py": Linguagem.PYTHON, ".java": Linguagem.JAVA, ".js": Linguagem.JAVASCRIPT,
        ".mjs": Linguagem.JAVASCRIPT, ".cjs": Linguagem.JAVASCRIPT, ".jsx": Linguagem.JAVASCRIPT,
        ".ts": Linguagem.TYPESCRIPT, ".tsx": Linguagem.TYPESCRIPT}


def detectar_linguagem(caminho: str) -> Linguagem:
    for ext, lang in _EXT.items():
        if caminho.endswith(ext):
            return lang
    return Linguagem.DESCONHECIDA


class NormalizadorDeEntrada(Filtro[EntradaAgente, EntradaNormalizada]):
    nome = "0-normalizacao"
    tipo_entrada = EntradaAgente
    tipo_saida = EntradaNormalizada

    def processar(self, e: EntradaAgente) -> EntradaNormalizada:
        arquivos = {(a.caminho[2:] if a.caminho.startswith("./") else a.caminho): a for a in e.arquivos}
        linhas = {}
        if e.diff:
            linhas, novos = interpretar_diff(e.diff)
            for caminho, conteudo in novos.items():
                arquivos.setdefault(caminho, ArquivoFonte(caminho=caminho, conteudo=conteudo))
            sem_conteudo = [c for c in linhas if c not in arquivos]
            if sem_conteudo:
                self.anotar(f"diff referencia arquivos sem conteúdo completo (ignorados): {', '.join(sem_conteudo)}")
            linhas = {c: v for c, v in linhas.items() if c in arquivos}

        normalizados = []
        for caminho, a in sorted(arquivos.items()):
            lang = a.linguagem or detectar_linguagem(caminho)
            if lang == Linguagem.DESCONHECIDA:
                self.anotar(f"linguagem não suportada, ignorado: {caminho}")
                continue
            normalizados.append(ArquivoFonte(caminho=caminho, conteudo=a.conteudo.replace("\r\n", "\n"),
                                             linguagem=lang))

        contagem = Counter(a.linguagem for a in normalizados)
        linguagem = contagem.most_common(1)[0][0] if contagem else Linguagem.DESCONHECIDA
        if len(contagem) > 1:
            self.anotar(f"múltiplas linguagens; predominante: {linguagem.value}")
        framework = e.framework or PADRAO_POR_LINGUAGEM.get(linguagem, "pytest")
        obter_adaptador(framework)  # valida cedo

        openapi = carregar_openapi(e.contrato_openapi)
        self.anotar(f"{len(normalizados)} arquivo(s), linguagem={linguagem.value}, framework={framework}, "
                    f"openapi={'sim' if openapi else 'não'}, diff={'sim' if e.diff else 'não'}")
        return EntradaNormalizada(
            projeto=Projeto(nome=e.projeto, linguagem=linguagem, framework=framework),
            arquivos=normalizados, linhas_alteradas=linhas, requisitos=e.requisitos,
            descricao_funcionalidade=e.descricao_funcionalidade, casos_de_uso=e.casos_de_uso,
            openapi=openapi, testes_existentes=e.testes_existentes,
            relatorios_anteriores=e.relatorios_anteriores, tipos_teste=e.tipos_teste,
            api_base_url=e.api_base_url)
