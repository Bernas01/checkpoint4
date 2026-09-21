"""Geração reprodutível dos dados de energia (Questão 2) e função de criticidade.

Modelo sintético (documentado para reprodutibilidade):
  consumo(t)    = base_r · perfil_diário(h) · fator_semana(t) · onda_calor(t) · ruído N(1, 0.03)
  perfil_diário = 1 + 0.22·sin(2π(h − 13)/24) + 0.10·[18h ≤ h ≤ 21h]   (pico no início da noite)
  capacidade(t) = cap_r · (1 + solar_r · max(0, sin(π(h − 6)/12)))     (renováveis ao meio-dia)
                  · (1 − 0.12 se houver indisponibilidade de geração)
  ondas de calor: blocos de 24–72 h com +8 a +15% de consumo
  prioridade    = 5 quando há cargas essenciais em contingência, senão 1–4
  custo (R$/MWh)= 180 + 420·max(0, carga − 0.75)² ·10 + ruído  (preço sobe com a carga)

Resultado: a "curva do pato" — sobra capacidade ao meio-dia (solar) e ela
aperta no começo da noite, quando o consumo é máximo e o solar é zero.
"""
from __future__ import annotations

import csv
import math
import random
from datetime import datetime, timedelta
from pathlib import Path

from .config import DATA_DIR, SEED
from .estruturas import Registro

REGIOES = {
    "Norte": (620, 880, 0.10),
    "Nordeste": (1350, 1840, 0.30),
    "Centro-Oeste": (780, 1100, 0.18),
    "Sudeste": (3900, 5350, 0.15),
    "Sul": (1500, 2080, 0.12),
}
INICIO = datetime(2026, 1, 5, 0, 0)
ARQ = "problema2.csv"

LIMIAR_CARGA = 0.88
PESO_CARGA = 100.0
PESO_EXCESSO = 300.0
PESO_PRIORIDADE = 2.0
PESO_CUSTO = 5.0
CUSTO_REF = 250.0


def criticidade(r: Registro) -> float:
    """Criticidade de uma hora (pode ser negativa = hora "folgada").

    crit = 100·(carga − 0.88) + 300·max(0, carga − 1) + 2·(prioridade − 3)
           + 5·(custo/250 − 1)

    Ser negativa em horas tranquilas é essencial: um intervalo crítico só
    "vale a pena" estender enquanto o acumulado continuar crescendo. Se todos os
    valores fossem positivos, a resposta trivial seria a série inteira.
    """
    carga = r.consumo / r.capacidade
    return (PESO_CARGA * (carga - LIMIAR_CARGA)
            + PESO_EXCESSO * max(0.0, carga - 1.0)
            + PESO_PRIORIDADE * (r.prioridade - 3)
            + PESO_CUSTO * (r.custo / CUSTO_REF - 1))


def serie_criticidade(registros: list[Registro]) -> list[float]:
    return [criticidade(r) for r in registros]


def _eventos(rng: random.Random, n_horas: int, taxa_por_semana: float, dur_min: int, dur_max: int) -> set[int]:
    horas: set[int] = set()
    n_eventos = max(1, round(n_horas / 168 * taxa_por_semana))
    for _ in range(n_eventos):
        ini = rng.randrange(0, max(1, n_horas - dur_min))
        horas.update(range(ini, min(n_horas, ini + rng.randint(dur_min, dur_max))))
    return horas


def gerar_regiao(regiao: str, n_horas: int, rng: random.Random, inicio: datetime = INICIO) -> list[Registro]:
    if regiao not in REGIOES:
        raise KeyError(f"região desconhecida: {regiao}")
    if n_horas <= 0:
        raise ValueError("n_horas deve ser positivo")
    base, cap, solar = REGIOES[regiao]
    calor = _eventos(rng, n_horas, 1.0, 24, 72)
    falha = _eventos(rng, n_horas, 0.6, 3, 10)
    reg = []
    for t in range(n_horas):
        ts = inicio + timedelta(hours=t)
        h = ts.hour
        perfil = 1 + 0.22 * math.sin(2 * math.pi * (h - 13) / 24) + (0.10 if 18 <= h <= 21 else 0)
        semana = 0.93 if ts.weekday() >= 5 else 1.0
        onda = 1 + rng.uniform(0.08, 0.15) if t in calor else 1.0
        consumo = base * perfil * semana * onda * rng.gauss(1, 0.03)
        capacidade = cap * (1 + solar * max(0.0, math.sin(math.pi * (h - 6) / 12)))
        if t in falha:
            capacidade *= 0.88
        carga = consumo / capacidade
        prioridade = 5 if (t in falha and carga > 0.95) else rng.choices([1, 2, 3, 4], [2, 4, 3, 1])[0]
        custo = 180 + 4200 * max(0.0, carga - 0.75) ** 2 + rng.uniform(-15, 15)
        reg.append(Registro(ts, regiao, round(consumo, 2), round(capacidade, 2), prioridade, round(custo, 2)))
    return reg


def gerar_dados(n_horas: int = 336, seed: int = SEED, regioes: list[str] | None = None) -> list[Registro]:
    """n_horas por região. Padrão: 14 dias × 5 regiões = 1.680 observações."""
    rng = random.Random(seed)
    saida: list[Registro] = []
    for regiao in regioes or list(REGIOES):
        saida.extend(gerar_regiao(regiao, n_horas, rng))
    return saida


def gerar_serie_escalabilidade(n: int, seed: int = SEED, regiao: str = "Sudeste") -> list[float]:
    """Série de criticidade com exatamente n horas (experimento da Parte D)."""
    rng = random.Random(seed * 1000 + n)
    return serie_criticidade(gerar_regiao(regiao, n, rng))


def salvar_csv(registros: list[Registro], pasta: Path = DATA_DIR) -> Path:
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / ARQ
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(Registro._fields)
        for r in registros:
            w.writerow([r.timestamp.isoformat(), r.regiao, r.consumo, r.capacidade, r.prioridade, r.custo])
    return caminho


def carregar_csv(pasta: Path = DATA_DIR) -> list[Registro]:
    with open(pasta / ARQ, encoding="utf-8") as f:
        return [
            Registro(datetime.fromisoformat(l["timestamp"]), l["regiao"], float(l["consumo"]),
                     float(l["capacidade"]), int(l["prioridade"]), float(l["custo"]))
            for l in csv.DictReader(f)
        ]
