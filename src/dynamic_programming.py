"""Parte C (Questão 1) — Programação Dinâmica (mochila 0/1).

Modelo: cada região candidata i tem peso w_i = demanda (kits) e valor
v_i = benefício. O veículo leva no máximo C kits.

1. ESTADO     DP[i][c] = maior benefício possível usando apenas as i primeiras
              regiões candidatas e no máximo c kits de capacidade.
2. DECISÃO    para a região i: NÃO atender (herda DP[i-1][c]) ou ATENDER
              (ganha v_i e ocupa w_i kits: DP[i-1][c - w_i] + v_i), possível
              apenas se w_i <= c.
3. CASO-BASE  DP[0][c] = 0 para todo c (nenhuma região considerada) e
              DP[i][0] = 0 (sem capacidade nada é atendido; decorre da regra).
4. RECORRÊNCIA
              DP[i][c] = DP[i-1][c]                               se w_i > c
              DP[i][c] = max(DP[i-1][c], DP[i-1][c-w_i] + v_i)    caso contrário
5. RECONSTRUÇÃO
              Parte de (N, C). Se DP[i][c] != DP[i-1][c], o valor só pode ter
              vindo da opção "atender": registra i e faz c -= w_i. Repete para
              i = N..1. O conjunto registrado é a solução ótima.

Por que funciona (subestrutura ótima): numa solução ótima para (i, c), ou i
fica de fora — e o resto é ótimo para (i-1, c) — ou i entra — e o resto é
ótimo para (i-1, c-w_i). Qualquer outra combinação poderia ser trocada por uma
melhor. Os subproblemas se repetem (muitos caminhos chegam ao mesmo (i, c)),
por isso a tabela evita recomputação exponencial.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple, Sequence


class Item(NamedTuple):
    id: int
    peso: int
    valor: int


class Decisao(NamedTuple):
    i: int
    c: int
    atendeu: bool


@dataclass
class ResultadoDP:
    selecionados: list[int]
    beneficio: int
    peso_usado: int
    tabela: list[list[int]]
    decisoes: list[Decisao]
    itens: list[Item]


def validar_itens(itens: Sequence[Item], capacidade: int) -> None:
    if capacidade < 0:
        raise ValueError("capacidade não pode ser negativa")
    if not isinstance(capacidade, int):
        raise TypeError("capacidade deve ser inteira (a tabela é indexada por c)")
    for it in itens:
        if it.peso <= 0 or it.valor < 0:
            raise ValueError(f"item inválido: {it}")


def preencher_tabela(itens: Sequence[Item], capacidade: int) -> list[list[int]]:
    """Preenche DP[0..N][0..C] linha a linha (bottom-up)."""
    n = len(itens)
    dp = [[0] * (capacidade + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        peso, valor = itens[i - 1].peso, itens[i - 1].valor
        anterior, linha = dp[i - 1], dp[i]
        for c in range(capacidade + 1):
            linha[c] = anterior[c]
            if peso <= c and anterior[c - peso] + valor > linha[c]:
                linha[c] = anterior[c - peso] + valor
    return dp


def reconstruir(dp: list[list[int]], itens: Sequence[Item], capacidade: int) -> tuple[list[int], list[Decisao]]:
    selecionados, decisoes, c = [], [], capacidade
    for i in range(len(itens), 0, -1):
        atendeu = dp[i][c] != dp[i - 1][c]
        decisoes.append(Decisao(i, c, atendeu))
        if atendeu:
            selecionados.append(itens[i - 1].id)
            c -= itens[i - 1].peso
    return selecionados[::-1], decisoes


def mochila_dp(itens: Sequence[Item], capacidade: int) -> ResultadoDP:
    validar_itens(itens, capacidade)
    itens = list(itens)
    dp = preencher_tabela(itens, capacidade)
    selecionados, decisoes = reconstruir(dp, itens, capacidade)
    por_id = {it.id: it for it in itens}
    peso = sum(por_id[i].peso for i in selecionados)
    return ResultadoDP(selecionados, dp[-1][-1], peso, dp, decisoes, itens)


def mochila_dp_1d(itens: Sequence[Item], capacidade: int) -> int:
    """Variante O(C) de memória: só o valor ótimo (não permite reconstrução).

    Percorre c de C para 0 para que DP[c - w] ainda seja o valor da linha
    anterior. Usada para discutir o trade-off memória × reconstrução.
    """
    validar_itens(itens, capacidade)
    dp = [0] * (capacidade + 1)
    for it in itens:
        for c in range(capacidade, it.peso - 1, -1):
            dp[c] = max(dp[c], dp[c - it.peso] + it.valor)
    return dp[capacidade]
