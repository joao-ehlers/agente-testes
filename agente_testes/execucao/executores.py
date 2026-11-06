"""Execução dos testes em ambiente isolado (Docker) ou local (fallback de desenvolvimento)."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


@dataclass
class SaidaProcesso:
    codigo: int
    saida: str
    duracao_s: float
    executor: str
    comando: str


class Executor(ABC):
    nome: str

    @abstractmethod
    def executar(self, workspace: Path, comando: str, imagem: str, timeout_s: int,
                 env: Dict[str, str], rede: bool) -> SaidaProcesso: ...


def _rodar(args, cwd: Optional[Path], timeout_s: int, env=None) -> tuple:
    t0 = time.perf_counter()
    try:
        p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout_s, env=env)
        return p.returncode, (p.stdout + p.stderr)[-20000:], time.perf_counter() - t0
    except subprocess.TimeoutExpired as e:
        saida = ((e.stdout or b"") + (e.stderr or b"")) if isinstance(e.stdout, bytes) else (e.stdout or "")
        if isinstance(saida, bytes):
            saida = saida.decode(errors="replace")
        return 124, f"{saida}\n[agente] tempo limite de {timeout_s}s excedido", time.perf_counter() - t0


class ExecutorDocker(Executor):
    """Container descartável: sem rede (salvo testes de API), CPU/memória/PIDs limitados,
    usuário não-root e apenas o workspace montado."""

    nome = "docker"

    def __init__(self, memoria: str = "1g", cpus: str = "1.0"):
        self.memoria = memoria
        self.cpus = cpus

    @staticmethod
    def disponivel() -> bool:
        if not shutil.which("docker"):
            return False
        try:
            return subprocess.run(["docker", "info"], capture_output=True, timeout=10).returncode == 0
        except Exception:
            return False

    @staticmethod
    def imagem_existe(imagem: str) -> bool:
        return subprocess.run(["docker", "image", "inspect", imagem], capture_output=True).returncode == 0

    def executar(self, workspace, comando, imagem, timeout_s, env, rede):
        nome = f"agente-testes-{os.getpid()}-{int(time.time() * 1000)}"
        args = ["docker", "run", "--rm", "--name", nome,
                "--memory", self.memoria, "--cpus", self.cpus, "--pids-limit", "256",
                "--security-opt", "no-new-privileges",
                "-v", f"{workspace.resolve()}:/workspace", "-w", "/workspace",
                "-e", "PYTHONDONTWRITEBYTECODE=1", "-e", "HOME=/tmp"]
        if hasattr(os, "getuid"):
            args += ["--user", f"{os.getuid()}:{os.getgid()}"]
        args += ["--network", "bridge", "--add-host", "host.docker.internal:host-gateway"] if rede \
            else ["--network", "none"]
        for k, v in env.items():
            args += ["-e", f"{k}={v}"]
        args += [imagem, "sh", "-c", comando]
        codigo, saida, dur = _rodar(args, None, timeout_s + 30)
        if codigo == 124:
            subprocess.run(["docker", "kill", nome], capture_output=True)
        return SaidaProcesso(codigo, saida, dur, self.nome, comando)


class ExecutorLocal(Executor):
    """Sem isolamento — apenas para desenvolvimento ou quando o Docker não existe."""

    nome = "local"

    def executar(self, workspace, comando, imagem, timeout_s, env, rede):
        comando_local = comando.replace("python -m", f"{sys.executable} -m", 1)
        ambiente = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", **env)
        codigo, saida, dur = _rodar(["sh", "-c", comando_local], workspace, timeout_s, ambiente)
        return SaidaProcesso(codigo, saida, dur, self.nome, comando_local)


def escolher_executor(preferencia: str, imagem: str) -> Executor:
    """preferencia: docker | local | auto (docker se a imagem existir, senão local)."""
    preferencia = (preferencia or "auto").lower()
    if preferencia == "local":
        return ExecutorLocal()
    if preferencia == "docker":
        if not ExecutorDocker.disponivel():
            raise RuntimeError("Docker indisponível (defina AGENTE_EXECUTOR=local para executar sem isolamento)")
        if not ExecutorDocker.imagem_existe(imagem):
            raise RuntimeError(f"imagem {imagem} não encontrada; construa com: make imagens")
        return ExecutorDocker()
    if ExecutorDocker.disponivel() and ExecutorDocker.imagem_existe(imagem):
        return ExecutorDocker()
    return ExecutorLocal()
