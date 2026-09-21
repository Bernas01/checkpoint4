"""Questão 2, Parte D — experimento de escalabilidade.

Para cada n: gera uma série de n horas (SEED fixa), mede
  * tempo médio (time.perf_counter, várias repetições);
  * operações relevantes (Contador);
  * pico de memória alocada (tracemalloc, em execução separada para não
    distorcer o tempo).
Também registra as razões tempo/n² e tempo/(n·log₂n): se a análise
assintótica estiver certa, a razão correspondente fica aproximadamente
constante enquanto a outra varia.
"""
from __future__ import annotations

import math
import statistics
import time
import tracemalloc
from typing import Callable, Sequence

from .brute_force import intervalo_critico_forca_bruta
from .config import SEED
from .dados_q2 import gerar_serie_escalabilidade
from .divide_conquer import intervalo_critico_dc
from .metricas import Contador

TAMANHOS = [100, 250, 500, 1000, 2000, 5000]


def _forca_bruta(v, c):
    return intervalo_critico_forca_bruta(v, c)


def _dc(v, c):
    return intervalo_critico_dc(v, c)[0]


ALGORITMOS: dict[str, Callable] = {"forca_bruta": _forca_bruta, "dividir_conquistar": _dc}


def medir(algoritmo: Callable, valores: Sequence[float], repeticoes: int) -> dict:
    tempos = []
    for _ in range(repeticoes):
        inicio = time.perf_counter()
        algoritmo(valores, Contador())
        tempos.append(time.perf_counter() - inicio)
    contador = Contador()
    tracemalloc.start()
    resultado = algoritmo(valores, contador)
    _, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {"tempo_s": statistics.mean(tempos), "desvio_s": statistics.pstdev(tempos),
            "operacoes": contador.operacoes, "memoria_pico_kb": pico / 1024, "soma": resultado.soma}


def rodar(tamanhos: Sequence[int] = TAMANHOS, seed: int = SEED, rep_fb: int = 3, rep_dc: int = 7) -> list[dict]:
    linhas = []
    for n in tamanhos:
        valores = gerar_serie_escalabilidade(n, seed)
        for nome, alg in ALGORITMOS.items():
            m = medir(alg, valores, rep_fb if nome == "forca_bruta" else rep_dc)
            m.update(algoritmo=nome, n=n,
                     tempo_por_n2_ns=m["tempo_s"] / n ** 2 * 1e9,
                     tempo_por_nlogn_ns=m["tempo_s"] / (n * math.log2(n)) * 1e9)
            linhas.append(m)
            print(f"  n={n:>5} {nome:<19} {m['tempo_s']*1000:>10.2f} ms  ops={m['operacoes']:>11,}  "
                  f"mem={m['memoria_pico_kb']:>8.1f} KB")
        somas = {l["soma"] for l in linhas if l["n"] == n}
        assert len({round(s, 6) for s in somas}) == 1, "algoritmos divergiram!"
    return linhas


def extrapolar(linhas: list[dict], n_alvo: int = 1_000_000) -> dict[str, float]:
    """Projeta o tempo para n_alvo usando a constante medida no maior n."""
    maior = max(l["n"] for l in linhas)
    fb = next(l for l in linhas if l["n"] == maior and l["algoritmo"] == "forca_bruta")
    dc = next(l for l in linhas if l["n"] == maior and l["algoritmo"] == "dividir_conquistar")
    return {
        "n": n_alvo,
        "forca_bruta_s": fb["tempo_por_n2_ns"] * 1e-9 * n_alvo ** 2,
        "dividir_conquistar_s": dc["tempo_por_nlogn_ns"] * 1e-9 * n_alvo * math.log2(n_alvo),
        "forca_bruta_ops": n_alvo * (n_alvo + 1) // 2,
        "dividir_conquistar_ops_aprox": round(n_alvo * math.log2(n_alvo) + 2 * n_alvo),
        "profundidade_recursao": math.ceil(math.log2(n_alvo)),
    }
