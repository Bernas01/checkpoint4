"""Força bruta.

* Questão 2, Parte B — intervalo contínuo de maior criticidade acumulada.
* Questão 1 (apoio) — mochila por enumeração, usada como "gabarito" nos
  testes e no contraexemplo para provar que a DP é ótima.
"""
from __future__ import annotations

from itertools import combinations
from typing import NamedTuple, Sequence

from .dynamic_programming import Item
from .metricas import Contador


class Intervalo(NamedTuple):
    inicio: int
    fim: int
    soma: float


def validar_serie(valores: Sequence[float]) -> None:
    if len(valores) == 0:
        raise ValueError("a série não pode ser vazia")


def intervalo_critico_forca_bruta(valores: Sequence[float], contador: Contador | None = None) -> Intervalo:
    """Examina explicitamente TODOS os n(n+1)/2 intervalos [i, j].

    Para cada início i, o fim j avança e a soma do intervalo [i, j] é obtida
    de [i, j-1] + valores[j] — cada intervalo é avaliado em O(1), mas todos
    são avaliados. Tempo T(n) = n(n+1)/2 = Θ(n²); espaço S(n) = O(1) extra.
    """
    validar_serie(valores)
    contador = contador or Contador()
    n = len(valores)
    melhor = Intervalo(0, 0, valores[0])
    for i in range(n):
        soma = 0.0
        for j in range(i, n):
            soma += valores[j]
            contador.add()
            if soma > melhor.soma:
                melhor = Intervalo(i, j, soma)
    return melhor


def intervalo_critico_ingenuo(valores: Sequence[float], contador: Contador | None = None) -> Intervalo:
    """Versão literal Θ(n³): recalcula a soma de cada intervalo do zero.

    Mantida só para mostrar por que a versão acima reaproveita a soma anterior.
    """
    validar_serie(valores)
    contador = contador or Contador()
    n = len(valores)
    melhor = Intervalo(0, 0, valores[0])
    for i in range(n):
        for j in range(i, n):
            soma = 0.0
            for k in range(i, j + 1):
                soma += valores[k]
                contador.add()
            if soma > melhor.soma:
                melhor = Intervalo(i, j, soma)
    return melhor


def mochila_forca_bruta(itens: Sequence[Item], capacidade: int) -> tuple[int, list[int]]:
    """Testa os 2^N subconjuntos. Viável só para N pequeno (N <= ~20)."""
    melhor_valor, melhor_ids = 0, []
    for r in range(1, len(itens) + 1):
        for combo in combinations(itens, r):
            if sum(it.peso for it in combo) <= capacidade:
                valor = sum(it.valor for it in combo)
                if valor > melhor_valor:
                    melhor_valor, melhor_ids = valor, sorted(it.id for it in combo)
    return melhor_valor, melhor_ids
