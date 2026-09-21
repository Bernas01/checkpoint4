"""Parte D (Questão 1) — instâncias construídas pelo grupo para comparar Greedy × DP.

CONTRAEXEMPLO (Greedy ≠ ótimo)
------------------------------
Três abrigos à MESMA distância (10 km) do centro; veículo com 10 kits.

    ponto            demanda  benefício  benefício/kit
    A  Escola Estadual    6        36          6.0
    B  Ginásio            5        27          5.4
    C  Igreja             5        27          5.4

Como as distâncias são iguais, o score guloso depende só de benefício/kit.
1º passo: A tem o maior score (6.0 > 5.4) → atende A, sobram 4 kits.
2º passo: B e C pedem 5 kits cada → não cabem. Fim. Benefício = 36.
Ótimo (DP): B + C = 10 kits, benefício 54 (+50%).

Por quê: a escolha de A é localmente a melhor (maior rendimento por kit),
mas deixa 4 kits ociosos que nenhuma outra região consegue aproveitar. O
Greedy nunca desfaz uma decisão; a DP avalia DP[i-1][c - w_i] para todo c e
"enxerga" que abrir mão de A libera exatamente o espaço para B e C.
Em outras palavras: a mochila 0/1 NÃO tem a propriedade da escolha gulosa
(ela só vale na mochila fracionária, onde seria possível levar 4/5 de B).

CASO EM QUE O GREEDY É ÓTIMO
----------------------------
Quando todas as demandas são iguais (w), o problema vira "escolher os ⌊C/w⌋
de maior benefício". Ordenar por benefício/kit = ordenar por benefício, e
trocar qualquer escolhido por um não escolhido nunca aumenta o total
(argumento de troca) → o Greedy é ótimo.
"""
from __future__ import annotations

from .estruturas import Grafo, Ponto


def _grafo_estrela(pontos: list[tuple[str, int, int]], distancia: float = 10.0) -> Grafo:
    g = Grafo()
    g.adicionar_ponto(Ponto(0, "Centro", 0.0, 0.0, 0, 1, 0, 0, eh_centro=True))
    n = len(pontos)
    for i, (nome, demanda, beneficio) in enumerate(pontos, start=1):
        x = distancia * (i - (n + 1) / 2) / max(1, n - 1) * 2
        g.adicionar_ponto(Ponto(i, nome, x, distancia, 0, 3, demanda, beneficio))
        g.adicionar_aresta(0, i, distancia)
    return g


def contraexemplo_guloso() -> tuple[Grafo, int]:
    """Instância em que o Greedy obtém 36 e o ótimo é 54."""
    return _grafo_estrela([("A Escola Estadual", 6, 36), ("B Ginásio", 5, 27), ("C Igreja", 5, 27)]), 10


def caso_guloso_otimo() -> tuple[Grafo, int]:
    """Demandas iguais: o Greedy coincide com a DP."""
    return _grafo_estrela([("A", 10, 50), ("B", 10, 80), ("C", 10, 30), ("D", 10, 70)]), 20
