"""Análise estática de código Python via AST (determinística)."""
from __future__ import annotations

import ast
from typing import Dict, List, Optional, Set

from ..contratos import Condicao, Parametro, UnidadeCodigo


def nome_modulo(caminho: str) -> str:
    partes = caminho.replace("\\", "/").split("/")
    if partes and partes[0] in ("src", "lib"):
        partes = partes[1:]
    partes[-1] = partes[-1].rsplit(".", 1)[0]
    if partes[-1] == "__init__":
        partes = partes[:-1]
    return ".".join(p for p in partes if p)


def _txt(no: Optional[ast.AST]) -> Optional[str]:
    if no is None:
        return None
    try:
        return ast.unparse(no)
    except Exception:  # pragma: no cover
        return None


def _nome_excecao(no: Optional[ast.AST]) -> Optional[str]:
    if no is None:
        return None
    if isinstance(no, ast.Call):
        no = no.func
    if isinstance(no, ast.Name):
        return no.id
    if isinstance(no, ast.Attribute):
        return no.attr
    return None


_OPS = {ast.Lt: "<", ast.LtE: "<=", ast.Gt: ">", ast.GtE: ">=", ast.Eq: "==", ast.NotEq: "!=",
        ast.Is: "is", ast.IsNot: "is not"}


def _condicao_simples(teste: ast.AST, params: Set[str], excecao: str) -> Optional[Condicao]:
    """Reconhece `p < 0`, `p == 0`, `p is None`, `not p`, `0 > p`, `len(p) == 0`."""
    if isinstance(teste, ast.UnaryOp) and isinstance(teste.op, ast.Not) and isinstance(teste.operand, ast.Name):
        if teste.operand.id in params:
            return Condicao(parametro=teste.operand.id, operador="falsy", excecao=excecao)
    if isinstance(teste, ast.BoolOp) and isinstance(teste.op, ast.Or):
        for v in teste.values:
            c = _condicao_simples(v, params, excecao)
            if c:
                return c
    if not (isinstance(teste, ast.Compare) and len(teste.ops) == 1):
        return None
    esq, op, dir_ = teste.left, type(teste.ops[0]), teste.comparators[0]
    if op not in _OPS:
        return None
    if isinstance(esq, ast.Constant) and isinstance(dir_, ast.Name):  # 0 > p  =>  p < 0
        inverso = {ast.Lt: ast.Gt, ast.Gt: ast.Lt, ast.LtE: ast.GtE, ast.GtE: ast.LtE}
        esq, dir_, op = dir_, esq, inverso.get(op, op)
    if isinstance(esq, ast.Call) and isinstance(esq.func, ast.Name) and esq.func.id == "len" \
            and esq.args and isinstance(esq.args[0], ast.Name) and isinstance(dir_, ast.Constant):
        if esq.args[0].id in params:
            return Condicao(parametro=esq.args[0].id, operador="len" + _OPS[op], valor=dir_.value, excecao=excecao)
    if isinstance(esq, ast.Name) and esq.id in params and isinstance(dir_, ast.Constant):
        return Condicao(parametro=esq.id, operador=_OPS[op], valor=dir_.value, excecao=excecao)
    return None


def _condicoes(teste: ast.AST, params: Set[str], excecao: str) -> List[Condicao]:
    """Todas as condições simples de um `if`: cada termo de `a or b` leva ao mesmo `raise`."""
    if isinstance(teste, ast.BoolOp) and isinstance(teste.op, ast.Or):
        return [c for v in teste.values for c in _condicoes(v, params, excecao)]
    c = _condicao_simples(teste, params, excecao)
    return [c] if c else []


class _ColetorFuncao(ast.NodeVisitor):
    def __init__(self, params: Set[str]):
        self.params = params
        self.excecoes: List[str] = []
        self.condicoes: List[Condicao] = []
        self.ramos = 1
        self.chamadas: Set[str] = set()

    def visit_If(self, no: ast.If) -> None:
        self.ramos += 1
        for filho in no.body:
            if isinstance(filho, ast.Raise):
                exc = _nome_excecao(filho.exc)
                if exc:
                    self.condicoes += _condicoes(no.test, self.params, exc)
        self.generic_visit(no)

    def visit_For(self, no): self.ramos += 1; self.generic_visit(no)
    def visit_While(self, no): self.ramos += 1; self.generic_visit(no)
    def visit_ExceptHandler(self, no): self.ramos += 1; self.generic_visit(no)
    def visit_IfExp(self, no): self.ramos += 1; self.generic_visit(no)

    def visit_BoolOp(self, no):
        self.ramos += len(no.values) - 1
        self.generic_visit(no)

    def visit_Raise(self, no: ast.Raise) -> None:
        exc = _nome_excecao(no.exc)
        if exc and exc not in self.excecoes:
            self.excecoes.append(exc)
        self.generic_visit(no)

    def visit_Call(self, no: ast.Call) -> None:
        if isinstance(no.func, ast.Name):
            self.chamadas.add(no.func.id)
        self.generic_visit(no)

    # Não desce em funções/classes aninhadas
    def visit_FunctionDef(self, no): pass
    def visit_AsyncFunctionDef(self, no): pass
    def visit_ClassDef(self, no): pass


