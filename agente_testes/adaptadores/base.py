"""Padrão Adapter (GoF): cada framework de teste tem comando, formato de saída e
relatório de cobertura próprios. Os adaptadores convertem tudo para um contrato
único (`ResultadoDeTeste` + `Cobertura`), de modo que o núcleo do agente não
conhece nenhuma ferramenta concreta.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..modelos.dominio import Cobertura, Linguagem, ResultadoDeTeste, StatusResultado, TipoTeste


class AdaptadorFramework(ABC):
    nome: str
    linguagem: Linguagem
    imagem_docker: str

    @abstractmethod
    def caminho_teste(self, alvo: str, tipo: TipoTeste) -> str: ...

    @abstractmethod
    def comando(self, arquivos_teste: List[str]) -> str:
        """Comando shell executado na raiz do workspace."""

    @abstractmethod
    def ler_resultados(self, workspace: Path) -> Tuple[List[ResultadoDeTeste], Optional[Cobertura]]: ...

    def preparar_workspace(self, workspace: Path) -> None:
        """Arquivos de configuração que o framework precisa (opcional)."""

    def validar_sintaxe(self, codigo: str) -> Optional[str]:
        """Devolve mensagem de erro se o código gerado for inválido."""
        return None


def ler_junit_xml(arquivo: Path, prefixo_remover: str = "") -> List[ResultadoDeTeste]:
    """Formato JUnit XML: usado por pytest, Maven Surefire, jest-junit, etc."""
    if not arquivo.exists():
        return []
    raiz = ET.parse(arquivo).getroot()
    out: List[ResultadoDeTeste] = []
    for caso in raiz.iter("testcase"):
        classe = caso.get("classname", "")
        nome = caso.get("name", "")
        status, msg, det = StatusResultado.APROVADO, None, None
        for tag, st in (("failure", StatusResultado.REPROVADO), ("error", StatusResultado.ERRO),
                        ("skipped", StatusResultado.IGNORADO)):
            el = caso.find(tag)
            if el is not None:
                status, msg, det = st, el.get("message"), (el.text or "")[-4000:]
                break
        arquivo_teste = caso.get("file") or (classe.replace(".", "/") + ".py" if classe else None)
        out.append(ResultadoDeTeste(
            nome=f"{classe}::{nome}".replace(prefixo_remover, "") if classe else nome,
            arquivo=arquivo_teste, status=status, duracao_s=float(caso.get("time") or 0),
            mensagem=msg, detalhe=det))
    return out


def ler_cobertura_xml_cobertura(arquivo: Path) -> Optional[Cobertura]:
    """Formato Cobertura XML (coverage.py `xml`, istanbul `cobertura`)."""
    if not arquivo.exists():
        return None
    raiz = ET.parse(arquivo).getroot()
    por_arquivo: Dict[str, float] = {}
    faltantes: Dict[str, List[int]] = {}
    for cls in raiz.iter("class"):
        nome = cls.get("filename", "")
        por_arquivo[nome] = round(float(cls.get("line-rate", 0)) * 100, 1)
        faltantes[nome] = [int(l.get("number")) for l in cls.iter("line") if l.get("hits") == "0"]
    return Cobertura(percentual=round(float(raiz.get("line-rate", 0)) * 100, 1),
                     por_arquivo=por_arquivo, linhas_nao_cobertas={k: v for k, v in faltantes.items() if v})
