"""Questão 2, Parte C — Dividir e Conquistar para o intervalo mais crítico.

    DIVIDE        meio = (lo + hi) // 2  →  [lo, meio] e [meio+1, hi]
    SOLVE LEFT    melhor intervalo inteiramente à esquerda (recursão)
    SOLVE RIGHT   melhor intervalo inteiramente à direita  (recursão)
    SOLVE CROSSING melhor intervalo que CONTÉM meio e meio+1
    COMBINE       o maior dos três

Caso-base: lo == hi → o único intervalo possível é [lo, lo].

Caso que atravessa: todo intervalo que cruza a divisão é a união de um
sufixo da metade esquerda terminando em ``meio`` e de um prefixo da metade
direita começando em ``meio+1``. As duas partes são independentes, então
basta o MELHOR sufixo (varrendo de meio até lo) + o MELHOR prefixo
(varrendo de meio+1 até hi): O(hi - lo + 1) operações.

Recorrência: T(n) = 2T(n/2) + Θ(n)  →  Θ(n log n)  (Teorema Mestre, caso 2).
Espaço: pilha de recursão com profundidade ⌈log₂ n⌉ → O(log n).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from .brute_force import Intervalo, validar_serie
from .metricas import Contador


@dataclass
class NoDecomposicao:
    """Nó da árvore de recursão (guardado só até ``profundidade_registro``)."""

    lo: int
    hi: int
    profundidade: int
    melhor: Intervalo | None = None
    esquerda_melhor: Intervalo | None = None
    direita_melhor: Intervalo | None = None
    cruzamento: Intervalo | None = None
    origem: str = "base"
    filhos: list["NoDecomposicao"] = field(default_factory=list)


def intervalo_cruzamento(valores: Sequence[float], lo: int, meio: int, hi: int, contador: Contador) -> Intervalo:
    """Melhor intervalo que contém obrigatoriamente meio e meio+1."""
    soma, melhor_esq, inicio = 0.0, float("-inf"), meio
    for i in range(meio, lo - 1, -1):
        soma += valores[i]
        contador.add()
        if soma > melhor_esq:
            melhor_esq, inicio = soma, i
    soma, melhor_dir, fim = 0.0, float("-inf"), meio + 1
    for j in range(meio + 1, hi + 1):
        soma += valores[j]
        contador.add()
        if soma > melhor_dir:
            melhor_dir, fim = soma, j
    return Intervalo(inicio, fim, melhor_esq + melhor_dir)


def _resolver(valores, lo, hi, prof, contador, prof_registro) -> tuple[Intervalo, NoDecomposicao | None]:
    registrar = prof <= prof_registro
    if lo == hi:
        contador.add()
        base = Intervalo(lo, lo, valores[lo])
        return base, (NoDecomposicao(lo, hi, prof, base) if registrar else None)

    meio = (lo + hi) // 2
    esq, no_esq = _resolver(valores, lo, meio, prof + 1, contador, prof_registro)
    dir_, no_dir = _resolver(valores, meio + 1, hi, prof + 1, contador, prof_registro)
    cruz = intervalo_cruzamento(valores, lo, meio, hi, contador)
    melhor, origem = esq, "esquerda"
    if dir_.soma > melhor.soma:
        melhor, origem = dir_, "direita"
    if cruz.soma > melhor.soma:
        melhor, origem = cruz, "cruzamento"

    no = None
    if registrar:
        no = NoDecomposicao(lo, hi, prof, melhor, esq, dir_, cruz, origem,
                            [n for n in (no_esq, no_dir) if n is not None])
    return melhor, no


def intervalo_critico_dc(
    valores: Sequence[float],
    contador: Contador | None = None,
    profundidade_registro: int = -1,
) -> tuple[Intervalo, NoDecomposicao | None]:
    """Resolve o problema e, opcionalmente, registra a árvore até a profundidade dada.

    ``profundidade_registro = 3`` guarda 4 níveis (0..3) para a Figura 2.
    O registro não altera a complexidade assintótica (no máximo 2^(p+1) nós).
    """
    validar_serie(valores)
    contador = contador or Contador()
    dados = valores if isinstance(valores, list) else list(valores)
    return _resolver(dados, 0, len(dados) - 1, 0, contador, profundidade_registro)