def _parametros(args: ast.arguments, eh_metodo: bool) -> List[Parametro]:
    posicionais = list(args.posonlyargs) + list(args.args)
    if eh_metodo and posicionais and posicionais[0].arg in ("self", "cls"):
        posicionais = posicionais[1:]
    defaults = [None] * (len(posicionais) - len(args.defaults)) + list(args.defaults)
    out = [Parametro(nome=a.arg, anotacao=_txt(a.annotation), default=_txt(d), obrigatorio=d is None)
           for a, d in zip(posicionais, defaults)]
    for a, d in zip(args.kwonlyargs, args.kw_defaults):
        out.append(Parametro(nome=a.arg, anotacao=_txt(a.annotation), default=_txt(d), obrigatorio=d is None))
    return out


def _construtor_sem_args(classe: ast.ClassDef) -> bool:
    for no in classe.body:
        if isinstance(no, ast.FunctionDef) and no.name == "__init__":
            return all(not p.obrigatorio for p in _parametros(no.args, True))
    # dataclass sem defaults exige argumentos
    for dec in classe.decorator_list:
        if "dataclass" in (_txt(dec) or ""):
            return all(not isinstance(n, ast.AnnAssign) or n.value is not None for n in classe.body)
    return True


def analisar_python(caminho: str, codigo: str, linhas_alteradas: Optional[List[int]] = None) -> List[UnidadeCodigo]:
    arvore = ast.parse(codigo, filename=caminho)
    modulo = nome_modulo(caminho)
    linhas = codigo.splitlines()
    alteradas = set(linhas_alteradas or [])
    nomes_modulo = {n.name for n in arvore.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    unidades: List[UnidadeCodigo] = []

    def registrar(no, classe: Optional[ast.ClassDef]) -> None:
        if no.name.startswith("_") and no.name != "__call__":
            return
        eh_metodo = classe is not None
        decs = {_txt(d) for d in no.decorator_list}
        if eh_metodo and "staticmethod" in decs:
            eh_metodo_inst = False
        else:
            eh_metodo_inst = eh_metodo
        params = _parametros(no.args, eh_metodo)
        col = _ColetorFuncao({p.nome for p in params})
        for filho in no.body:
            col.visit(filho)
        fim = getattr(no, "end_lineno", no.lineno)
        unidades.append(UnidadeCodigo(
            nome=no.name,
            qualificado=f"{modulo}.{classe.name}.{no.name}" if classe else f"{modulo}.{no.name}",
            arquivo=caminho, modulo=modulo,
            tipo="metodo" if eh_metodo_inst else "funcao",
            classe=classe.name if classe else None,
            construtor_sem_args=_construtor_sem_args(classe) if classe else True,
            parametros=params, retorno=_txt(no.returns),
            excecoes=col.excecoes, condicoes_excecao=col.condicoes,
            docstring=ast.get_docstring(no),
            linha_inicio=no.lineno, linha_fim=fim,
            complexidade=col.ramos,
            assincrona=isinstance(no, ast.AsyncFunctionDef),
            alterada=(not alteradas) or bool(alteradas & set(range(no.lineno, fim + 1))),
            chamadas_internas=sorted(col.chamadas & nomes_modulo),
            trecho="\n".join(linhas[no.lineno - 1: fim]),
        ))

    for no in arvore.body:
        if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef)):
            registrar(no, None)
        elif isinstance(no, ast.ClassDef) and not no.name.startswith("_"):
            for m in no.body:
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    registrar(m, no)
    return unidades


def nomes_testados(testes: List[str]) -> Set[str]:
    """Nomes de funções/métodos referenciados pela suíte existente."""
    nomes: Set[str] = set()
    for codigo in testes:
        try:
            arvore = ast.parse(codigo)
        except SyntaxError:
            continue
        for no in ast.walk(arvore):
            if isinstance(no, ast.Call):
                n = _nome_excecao(no.func)
                if n:
                    nomes.add(n)
    return nomes


def contar_linhas_por_unidade(unidades: List[UnidadeCodigo], faltantes: Dict[str, List[int]]) -> Dict[str, List[int]]:
    out: Dict[str, List[int]] = {}
    for u in unidades:
        linhas = [ln for ln in faltantes.get(u.arquivo, []) if u.linha_inicio <= ln <= u.linha_fim]
        if linhas:
            out[u.qualificado] = linhas
    return out
