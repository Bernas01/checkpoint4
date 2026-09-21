"""Figuras da Questão 1 (geradas a partir dos resultados reais)."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from .caminhos import MatrizDistancias
from .estruturas import Grafo

CORES_PRIORIDADE = {1: "#9ecae1", 2: "#6baed6", 3: "#fdae6b", 4: "#f16913", 5: "#a50f15"}


def _desenhar_arestas(ax, g: Grafo, rotulos: bool = True, alpha: float = 1.0) -> None:
    for u, v, peso, bloq in g.arestas():
        pu, pv = g.pontos[u], g.pontos[v]
        estilo = dict(color="#d62728", ls="--", lw=1.4) if bloq else dict(color="#9a9a9a", ls="-", lw=1.0)
        ax.plot([pu.x, pv.x], [pu.y, pv.y], zorder=1, alpha=alpha, **estilo)
        mx, my = (pu.x + pv.x) / 2, (pu.y + pv.y) / 2
        if bloq:
            ax.text(mx, my, "✕", color="#d62728", ha="center", va="center", fontsize=11, zorder=3, alpha=alpha)
        elif rotulos:
            ax.text(mx, my, f"{peso:g}", fontsize=6.5, ha="center", va="center", zorder=2, alpha=alpha,
                    bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.8))


def figura_grafo(g: Grafo, capacidade: int, destino: Path) -> Path:
    fig, ax = plt.subplots(figsize=(13, 10))
    _desenhar_arestas(ax, g)
    for p in g.pontos.values():
        if p.eh_centro:
            ax.scatter(p.x, p.y, s=500, marker="s", c="#2ca02c", edgecolors="black", zorder=4)
            ax.annotate("CD", (p.x, p.y), ha="center", va="center", color="white", weight="bold", zorder=5)
            continue
        ax.scatter(p.x, p.y, s=60 + p.pessoas / 4, c=CORES_PRIORIDADE[p.prioridade], edgecolors="black", zorder=4)
        ax.annotate(f"{p.id}", (p.x, p.y), ha="center", va="center", fontsize=8, weight="bold", zorder=5)
        ax.annotate(f"{p.nome}\nd={p.demanda} b={p.beneficio}", (p.x, p.y), xytext=(0, -20),
                    textcoords="offset points", ha="center", fontsize=6.5, zorder=5)
    legenda = [Line2D([], [], marker="s", ls="", mfc="#2ca02c", mec="black", ms=12, label="Centro de distribuição"),
               Line2D([], [], color="#9a9a9a", label="Via disponível (peso = km)"),
               Line2D([], [], color="#d62728", ls="--", label="Via bloqueada ✕")]
    legenda += [Line2D([], [], marker="o", ls="", mfc=c, mec="black", ms=9, label=f"Prioridade {k}")
                for k, c in CORES_PRIORIDADE.items()]
    ax.legend(handles=legenda, loc="upper left", bbox_to_anchor=(1.01, 1), fontsize=9, framealpha=0.9)
    ax.set_title(f"Figura 1 — Rede de atendimento: V={g.num_vertices}, E={g.num_arestas} "
                 f"({g.num_bloqueadas} bloqueadas), capacidade do veículo C={capacidade} kits\n"
                 "tamanho do círculo ∝ pessoas afetadas; d = demanda (kits), b = benefício")
    ax.set_xlabel("x (km)"); ax.set_ylabel("y (km)"); ax.set_aspect("equal")
    return _salvar(fig, destino)


def _desenhar_rota(ax, g: Grafo, ordem: list[int], matriz: MatrizDistancias, cor: str) -> None:
    sequencia = [g.centro, *ordem, g.centro]
    for passo, (a, b) in enumerate(zip(sequencia, sequencia[1:]), start=1):
        caminho = matriz.caminho(a, b)
        for u, v in zip(caminho, caminho[1:]):
            pu, pv = g.pontos[u], g.pontos[v]
            ax.annotate("", xy=(pv.x, pv.y), xytext=(pu.x, pu.y), zorder=3,
                        arrowprops=dict(arrowstyle="-|>", color=cor, lw=2.2, alpha=0.8, shrinkA=8, shrinkB=8))
        if b != g.centro:
            p = g.pontos[b]
            ax.annotate(f"#{passo}", (p.x, p.y), xytext=(10, 8), textcoords="offset points",
                        color=cor, weight="bold", fontsize=10, zorder=6)


def _painel_solucao(ax, g, ordem, matriz, titulo, cor) -> None:
    _desenhar_arestas(ax, g, rotulos=False, alpha=0.45)
    atendidos = set(ordem)
    for p in g.pontos.values():
        if p.eh_centro:
            ax.scatter(p.x, p.y, s=450, marker="s", c="#2ca02c", edgecolors="black", zorder=4)
            continue
        cor_no = "#31a354" if p.id in atendidos else "#d9d9d9"
        ax.scatter(p.x, p.y, s=260, c=cor_no, edgecolors="black", zorder=4)
        ax.annotate(str(p.id), (p.x, p.y), ha="center", va="center", fontsize=8, weight="bold", zorder=5)
    _desenhar_rota(ax, g, ordem, matriz, cor)
    ax.set_title(titulo, fontsize=10); ax.set_aspect("equal")


def figura_solucao(g, matriz, guloso, dp_ordem, dp_resultado, dp_distancia, capacidade, destino: Path) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(18, 9))
    _painel_solucao(axes[0], g, guloso.ordem, matriz,
                    f"GREEDY — benefício {guloso.beneficio}, carga {guloso.carga_usada}/{capacidade} kits, "
                    f"rota {guloso.distancia_total:.0f} km\nordem = {guloso.ordem}", "#1f77b4")
    _painel_solucao(axes[1], g, dp_ordem, matriz,
                    f"PROGRAMAÇÃO DINÂMICA — benefício {dp_resultado.beneficio}, carga "
                    f"{dp_resultado.peso_usado}/{capacidade} kits, rota {dp_distancia:.0f} km\n"
                    f"conjunto ótimo = {sorted(dp_resultado.selecionados)} (visitado por vizinho mais próximo)",
                    "#9467bd")
    legenda = [Line2D([], [], marker="o", ls="", mfc="#31a354", mec="black", ms=12, label="Atendido"),
               Line2D([], [], marker="o", ls="", mfc="#d9d9d9", mec="black", ms=12, label="Não atendido"),
               Line2D([], [], color="#d62728", ls="--", label="Via bloqueada"),
               Line2D([], [], color="black", marker=">", label="Sequência (#k = k-ésima entrega)")]
    fig.legend(handles=legenda, loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=4, fontsize=10)
    fig.suptitle("Figura 2 — Locais atendidos e sequência de atendimento (setas seguem os caminhos mínimos de Dijkstra)",
                 fontsize=13)
    return _salvar(fig, destino)


def figura_dp(resultado, nomes: dict[int, str], curva_guloso: list[int], destino: Path) -> Path:
    tabela, itens = resultado.tabela, resultado.itens
    n, cap = len(itens), len(tabela[0]) - 1
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 11), gridspec_kw={"height_ratios": [1.3, 1]})
    im = ax1.imshow(tabela, aspect="auto", cmap="viridis", origin="upper", interpolation="nearest")
    fig.colorbar(im, ax=ax1, label="DP[i][c] = melhor benefício")
    for d in resultado.decisoes:
        if d.atendeu:
            ax1.scatter(d.c, d.i, marker="o", s=45, c="#ff4136", edgecolors="black", linewidths=0.6, zorder=3)
        else:
            ax1.scatter(d.c, d.i, marker="x", s=45, c="white", linewidths=1.2, zorder=3)
    ax1.set_yticks(range(n + 1))
    ax1.set_yticklabels(["0 (caso-base)"] + [f"{i}: pt {it.id} (w={it.peso}, v={it.valor})"
                                             for i, it in enumerate(itens, start=1)], fontsize=7)
    ax1.set_xlabel("capacidade c (kits)"); ax1.set_ylabel("i = regiões consideradas")
    ax1.set_title("Figura 3a — Tabela DP[i][c] e reconstrução a partir de (N, C): "
                  "● vermelho = atendeu (DP[i][c] ≠ DP[i-1][c], c -= w_i), ✕ = não atendeu")
    ax2.step(range(cap + 1), tabela[-1], where="post", color="#9467bd", lw=2, label="DP — ótimo DP[N][c]")
    ax2.step(range(cap + 1), curva_guloso, where="post", color="#1f77b4", lw=1.5, ls="--",
             label="Greedy (benefício/kit, sem distância)")
    diff = [c for c in range(cap + 1) if curva_guloso[c] < tabela[-1][c]]
    ax2.fill_between(range(cap + 1), curva_guloso, tabela[-1], step="post", color="#ff7f0e", alpha=0.3,
                     label=f"perda do Greedy ({len(diff)} de {cap + 1} capacidades)")
    ax2.set_xlabel("capacidade disponível c (kits)"); ax2.set_ylabel("benefício total")
    ax2.set_title("Figura 3b — Evolução do benefício ótimo com a capacidade (última linha da tabela) × Greedy")
    ax2.legend(); ax2.grid(alpha=0.3)
    return _salvar(fig, destino)


def figura_varredura(varredura: list[dict], destino: Path) -> Path:
    caps = [v["capacidade"] for v in varredura]
    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.plot(caps, [v["dp"] for v in varredura], "o-", color="#9467bd", label="DP (ótimo)")
    ax.plot(caps, [v["guloso_densidade"] for v in varredura], "s--", color="#1f77b4", label="Greedy benefício/kit")
    ax.plot(caps, [v["guloso_distancia"] for v in varredura], "^:", color="#ff7f0e", label="Greedy com distância")
    ax.set_xlabel("capacidade do veículo (kits)"); ax.set_ylabel("benefício total")
    ax.set_title("Figura 4 — Greedy × DP para capacidades de 5% a 100% da demanda total")
    ax.grid(alpha=0.3); ax.legend()
    return _salvar(fig, destino)


def figura_contraexemplo(guloso, dp, destino: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    barras = ax.bar(["Greedy", "DP (ótimo)"], [guloso.beneficio, dp.beneficio], color=["#1f77b4", "#9467bd"])
    ax.bar_label(barras, labels=[f"{guloso.beneficio}\natende {guloso.ordem}\nusa {guloso.carga_usada}/10 kits",
                                 f"{dp.beneficio}\natende {dp.selecionados}\nusa {dp.peso_usado}/10 kits"],
                 padding=3, fontsize=9)
    ax.set_ylim(0, dp.beneficio * 1.45); ax.set_ylabel("benefício")
    ax.set_title("Figura 5 — Contraexemplo: A (6 kits, 36) × B, C (5 kits, 27 cada), C = 10")
    return _salvar(fig, destino)


def _salvar(fig, destino: Path) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(destino, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return destino
