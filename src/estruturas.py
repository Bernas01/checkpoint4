"""Estruturas de dados das duas questões.

Questão 1 — rede de atendimento da Defesa Civil
    * ``Ponto`` (dataclass imutável): atributos de um vértice.
    * ``Grafo``: lista de adjacência ``dict[int, dict[int, float]]`` + ``set``
      de vias bloqueadas.

Questão 2 — consumo de energia
    * ``Registro`` (NamedTuple = tupla): uma medição horária.
    * ``IndiceEnergia``: agrupa ``list``, ``dict``, ``set``, ``heap`` e somas
      de prefixo para responder às consultas pedidas na Parte A.

A justificativa de cada escolha está nas docstrings e no README.
"""
from __future__ import annotations

import heapq
from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Iterator, NamedTuple


FATOR_PRIORIDADE = {1: 1.0, 2: 1.5, 3: 2.0, 4: 3.0, 5: 4.0}


def calcular_beneficio(pessoas: int, prioridade: int) -> int:
    """Benefício esperado de atender um ponto.

    benefício = pessoas/10 * fator(prioridade). O fator cresce de forma
    super-linear para que uma região de prioridade 5 valha 4x uma de
    prioridade 1 com o mesmo número de pessoas. Inteiro para que a DP compare
    valores sem erro de ponto flutuante.
    """
    if prioridade not in FATOR_PRIORIDADE:
        raise ValueError(f"prioridade deve estar em 1..5, recebido {prioridade}")
    if pessoas < 0:
        raise ValueError("pessoas não pode ser negativo")
    return round(pessoas / 10 * FATOR_PRIORIDADE[prioridade])


@dataclass(frozen=True)
class Ponto:
    """Vértice do grafo (centro de distribuição ou ponto de atendimento).

    ``frozen=True``: um ponto não muda durante a execução; imutabilidade evita
    que um algoritmo altere acidentalmente o dado de outro.
    """

    id: int
    nome: str
    x: float
    y: float
    pessoas: int
    prioridade: int
    demanda: int
    beneficio: int
    eh_centro: bool = False

    def __post_init__(self) -> None:
        if not self.eh_centro and self.demanda <= 0:
            raise ValueError(f"ponto {self.id}: demanda deve ser positiva")
        if self.beneficio < 0:
            raise ValueError(f"ponto {self.id}: benefício negativo")


def _chave_aresta(u: int, v: int) -> frozenset:
    return frozenset((u, v))


