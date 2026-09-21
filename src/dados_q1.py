"""Geração, gravação e leitura da instância da Questão 1.

Geração reprodutível: tudo deriva de ``random.Random(seed)``.
Modelo espacial: pontos num quadrado 100 x 100 km; cada ponto é ligado aos
seus vizinhos mais próximos (malha viária plausível, grafo esparso). O peso
de uma via é a distância euclidiana x fator de sinuosidade (1.0–1.35).
Uma fração das vias é marcada como bloqueada (enchente/deslizamento).
"""
from __future__ import annotations

import csv
import json
import math
import random
from pathlib import Path

from .config import DATA_DIR, SEED
from .estruturas import Grafo, Ponto, calcular_beneficio

NOMES = [
    "Vila Esperança", "Jardim das Águas", "Morro Alto", "Baixada Sul", "Vale Verde",
    "Parque Ribeirinho", "Centro Velho", "Vila Operária", "Jardim Primavera", "Alto da Serra",
    "Ponte Nova", "Barra Funda", "Capão Seco", "Recanto dos Rios", "Vila Nova",
    "Campo Limpo", "Várzea Grande", "Lagoa Azul", "Encosta Norte", "Porto Velho",
    "Vila Aurora", "Monte Belo", "Jardim Europa", "Beira-Rio", "Chácara Flora",
]

ARQ_PONTOS = "problema1_pontos.csv"
ARQ_ARESTAS = "problema1.csv"
ARQ_PARAMETROS = "problema1_parametros.json"


def gerar_instancia(
    seed: int = SEED,
    n_pontos: int = 20,
    vizinhos_por_ponto: int = 3,
    min_arestas: int = 35,
    fracao_bloqueada: float = 0.15,
    fracao_capacidade: float = 0.45,
) -> tuple[Grafo, int]:
    """Cria o grafo e a capacidade do veículo. Retorna (grafo, capacidade)."""
    if n_pontos < 2 or n_pontos > len(NOMES):
        raise ValueError(f"n_pontos deve estar entre 2 e {len(NOMES)}")
    rng = random.Random(seed)
    grafo = Grafo()
    grafo.adicionar_ponto(Ponto(0, "Centro de Distribuição", 50.0, 50.0, 0, 1, 0, 0, eh_centro=True))

    coords: list[tuple[float, float]] = [(50.0, 50.0)]
    while len(coords) < n_pontos + 1:
        x, y = rng.uniform(3, 97), rng.uniform(3, 97)
        if all(math.dist((x, y), c) >= 9 for c in coords):
            coords.append((round(x, 1), round(y, 1)))

    for i in range(1, n_pontos + 1):
        pessoas = rng.randint(80, 1500)
        prioridade = rng.choices([1, 2, 3, 4, 5], weights=[1, 2, 3, 2, 2])[0]
        demanda = max(5, round(pessoas / 40) + rng.randint(0, 12))
        x, y = coords[i]
        grafo.adicionar_ponto(
            Ponto(i, NOMES[i - 1], x, y, pessoas, prioridade, demanda, calcular_beneficio(pessoas, prioridade))
        )

    pares = _pares_mais_proximos(coords, vizinhos_por_ponto, min_arestas)
    n_bloq = max(1, round(len(pares) * fracao_bloqueada))
    bloqueadas = set(rng.sample(range(len(pares)), n_bloq))
    for k, (u, v) in enumerate(pares):
        peso = round(math.dist(coords[u], coords[v]) * rng.uniform(1.0, 1.35), 1)
        grafo.adicionar_aresta(u, v, peso, bloqueada=k in bloqueadas)

    demanda_total = sum(p.demanda for p in grafo.pontos_atendimento())
    capacidade = round(demanda_total * fracao_capacidade)
    return grafo, capacidade


def _pares_mais_proximos(coords, k: int, minimo: int) -> list[tuple[int, int]]:
    """Liga cada vértice aos k mais próximos; aumenta k até ter ``minimo`` arestas."""
    n = len(coords)
    while True:
        pares = set()
        for u in range(n):
            ordem = sorted((math.dist(coords[u], coords[v]), v) for v in range(n) if v != u)
            for _, v in ordem[:k]:
                pares.add((min(u, v), max(u, v)))
        if len(pares) >= minimo:
            return sorted(pares)
        k += 1


def salvar_instancia(grafo: Grafo, capacidade: int, pasta: Path = DATA_DIR, seed: int = SEED) -> None:
    pasta.mkdir(parents=True, exist_ok=True)
    with open(pasta / ARQ_PONTOS, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "nome", "x", "y", "pessoas", "prioridade", "demanda", "beneficio", "tipo"])
        for p in grafo.pontos.values():
            w.writerow([p.id, p.nome, p.x, p.y, p.pessoas, p.prioridade, p.demanda, p.beneficio,
                        "centro" if p.eh_centro else "atendimento"])
    with open(pasta / ARQ_ARESTAS, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["origem", "destino", "distancia_km", "bloqueada"])
        for u, v, peso, bloq in grafo.arestas():
            w.writerow([u, v, peso, int(bloq)])
    with open(pasta / ARQ_PARAMETROS, "w", encoding="utf-8") as f:
        json.dump({"seed": seed, "capacidade_veiculo": capacidade,
                   "unidade_capacidade": "kits de suprimentos"}, f, indent=2, ensure_ascii=False)


def carregar_instancia(pasta: Path = DATA_DIR) -> tuple[Grafo, int]:
    grafo = Grafo()
    with open(pasta / ARQ_PONTOS, encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            grafo.adicionar_ponto(Ponto(
                int(linha["id"]), linha["nome"], float(linha["x"]), float(linha["y"]),
                int(linha["pessoas"]), int(linha["prioridade"]), int(linha["demanda"]),
                int(linha["beneficio"]), linha["tipo"] == "centro",
            ))
    with open(pasta / ARQ_ARESTAS, encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            grafo.adicionar_aresta(int(linha["origem"]), int(linha["destino"]),
                                   float(linha["distancia_km"]), linha["bloqueada"] == "1")
    with open(pasta / ARQ_PARAMETROS, encoding="utf-8") as f:
        capacidade = int(json.load(f)["capacidade_veiculo"])
    return grafo, capacidade
