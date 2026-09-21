"""Parte B (Questão 1) — estratégia gulosa para ordem e seleção de atendimentos.

Função de prioridade (score) do candidato i visto a partir da posição atual a:

                 beneficio_i / demanda_i
    score(i) = ---------------------------
                 1 + d(a, i) / d_ref

* Numerador — densidade de benefício: quanto benefício cada kit colocado no
  caminhão gera. A capacidade é o recurso escasso; gastar 1 kit em i "rende"
  beneficio_i/demanda_i. Maximizar essa razão é maximizar o ganho marginal por
  unidade do recurso que limita a solução.
* Denominador — penalidade de deslocamento: d(a, i) é a distância pela malha
  DISPONÍVEL (Dijkstra, vias bloqueadas excluídas). Dividir por (1 + d/d_ref)
  faz um ponto duas vezes mais longe que a média (d = 2·d_ref) valer 1/3 do
  score, como se o benefício "chegasse depois". d_ref = distância média do
  centro aos candidatos, o que torna o termo adimensional.
* Prioridade e número de pessoas entram via benefício
  (pessoas/10 · fator(prioridade)).

Por que é localmente vantajosa: entre os candidatos que ainda cabem no
veículo, é o que entrega mais benefício por unidade dos dois recursos que a
decisão consome agora (espaço no caminhão e tempo de deslocamento).
A decisão nunca é revista — é exatamente isso que a faz falhar em certos
casos (ver Parte D / contraexemplo.py).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .caminhos import INF, MatrizDistancias
from .estruturas import Grafo, Ponto


@dataclass
class PassoGuloso:
    escolhido: int
    score: float
    distancia: float
    capacidade_restante: int
    alternativas_viaveis: int


@dataclass
class ResultadoGuloso:
    ordem: list[int]
    beneficio: int
    carga_usada: int
    distancia_total: float
    passos: list[PassoGuloso] = field(default_factory=list)


def regioes_candidatas(grafo: Grafo, matriz: MatrizDistancias) -> list[Ponto]:
    """Pontos alcançáveis a partir do centro (vias bloqueadas podem isolar regiões)."""
    centro = grafo.centro
    return [p for p in grafo.pontos_atendimento() if matriz.distancia(centro, p.id) < INF]


def score(ponto: Ponto, distancia: float, dist_ref: float, usar_distancia: bool = True) -> float:
    densidade = ponto.beneficio / ponto.demanda
    if not usar_distancia:
        return densidade
    return densidade / (1 + distancia / dist_ref)


def guloso_atendimento(
    grafo: Grafo,
    capacidade: int,
    usar_distancia: bool = True,
    matriz: MatrizDistancias | None = None,
) -> ResultadoGuloso:
    """Constrói a rota passo a passo escolhendo sempre o maior score que ainda cabe."""
    if capacidade < 0:
        raise ValueError("capacidade não pode ser negativa")
    matriz = matriz or MatrizDistancias(grafo)
    centro = grafo.centro
    candidatos = regioes_candidatas(grafo, matriz)
    if not candidatos:
        return ResultadoGuloso([], 0, 0, 0.0)
    dist_ref = sum(matriz.distancia(centro, p.id) for p in candidatos) / len(candidatos)

    restantes = {p.id: p for p in candidatos}
    atual, livre = centro, capacidade
    ordem, passos, distancia_total = [], [], 0.0
    while True:
        viaveis = [p for p in restantes.values()
                   if p.demanda <= livre and matriz.distancia(atual, p.id) < INF]
        if not viaveis:
            break
        melhor = max(viaveis, key=lambda p: (score(p, matriz.distancia(atual, p.id), dist_ref, usar_distancia), -p.id))
        d = matriz.distancia(atual, melhor.id)
        passos.append(PassoGuloso(melhor.id, score(melhor, d, dist_ref, usar_distancia), d, livre, len(viaveis)))
        ordem.append(melhor.id)
        distancia_total += d
        livre -= melhor.demanda
        atual = melhor.id
        del restantes[melhor.id]
    if ordem:
        distancia_total += matriz.distancia(atual, centro)
    beneficio = sum(grafo.pontos[i].beneficio for i in ordem)
    return ResultadoGuloso(ordem, beneficio, capacidade - livre, distancia_total, passos)


def rota_vizinho_mais_proximo(grafo: Grafo, selecionados: list[int], matriz: MatrizDistancias) -> tuple[list[int], float]:
    """Ordena um conjunto já escolhido (ex.: pela DP) visitando sempre o mais próximo.

    Só define a sequência de visita para a Figura 2; não altera o benefício.
    """
    centro = grafo.centro
    faltam, atual, ordem, total = set(selecionados), centro, [], 0.0
    while faltam:
        prox = min(faltam, key=lambda v: (matriz.distancia(atual, v), v))
        total += matriz.distancia(atual, prox)
        ordem.append(prox)
        faltam.remove(prox)
        atual = prox
    if ordem:
        total += matriz.distancia(atual, centro)
    return ordem, total