class Grafo:
    """Grafo não direcionado e ponderado.

    Por que ``dict[int, dict[int, float]]`` (lista de adjacência com dict)?
      * Dijkstra percorre os vizinhos de cada vértice: custo O(grau(u)), e o
        total fica O(V + E) — uma matriz de adjacência custaria O(V²).
      * O grafo é esparso (E ≈ 2V), então a matriz desperdiçaria memória.
      * ``peso(u, v)`` e ``alterar_peso`` são O(1): útil quando o professor
        muda um peso durante a apresentação.

    Por que ``set`` de ``frozenset`` para as vias bloqueadas?
      * ``esta_bloqueada`` é chamada para CADA aresta relaxada no Dijkstra;
        em um set a pertinência é O(1) média. Em uma lista seria O(B).
      * ``frozenset({u, v})`` é igual a ``frozenset({v, u})``: a via é não
        direcionada sem precisar armazenar duas chaves.
      * Bloquear/desbloquear uma via é O(1) e não apaga o peso original.
    """

    def __init__(self) -> None:
        self.pontos: dict[int, Ponto] = {}
        self._adj: dict[int, dict[int, float]] = {}
        self._bloqueadas: set[frozenset] = set()

    def adicionar_ponto(self, ponto: Ponto) -> None:
        if ponto.id in self.pontos:
            raise ValueError(f"ponto {ponto.id} duplicado")
        self.pontos[ponto.id] = ponto
        self._adj[ponto.id] = {}

    def adicionar_aresta(self, u: int, v: int, peso: float, bloqueada: bool = False) -> None:
        self._validar_par(u, v)
        if peso <= 0:
            raise ValueError(f"peso da aresta {u}-{v} deve ser positivo")
        if v in self._adj[u]:
            raise ValueError(f"aresta {u}-{v} duplicada")
        self._adj[u][v] = peso
        self._adj[v][u] = peso
        if bloqueada:
            self._bloqueadas.add(_chave_aresta(u, v))

    def alterar_peso(self, u: int, v: int, peso: float) -> None:
        self._exigir_aresta(u, v)
        if peso <= 0:
            raise ValueError("peso deve ser positivo")
        self._adj[u][v] = peso
        self._adj[v][u] = peso

    def bloquear(self, u: int, v: int) -> None:
        self._exigir_aresta(u, v)
        self._bloqueadas.add(_chave_aresta(u, v))

    def desbloquear(self, u: int, v: int) -> None:
        self._exigir_aresta(u, v)
        self._bloqueadas.discard(_chave_aresta(u, v))

    def substituir_ponto(self, ponto: Ponto) -> None:
        """Troca os atributos de um ponto existente (ex.: nova prioridade)."""
        if ponto.id not in self.pontos:
            raise KeyError(ponto.id)
        self.pontos[ponto.id] = ponto

    def vizinhos(self, u: int) -> Iterator[tuple[int, float]]:
        """Vizinhos por vias DISPONÍVEIS (ignora as bloqueadas)."""
        for v, peso in self._adj[u].items():
            if _chave_aresta(u, v) not in self._bloqueadas:
                yield v, peso

    def esta_bloqueada(self, u: int, v: int) -> bool:
        return _chave_aresta(u, v) in self._bloqueadas

    def peso(self, u: int, v: int) -> float:
        self._exigir_aresta(u, v)
        return self._adj[u][v]

    def arestas(self) -> list[tuple[int, int, float, bool]]:
        """Todas as arestas (u < v), com a flag de bloqueio."""
        return [
            (u, v, p, self.esta_bloqueada(u, v))
            for u, viz in self._adj.items()
            for v, p in viz.items()
            if u < v
        ]

    @property
    def centro(self) -> int:
        for p in self.pontos.values():
            if p.eh_centro:
                return p.id
        raise ValueError("grafo sem centro de distribuição")

    def pontos_atendimento(self) -> list[Ponto]:
        return [p for p in self.pontos.values() if not p.eh_centro]

    @property
    def num_vertices(self) -> int:
        return len(self.pontos)

    @property
    def num_arestas(self) -> int:
        return sum(len(v) for v in self._adj.values()) // 2

    @property
    def num_bloqueadas(self) -> int:
        return len(self._bloqueadas)

    def _validar_par(self, u: int, v: int) -> None:
        if u == v:
            raise ValueError("laços (u == v) não são permitidos")
        for n in (u, v):
            if n not in self.pontos:
                raise KeyError(f"vértice {n} inexistente")

    def _exigir_aresta(self, u: int, v: int) -> None:
        self._validar_par(u, v)
        if v not in self._adj[u]:
            raise KeyError(f"aresta {u}-{v} inexistente")



class Registro(NamedTuple):
    """Uma medição horária.

    NamedTuple (tupla): imutável, ~3x mais leve que um dict por registro e
    com acesso por nome. Com 10⁶ registros a diferença de memória importa.
    """

    timestamp: datetime
    regiao: str
    consumo: float
    capacidade: float
    prioridade: int
    custo: float

    @property
    def carga(self) -> float:
        return self.consumo / self.capacidade


