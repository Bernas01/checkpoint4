"""Figuras da Questão 2."""
from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from .brute_force import Intervalo
from .divide_conquer import NoDecomposicao
from .estruturas import Registro


def figura_serie(serie: list[Registro], crit: list[float], intervalo: Intervalo, regiao: str, destino: Path) -> Path:
    ts = [r.timestamp for r in serie]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 8), sharex=True, gridspec_kw={"height_ratios": [2, 1]})
    ax1.plot(ts, [r.consumo for r in serie], color="#1f77b4", lw=1.2, label="consumo (MWh)")
    ax1.plot(ts, [r.capacidade for r in serie], color="#2ca02c", lw=1, ls="--", label="capacidade disponível (MW)")
    sobre = [(r.timestamp, r.consumo) for r in serie if r.consumo > r.capacidade]
    if sobre:
        ax1.scatter(*zip(*sobre), s=12, color="#d62728", zorder=3, label="consumo > capacidade")
    a, b = ts[intervalo.inicio], ts[intervalo.fim]
    for ax in (ax1, ax2):
        ax.axvspan(a, b, color="#ff7f0e", alpha=0.3,
                   label=f"intervalo crítico: {a:%d/%m %Hh} → {b:%d/%m %Hh}" if ax is ax1 else None)
    ax1.set_ylabel("MWh / MW"); ax1.legend(loc="upper left", fontsize=9); ax1.grid(alpha=0.3)
    ax1.set_title(f"Figura 1 — Consumo × tempo, região {regiao} ({len(serie)} horas). "
                  f"Criticidade acumulada máxima = {intervalo.soma:.1f} ({intervalo.fim - intervalo.inicio + 1} h)")
    cores = ["#d62728" if c > 0 else "#9ecae1" for c in crit]
    ax2.bar(ts, crit, width=1 / 24, color=cores)
    ax2.axhline(0, color="black", lw=0.6)
    ax2.set_ylabel("criticidade/hora"); ax2.grid(alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    return _salvar(fig, destino)


def figura_decomposicao(raiz: NoDecomposicao, crit: list[float], serie: list[Registro], destino: Path) -> Path:
    niveis: dict[int, list[NoDecomposicao]] = {}
    pilha = [raiz]
    while pilha:
        no = pilha.pop()
        niveis.setdefault(no.profundidade, []).append(no)
        pilha.extend(no.filhos)
    n = len(crit)
    prof_max = max(niveis)
    fig, (ax, axs) = plt.subplots(2, 1, figsize=(17, 10), gridspec_kw={"height_ratios": [3, 1.1]}, sharex=True)
    cor_origem = {"esquerda": "#1f77b4", "direita": "#2ca02c", "cruzamento": "#ff7f0e", "base": "#7f7f7f"}
    for prof, nos in niveis.items():
        y = prof_max - prof
        for no in nos:
            largura = no.hi - no.lo + 1
            caixa = Rectangle((no.lo + largura * 0.02, y + 0.1), largura * 0.96, 0.8,
                              fc=cor_origem[no.origem], alpha=0.25, ec=cor_origem[no.origem], lw=1.5)
            ax.add_patch(caixa)
            m = no.melhor
            t0, t1 = serie[no.lo].timestamp, serie[no.hi].timestamp
            texto = (f"[{no.lo}, {no.hi}]  {t0:%d/%m %Hh}–{t1:%d/%m %Hh}\n"
                     f"melhor [{m.inicio},{m.fim}] = {m.soma:.1f}")
            if no.cruzamento is not None:
                texto += (f"\nE={no.esquerda_melhor.soma:.0f}  D={no.direita_melhor.soma:.0f}  "
                          f"X={no.cruzamento.soma:.0f} → {no.origem.upper()}")
            ax.text(no.lo + largura / 2, y + 0.5, texto, ha="center", va="center", fontsize=6.8 if prof >= 3 else 8.5)
            if no.filhos:
                meio = (no.lo + no.hi) // 2 + 0.5
                ax.plot([meio, meio], [y + 0.1, y + 0.9], color="black", lw=0.8, ls=":")
                for f in no.filhos:
                    ax.plot([no.lo + largura / 2, f.lo + (f.hi - f.lo + 1) / 2], [y + 0.1, y - 0.1], color="#555", lw=0.8)
            ax.plot([m.inicio, m.fim + 1], [y + 0.14, y + 0.14], color="#d62728", lw=3)
    ax.set_xlim(0, n); ax.set_ylim(-0.1, prof_max + 1.05)
    ax.set_yticks([prof_max - p + 0.5 for p in niveis])
    ax.set_yticklabels([f"nível {p}" for p in niveis])
    ax.set_title("Figura 2 — Dividir e Conquistar sobre a série real: 4 níveis da recursão. "
                 "Cor = de onde veio o melhor intervalo do nó (azul = esquerda, verde = direita, laranja = cruza o meio); "
                 "barra vermelha = intervalo vencedor; E/D/X = somas de SOLVE LEFT / SOLVE RIGHT / CROSSING",
                 fontsize=10, wrap=True)
    axs.bar(range(n), crit, width=1.0, color=["#d62728" if c > 0 else "#9ecae1" for c in crit], align="edge")
    axs.axhline(0, color="black", lw=0.5)
    axs.set_ylabel("criticidade"); axs.set_xlabel("índice da hora na série (entrada do algoritmo)")
    for prof in range(min(3, prof_max) + 1):
        for no in niveis.get(prof, []):
            if no.filhos:
                axs.axvline((no.lo + no.hi) // 2 + 1, color="black", lw=1.6 - 0.4 * prof, alpha=0.7)
    return _salvar(fig, destino)


def figura_escalabilidade(linhas: list[dict], destino: Path) -> Path:
    fb = sorted((l for l in linhas if l["algoritmo"] == "forca_bruta"), key=lambda l: l["n"])
    dc = sorted((l for l in linhas if l["algoritmo"] == "dividir_conquistar"), key=lambda l: l["n"])
    ns = [l["n"] for l in fb]
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 5.5))
    for ax, escala in ((ax1, "linear"), (ax2, "log")):
        ax.plot(ns, [l["tempo_s"] * 1000 for l in fb], "o-", color="#d62728", label="Força bruta (medido)")
        ax.plot(ns, [l["tempo_s"] * 1000 for l in dc], "s-", color="#1f77b4", label="Dividir e conquistar (medido)")
        k2 = fb[-1]["tempo_s"] / ns[-1] ** 2
        kn = dc[-1]["tempo_s"] / (ns[-1] * math.log2(ns[-1]))
        ax.plot(ns, [k2 * n ** 2 * 1000 for n in ns], ":", color="#d62728", alpha=0.6, label="c·n² (ajuste)")
        ax.plot(ns, [kn * n * math.log2(n) * 1000 for n in ns], ":", color="#1f77b4", alpha=0.6, label="c·n·log₂n (ajuste)")
        ax.set_xscale(escala); ax.set_yscale(escala)
        ax.set_xlabel("n (horas na série)"); ax.set_ylabel("tempo médio (ms)")
        ax.grid(alpha=0.3, which="both"); ax.legend(fontsize=8)
    ax1.set_title("Figura 3a — Tempo × n (escala linear)")
    ax2.set_title("Figura 3b — escala log-log: inclinação ≈ 2 (FB) e ≈ 1 (D&C)")
    ax3.plot(ns, [l["operacoes"] for l in fb], "o-", color="#d62728", label="Força bruta: n(n+1)/2")
    ax3.plot(ns, [l["operacoes"] for l in dc], "s-", color="#1f77b4", label="D&C: ≈ n·log₂n + n")
    ax3.set_xscale("log"); ax3.set_yscale("log"); ax3.grid(alpha=0.3, which="both")
    ax3.set_xlabel("n"); ax3.set_ylabel("operações contadas"); ax3.legend(fontsize=8)
    ax3.set_title("Figura 3c — Operações relevantes contadas")
    return _salvar(fig, destino)


def _salvar(fig, destino: Path) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(destino, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return destino
