"""Código que depende de serviço externo (TLD .invalid nunca resolve: nenhum tráfego real sai)."""
import urllib.request


def consultar_cotacao(moeda: str) -> float:
    """Consulta a cotação da moeda em um serviço HTTP externo."""
    if not moeda:
        raise ValueError("moeda obrigatória")
    with urllib.request.urlopen(f"http://cotacoes.exemplo.invalid/{moeda}", timeout=2) as r:
        return float(r.read())