class IndiceEnergia:
    """Organiza os registros para as consultas da Parte A.

    Estrutura                  | Operação favorecida                    | Custo
    ---------------------------|----------------------------------------|---------
    list (ordenada por tempo)  | acesso por posição / fatia contínua    | O(1)/O(k)
    dict região -> list[int]   | consumo por região                     | O(1)+O(k)
    dict hora -> list[int]     | consumo por horário do dia             | O(1)+O(k)
    list de timestamps + bisect| selecionar intervalo [t0, t1]          | O(log n)
    list de prefixos           | soma do consumo em um intervalo        | O(1)
    set de (timestamp, região) | "esta hora estava sobrecarregada?"     | O(1)
    heap (heapq)               | top-k picos de consumo                 | O(n log k)
    """

    def __init__(self, registros: Iterable[Registro]) -> None:
        self.registros: list[Registro] = sorted(registros, key=lambda r: (r.timestamp, r.regiao))
        if not self.registros:
            raise ValueError("nenhum registro informado")
        self.por_regiao: dict[str, list[int]] = {}
        self.por_hora: dict[int, list[int]] = {}
        self.sobrecarga: set[tuple[datetime, str]] = set()
        for i, r in enumerate(self.registros):
            self.por_regiao.setdefault(r.regiao, []).append(i)
            self.por_hora.setdefault(r.timestamp.hour, []).append(i)
            if r.consumo > r.capacidade:
                self.sobrecarga.add((r.timestamp, r.regiao))
        self._ts: dict[str, list[datetime]] = {}
        self._prefixo: dict[str, list[float]] = {}
        for reg, idx in self.por_regiao.items():
            self._ts[reg] = [self.registros[i].timestamp for i in idx]
            acumulado, pref = 0.0, [0.0]
            for i in idx:
                acumulado += self.registros[i].consumo
                pref.append(acumulado)
            self._prefixo[reg] = pref

    @property
    def regioes(self) -> list[str]:
        return sorted(self.por_regiao)

    def serie(self, regiao: str) -> list[Registro]:
        self._exigir_regiao(regiao)
        return [self.registros[i] for i in self.por_regiao[regiao]]

    def consumo_por_regiao(self) -> dict[str, float]:
        return {reg: self._prefixo[reg][-1] for reg in self.regioes}

    def consumo_medio_por_hora(self) -> dict[int, float]:
        return {
            h: sum(self.registros[i].consumo for i in idx) / len(idx)
            for h, idx in sorted(self.por_hora.items())
        }

    def picos(self, k: int = 10, regiao: str | None = None) -> list[Registro]:
        """Os k registros de maior consumo — heap de tamanho k, O(n log k)."""
        if k <= 0:
            raise ValueError("k deve ser positivo")
        fonte = self.serie(regiao) if regiao else self.registros
        return heapq.nlargest(k, fonte, key=lambda r: r.consumo)

    def esta_sobrecarregado(self, timestamp: datetime, regiao: str) -> bool:
        return (timestamp, regiao) in self.sobrecarga

    def periodos_criticos(self, regiao: str, limiar_carga: float = 1.0) -> list[tuple[datetime, datetime]]:
        """Trechos consecutivos com carga (consumo/capacidade) acima do limiar."""
        periodos, inicio, anterior = [], None, None
        for r in self.serie(regiao):
            if r.carga > limiar_carga:
                inicio = inicio or r.timestamp
                anterior = r.timestamp
            elif inicio is not None:
                periodos.append((inicio, anterior))
                inicio = None
        if inicio is not None:
            periodos.append((inicio, anterior))
        return periodos

    def selecionar_intervalo(self, regiao: str, inicio: datetime, fim: datetime) -> list[Registro]:
        """Registros da região com inicio <= t <= fim — busca binária O(log n)."""
        a, b = self._limites(regiao, inicio, fim)
        idx = self.por_regiao[regiao]
        return [self.registros[i] for i in idx[a:b]]

    def consumo_no_intervalo(self, regiao: str, inicio: datetime, fim: datetime) -> float:
        """Soma do consumo em [inicio, fim] — O(log n) com prefixos."""
        a, b = self._limites(regiao, inicio, fim)
        pref = self._prefixo[regiao]
        return pref[b] - pref[a]

    def _limites(self, regiao: str, inicio: datetime, fim: datetime) -> tuple[int, int]:
        self._exigir_regiao(regiao)
        if fim < inicio:
            raise ValueError("fim anterior ao início")
        ts = self._ts[regiao]
        return bisect_left(ts, inicio), bisect_right(ts, fim)

    def _exigir_regiao(self, regiao: str) -> None:
        if regiao not in self.por_regiao:
            raise KeyError(f"região desconhecida: {regiao}")
