"""Testes da Questão 1: grafo, Dijkstra, Greedy, DP e contraexemplo."""
import random

import pytest

from src.brute_force import mochila_forca_bruta
from src.caminhos import INF, MatrizDistancias, dijkstra, reconstruir_caminho
from src.contraexemplo import caso_guloso_otimo, contraexemplo_guloso
from src.dados_q1 import carregar_instancia, gerar_instancia, salvar_instancia
from src.dynamic_programming import Item, mochila_dp, mochila_dp_1d
from src.estruturas import Grafo, Ponto, calcular_beneficio
from src.greedy import guloso_atendimento, regioes_candidatas


def grafo_pequeno() -> Grafo:
    """0 —5— 1 —2— 2 ; 0 —10— 2 ; 2 —1— 3 (bloqueada) ; 3 isolado se bloqueado."""
    g = Grafo()
    g.adicionar_ponto(Ponto(0, "CD", 0, 0, 0, 1, 0, 0, eh_centro=True))
    for i, (d, b) in enumerate([(4, 40), (3, 20), (2, 30)], start=1):
        g.adicionar_ponto(Ponto(i, f"P{i}", i, 0, 100, 3, d, b))
    g.adicionar_aresta(0, 1, 5)
    g.adicionar_aresta(1, 2, 2)
    g.adicionar_aresta(0, 2, 10)
    g.adicionar_aresta(2, 3, 1, bloqueada=True)
    return g


def test_dijkstra_prefere_caminho_mais_curto_indireto():
    dist, pred = dijkstra(grafo_pequeno(), 0)
    assert dist[2] == 7
    assert reconstruir_caminho(pred, 0, 2) == [0, 1, 2]


def test_via_bloqueada_torna_ponto_inalcancavel():
    g = grafo_pequeno()
    dist, pred = dijkstra(g, 0)
    assert dist[3] == INF and reconstruir_caminho(pred, 0, 3) == []
    assert [p.id for p in regioes_candidatas(g, MatrizDistancias(g))] == [1, 2]


def test_desbloquear_e_alterar_peso():
    g = grafo_pequeno()
    g.desbloquear(2, 3)
    g.alterar_peso(0, 2, 3)
    dist, _ = dijkstra(g, 0)
    assert dist[2] == 3 and dist[3] == 4


@pytest.mark.parametrize("acao", [
    lambda g: g.adicionar_aresta(0, 1, 3),
    lambda g: g.adicionar_aresta(1, 1, 3),
    lambda g: g.adicionar_aresta(0, 3, -2),
])
def test_arestas_invalidas(acao):
    with pytest.raises(ValueError):
        acao(grafo_pequeno())


def test_vertice_inexistente():
    with pytest.raises(KeyError):
        grafo_pequeno().adicionar_aresta(0, 99, 1)


def test_ponto_invalido():
    with pytest.raises(ValueError):
        Ponto(1, "x", 0, 0, 10, 3, 0, 5)
    with pytest.raises(ValueError):
        calcular_beneficio(100, 9)


def test_instancia_atende_requisitos_minimos(tmp_path):
    g, cap = gerar_instancia(seed=123)
    assert len(g.pontos_atendimento()) >= 20
    assert g.num_arestas >= 35 and g.num_bloqueadas >= 1
    assert g.num_arestas < g.num_vertices * (g.num_vertices - 1) // 2
    salvar_instancia(g, cap, tmp_path, seed=123)
    g2, cap2 = carregar_instancia(tmp_path)
    assert cap2 == cap and g2.arestas() == g.arestas()


def test_mesma_seed_mesma_instancia():
    assert gerar_instancia(7)[0].arestas() == gerar_instancia(7)[0].arestas()
    assert gerar_instancia(7)[0].arestas() != gerar_instancia(8)[0].arestas()


def test_guloso_respeita_capacidade_e_nao_repete():
    g, cap = gerar_instancia(seed=1)
    r = guloso_atendimento(g, cap)
    assert r.carga_usada <= cap
    assert len(r.ordem) == len(set(r.ordem))
    assert r.beneficio == sum(g.pontos[i].beneficio for i in r.ordem)


def test_guloso_capacidade_zero_e_negativa():
    g = grafo_pequeno()
    assert guloso_atendimento(g, 0).ordem == []
    with pytest.raises(ValueError):
        guloso_atendimento(g, -1)


def test_dp_exemplo_classico():
    itens = [Item(1, 10, 60), Item(2, 20, 100), Item(3, 30, 120)]
    r = mochila_dp(itens, 50)
    assert r.beneficio == 220 and sorted(r.selecionados) == [2, 3] and r.peso_usado == 50


def test_dp_casos_base():
    assert mochila_dp([], 10).beneficio == 0
    assert mochila_dp([Item(1, 5, 9)], 0).beneficio == 0
    assert mochila_dp([Item(1, 5, 9)], 4).selecionados == []


def test_dp_igual_forca_bruta_em_instancias_aleatorias():
    rng = random.Random(0)
    for _ in range(60):
        itens = [Item(i, rng.randint(1, 15), rng.randint(0, 50)) for i in range(rng.randint(1, 10))]
        cap = rng.randint(0, 40)
        dp = mochila_dp(itens, cap)
        valor_fb, _ = mochila_forca_bruta(itens, cap)
        assert dp.beneficio == valor_fb == mochila_dp_1d(itens, cap)
        assert dp.peso_usado <= cap
        assert sum(it.valor for it in itens if it.id in dp.selecionados) == dp.beneficio


def test_dp_entradas_invalidas():
    with pytest.raises(ValueError):
        mochila_dp([Item(1, 0, 5)], 10)
    with pytest.raises(ValueError):
        mochila_dp([Item(1, 2, 5)], -1)
    with pytest.raises(TypeError):
        mochila_dp([Item(1, 2, 5)], 2.5)


def test_dp_nunca_pior_que_guloso_na_instancia_do_grupo():
    g, cap = carregar_instancia()
    m = MatrizDistancias(g)
    itens = [Item(p.id, p.demanda, p.beneficio) for p in regioes_candidatas(g, m)]
    for c in range(0, cap + 1, 7):
        assert mochila_dp(itens, c).beneficio >= guloso_atendimento(g, c, True, m).beneficio


def test_contraexemplo_guloso_nao_otimo():
    g, cap = contraexemplo_guloso()
    guloso = guloso_atendimento(g, cap)
    itens = [Item(p.id, p.demanda, p.beneficio) for p in g.pontos_atendimento()]
    dp = mochila_dp(itens, cap)
    assert guloso.ordem == [1] and guloso.beneficio == 36
    assert sorted(dp.selecionados) == [2, 3] and dp.beneficio == 54


def test_caso_em_que_guloso_e_otimo():
    g, cap = caso_guloso_otimo()
    itens = [Item(p.id, p.demanda, p.beneficio) for p in g.pontos_atendimento()]
    assert guloso_atendimento(g, cap).beneficio == mochila_dp(itens, cap).beneficio == 150
