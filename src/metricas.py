"""Contador de operações relevantes (usado no experimento de escalabilidade)."""
from __future__ import annotations


class Contador:
    """Conta operações elementares definidas por cada algoritmo.

    Força bruta: 1 operação = somar um elemento a um intervalo candidato.
    Dividir e conquistar: 1 operação = visitar um elemento no caso de
    cruzamento ou resolver um caso-base.
    """

    __slots__ = ("operacoes",)

    def __init__(self) -> None:
        self.operacoes = 0

    def add(self, k: int = 1) -> None:
        self.operacoes += k
