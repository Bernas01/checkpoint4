"""Caminhos mínimos — Dijkstra implementado pelo grupo (sem networkx).

Usado pelo Greedy para saber a distância real (pela malha viária disponível)
entre o veículo e cada ponto candidato.
"""
from __future__ import annotations

import heapq
import math

from .estruturas import Grafo

INF = math.inf


def dijkstra(grafo: Grafo, origem: int) -> tuple[dict[int, float], dict[int, int | None]]:
    """Distância mínima de ``origem`` a todos os vértices, ignorando vias bloqueadas.

    Heap (fila de prioridade) de pares (distância, vértice): ``heappop`` sempre
    devolve o vértice ainda não finalizado mais próximo em O(log V). Usamos
    "remoção preguiçosa": em vez de diminuir a chave, empilhamos um novo par e
    descartamos pares obsoletos ao retirá-los.

    Complexidade: cada aresta pode gerar um push → O((V + E) log V) tempo,
    O(V + E) espaço (heap no pior caso guarda E entradas).

    Retorna (dist, pred). Vértices inalcançáveis ficam com dist = inf.
    """
    if origem not in grafo.pontos:
        raise KeyError(f"origem {origem} inexistente")
    dist: dict[int, float] = {v: INF for v in grafo.pontos}
    pred: dict[int, int | None] = {v: None for v in grafo.pontos}
    dist[origem] = 0.0
    heap: list[tuple[float, int]] = [(0.0, origem)]
    finalizados: set[int] = set()
    while heap:
        d, u = heapq.heappop(heap)
        if u in finalizados:
            continue
        finalizados.add(u)
        for v, peso in grafo.vizinhos(u):
            nova = d + peso
            if nova < dist[v]:
                dist[v] = nova
                pred[v] = u
                heapq.heappush(heap, (nova, v))
    return dist, pred


def reconstruir_caminho(pred: dict[int, int | None], origem: int, destino: int) -> list[int]:
    """Segue os predecessores de ``destino`` até ``origem``. Lista vazia se inalcançável."""
    if destino == origem:
        return [origem]
    if pred.get(destino) is None:
        return []
    caminho = [destino]
    while caminho[-1] != origem:
        caminho.append(pred[caminho[-1]])
    return caminho[::-1]


class MatrizDistancias:
    """Cache de Dijkstra: executa a partir de um vértice apenas quando necessário.

    dict de origem -> (dist, pred). O Greedy só consulta distâncias a partir
    dos pontos por onde o veículo passa, então não calculamos V Dijkstras à toa.
    """

    def __init__(self, grafo: Grafo) -> None:
        self._grafo = grafo
        self._cache: dict[int, tuple[dict[int, float], dict[int, int | None]]] = {}

    def _rodar(self, origem: int):
        if origem not in self._cache:
            self._cache[origem] = dijkstra(self._grafo, origem)
        return self._cache[origem]

    def distancia(self, u: int, v: int) -> float:
        return self._rodar(u)[0][v]

    def caminho(self, u: int, v: int) -> list[int]:
        return reconstruir_caminho(self._rodar(u)[1], u, v)

    @property
    def execucoes(self) -> int:
        return len(self._cache)
