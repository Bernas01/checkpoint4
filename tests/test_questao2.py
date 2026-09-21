"""Testes da Questão 2: estruturas, força bruta e dividir e conquistar."""
import random
from datetime import datetime, timedelta

import pytest

from src.brute_force import intervalo_critico_forca_bruta, intervalo_critico_ingenuo
from src.dados_q2 import criticidade, gerar_dados, gerar_serie_escalabilidade
from src.divide_conquer import intervalo_critico_dc
from src.estruturas import IndiceEnergia, Registro
from src.metricas import Contador


@pytest.mark.parametrize("valores, esperado", [
    ([5], 5),
    ([-3, -1, -7], -1),
    ([2, -1, 2, 3, -9, 4], 6),
    ([-2, 1, -3, 4, -1, 2, 1, -5, 4], 6),
    ([1, 2, 3], 6),
])
def test_casos_conhecidos(valores, esperado):
    assert intervalo_critico_forca_bruta(valores).soma == esperado
    assert intervalo_critico_dc(valores)[0].soma == esperado
    assert intervalo_critico_ingenuo(valores).soma == esperado


def test_intervalo_atravessando_a_divisao():
    valores = [-10, -10, 5, 6, 7, 8, -10, -10]
    r, arvore = intervalo_critico_dc(valores, profundidade_registro=0)
    assert (r.inicio, r.fim, r.soma) == (2, 5, 26)
    assert arvore.origem == "cruzamento"


def test_dc_igual_forca_bruta_aleatorio():
    rng = random.Random(42)
    for _ in range(200):
        v = [rng.uniform(-50, 50) for _ in range(rng.randint(1, 60))]
        fb = intervalo_critico_forca_bruta(v)
        dc, _ = intervalo_critico_dc(v)
        assert dc.soma == pytest.approx(fb.soma)
        assert sum(v[dc.inicio:dc.fim + 1]) == pytest.approx(dc.soma)


def test_serie_vazia_invalida():
    with pytest.raises(ValueError):
        intervalo_critico_forca_bruta([])
    with pytest.raises(ValueError):
        intervalo_critico_dc([])


def test_contagem_de_operacoes():
    n = 64
    c_fb, c_dc = Contador(), Contador()
    v = gerar_serie_escalabilidade(n, seed=1)
    intervalo_critico_forca_bruta(v, c_fb)
    intervalo_critico_dc(v, c_dc)
    assert c_fb.operacoes == n * (n + 1) // 2
    assert c_dc.operacoes == n * 6 + n


def test_arvore_tem_quatro_niveis():
    v = gerar_serie_escalabilidade(200, seed=3)
    _, arvore = intervalo_critico_dc(v, profundidade_registro=3)
    niveis, fila = set(), [arvore]
    while fila:
        no = fila.pop()
        niveis.add(no.profundidade)
        fila.extend(no.filhos)
    assert niveis == {0, 1, 2, 3}


def test_dados_reprodutiveis_e_minimo_de_1000():
    a, b = gerar_dados(seed=9), gerar_dados(seed=9)
    assert a == b and len(a) >= 1000
    assert a != gerar_dados(seed=10)


def _indice_manual() -> IndiceEnergia:
    t0 = datetime(2026, 1, 1)
    regs = [Registro(t0 + timedelta(hours=h), reg, c, 100, 3, 200)
            for reg, consumos in {"A": [50, 120, 130, 40], "B": [90, 95, 99, 101]}.items()
            for h, c in enumerate(consumos)]
    return IndiceEnergia(regs)


def test_consultas_do_indice():
    idx = _indice_manual()
    t0 = datetime(2026, 1, 1)
    assert idx.consumo_por_regiao() == {"A": 340, "B": 385}
    assert [r.consumo for r in idx.picos(2)] == [130, 120]
    assert idx.esta_sobrecarregado(t0 + timedelta(hours=1), "A")
    assert not idx.esta_sobrecarregado(t0, "A")
    assert idx.periodos_criticos("A") == [(t0 + timedelta(hours=1), t0 + timedelta(hours=2))]
    assert idx.periodos_criticos("B") == [(t0 + timedelta(hours=3), t0 + timedelta(hours=3))]
    sel = idx.selecionar_intervalo("A", t0 + timedelta(hours=1), t0 + timedelta(hours=2))
    assert [r.consumo for r in sel] == [120, 130]
    assert idx.consumo_no_intervalo("A", t0 + timedelta(hours=1), t0 + timedelta(hours=3)) == 290
    assert idx.consumo_medio_por_hora()[0] == 70


def test_indice_entradas_invalidas():
    idx = _indice_manual()
    with pytest.raises(KeyError):
        idx.serie("Z")
    with pytest.raises(ValueError):
        idx.picos(0)
    with pytest.raises(ValueError):
        idx.selecionar_intervalo("A", datetime(2026, 1, 2), datetime(2026, 1, 1))
    with pytest.raises(ValueError):
        IndiceEnergia([])


def test_criticidade_cresce_com_a_carga():
    t = datetime(2026, 1, 1)
    folgado = Registro(t, "A", 50, 100, 3, 250)
    no_limite = Registro(t, "A", 95, 100, 3, 250)
    excedido = Registro(t, "A", 110, 100, 3, 250)
    assert criticidade(folgado) < 0 < criticidade(no_limite) < criticidade(excedido)
