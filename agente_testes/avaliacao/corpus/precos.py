"""Base correta para o teste de mutação (mesmas regras de RF-01 e RF-02 da loja)."""


def calcular_desconto(valor: float, percentual: float) -> float:
    """Aplica um desconto percentual (0 a 100) sobre o valor."""
    if valor < 0:
        raise ValueError("valor negativo")
    if percentual < 0 or percentual > 100:
        raise ValueError("percentual fora do intervalo")
    return round(valor * (1 - percentual / 100), 2)


def calcular_frete(peso_kg: float, distancia_km: int) -> float:
    """Frete: R$ 10 fixo + R$ 0,50/kg + R$ 0,10/km; acima de 30 kg cobra 20% a mais."""
    if peso_kg <= 0:
        raise ValueError("peso deve ser positivo")
    if distancia_km < 0:
        raise ValueError("distância negativa")
    frete = 10 + 0.5 * peso_kg + 0.1 * distancia_km
    if peso_kg > 30:
        frete *= 1.2
    return round(frete, 2)
