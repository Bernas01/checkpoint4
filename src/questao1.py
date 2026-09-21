"""Pipeline completo da Questão 1.

Uso:
    python -m src.questao1                      # gera dados (se preciso), resolve e desenha
    python -m src.questao1 --capacidade 150     # altera a capacidade
    python -m src.questao1 --bloquear 3-7 --desbloquear 1-12
    python -m src.questao1 --peso 5-9=40 --prioridade 13=5
    python -m src.questao1 --sem-figuras

As alterações (usadas na defesa, quando o professor muda uma entrada) valem
apenas para a execução — o CSV original não é modificado.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import replace

from .caminhos import MatrizDistancias
from .config import DATA_DIR, FIG_DIR, RESULTS_DIR, SEED
from .contraexemplo import caso_guloso_otimo, contraexemplo_guloso
from .dados_q1 import ARQ_ARESTAS, carregar_instancia, gerar_instancia, salvar_instancia
from .dynamic_programming import Item, mochila_dp
from .estruturas import Grafo, calcular_beneficio
from .greedy import guloso_atendimento, regioes_candidatas, rota_vizinho_mais_proximo
from . import visualizacao_q1 as viz

FIG_Q1 = FIG_DIR / "questao1"


def obter_instancia(regenerar: bool = False) -> tuple[Grafo, int]:
    if regenerar or not (DATA_DIR / ARQ_ARESTAS).exists():
        grafo, cap = gerar_instancia(SEED)
        salvar_instancia(grafo, cap)
    return carregar_instancia()


def aplicar_alteracoes(grafo: Grafo, args: argparse.Namespace) -> None:
    for par in args.bloquear or []:
        grafo.bloquear(*_par(par))
    for par in args.desbloquear or []:
        grafo.desbloquear(*_par(par))
    for item in args.peso or []:
        par, peso = item.split("=")
        grafo.alterar_peso(*_par(par), float(peso))
    for item in args.prioridade or []:
        pid, prio = map(int, item.split("="))
        p = grafo.pontos[pid]
        grafo.substituir_ponto(replace(p, prioridade=prio, beneficio=calcular_beneficio(p.pessoas, prio)))


def _par(texto: str) -> tuple[int, int]:
    u, v = texto.split("-")
    return int(u), int(v)


def itens_da_instancia(grafo: Grafo, matriz: MatrizDistancias) -> list[Item]:
    return [Item(p.id, p.demanda, p.beneficio) for p in regioes_candidatas(grafo, matriz)]


def varrer_capacidades(grafo: Grafo, matriz: MatrizDistancias, passos: int = 20) -> list[dict]:
    itens = itens_da_instancia(grafo, matriz)
    total = sum(it.peso for it in itens)
    linhas = []
    for k in range(1, passos + 1):
        cap = round(total * k / passos)
        linhas.append({
            "capacidade": cap,
            "dp": mochila_dp(itens, cap).beneficio,
            "guloso_densidade": guloso_atendimento(grafo, cap, False, matriz).beneficio,
            "guloso_distancia": guloso_atendimento(grafo, cap, True, matriz).beneficio,
        })
    return linhas


def resolver(grafo: Grafo, capacidade: int, figuras: bool = True) -> dict:
    matriz = MatrizDistancias(grafo)
    itens = itens_da_instancia(grafo, matriz)
    guloso = guloso_atendimento(grafo, capacidade, True, matriz)
    guloso_dens = guloso_atendimento(grafo, capacidade, False, matriz)
    dp = mochila_dp(itens, capacidade)
    dp_ordem, dp_dist = rota_vizinho_mais_proximo(grafo, dp.selecionados, matriz)
    varredura = varrer_capacidades(grafo, matriz)

    g_ce, cap_ce = contraexemplo_guloso()
    ce_guloso = guloso_atendimento(g_ce, cap_ce)
    ce_dp = mochila_dp(itens_da_instancia(g_ce, MatrizDistancias(g_ce)), cap_ce)
    g_ok, cap_ok = caso_guloso_otimo()
    ok_guloso = guloso_atendimento(g_ok, cap_ok)
    ok_dp = mochila_dp(itens_da_instancia(g_ok, MatrizDistancias(g_ok)), cap_ok)

    resumo = {
        "seed": SEED,
        "V": grafo.num_vertices, "E": grafo.num_arestas, "bloqueadas": grafo.num_bloqueadas,
        "N_candidatas": len(itens), "capacidade": capacidade,
        "demanda_total": sum(it.peso for it in itens),
        "guloso": {"ordem": guloso.ordem, "beneficio": guloso.beneficio, "carga": guloso.carga_usada,
                   "distancia_km": round(guloso.distancia_total, 1),
                   "passos": [vars(p) for p in guloso.passos]},
        "guloso_densidade": {"ordem": guloso_dens.ordem, "beneficio": guloso_dens.beneficio,
                             "carga": guloso_dens.carga_usada},
        "dp": {"selecionados": sorted(dp.selecionados), "beneficio": dp.beneficio, "carga": dp.peso_usado,
               "rota": dp_ordem, "distancia_km": round(dp_dist, 1), "celulas": len(dp.tabela) * len(dp.tabela[0])},
        "varredura": varredura,
        "varredura_resumo": {
            "total": len(varredura),
            "densidade_otimo": sum(v["guloso_densidade"] == v["dp"] for v in varredura),
            "distancia_otimo": sum(v["guloso_distancia"] == v["dp"] for v in varredura),
            "pior_gap_densidade_%": round(max(100 * (1 - v["guloso_densidade"] / v["dp"]) for v in varredura), 1),
            "pior_gap_distancia_%": round(max(100 * (1 - v["guloso_distancia"] / v["dp"]) for v in varredura), 1),
        },
        "contraexemplo": {"guloso": ce_guloso.beneficio, "guloso_ordem": ce_guloso.ordem,
                          "dp": ce_dp.beneficio, "dp_sel": ce_dp.selecionados},
        "caso_guloso_otimo": {"guloso": ok_guloso.beneficio, "dp": ok_dp.beneficio},
        "dijkstras_executados": matriz.execucoes,
    }

    if figuras:
        viz.figura_grafo(grafo, capacidade, FIG_Q1 / "fig1_grafo.png")
        viz.figura_solucao(grafo, matriz, guloso, dp_ordem, dp, dp_dist, capacidade, FIG_Q1 / "fig2_solucao.png")
        curva = [guloso_atendimento(grafo, c, False, matriz).beneficio for c in range(capacidade + 1)]
        viz.figura_dp(dp, {p.id: p.nome for p in grafo.pontos.values()}, curva, FIG_Q1 / "fig3_programacao_dinamica.png")
        viz.figura_varredura(varredura, FIG_Q1 / "fig4_greedy_vs_dp_capacidades.png")
        viz.figura_contraexemplo(ce_guloso, ce_dp, FIG_Q1 / "fig5_contraexemplo.png")
    return resumo


def imprimir(r: dict) -> None:
    print(f"Instância SEED={r['seed']}: V={r['V']} E={r['E']} ({r['bloqueadas']} bloqueadas), "
          f"N={r['N_candidatas']} candidatas, C={r['capacidade']} de {r['demanda_total']} kits")
    g, gd, dp = r["guloso"], r["guloso_densidade"], r["dp"]
    print(f"Greedy (com distância): {g['ordem']}  benefício={g['beneficio']}  carga={g['carga']}  rota={g['distancia_km']} km")
    print(f"Greedy (benefício/kit): {gd['ordem']}  benefício={gd['beneficio']}  carga={gd['carga']}")
    print(f"DP (ótimo):             {dp['selecionados']}  benefício={dp['beneficio']}  carga={dp['carga']}  rota={dp['distancia_km']} km")
    v = r["varredura_resumo"]
    print(f"Varredura de {v['total']} capacidades: Greedy/kit ótimo em {v['densidade_otimo']}, "
          f"Greedy c/ distância ótimo em {v['distancia_otimo']} (pior perda {v['pior_gap_distancia_%']}%)")
    ce = r["contraexemplo"]
    print(f"Contraexemplo: Greedy={ce['guloso']} {ce['guloso_ordem']}  ×  DP={ce['dp']} {ce['dp_sel']}")


def main(argv: list[str] | None = None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--regenerar", action="store_true", help="gera novamente os CSVs a partir da SEED")
    ap.add_argument("--capacidade", type=int)
    ap.add_argument("--bloquear", action="append", metavar="U-V")
    ap.add_argument("--desbloquear", action="append", metavar="U-V")
    ap.add_argument("--peso", action="append", metavar="U-V=KM")
    ap.add_argument("--prioridade", action="append", metavar="ID=P")
    ap.add_argument("--sem-figuras", action="store_true")
    args = ap.parse_args(argv)

    grafo, capacidade = obter_instancia(args.regenerar)
    aplicar_alteracoes(grafo, args)
    capacidade = args.capacidade if args.capacidade is not None else capacidade
    alterado = any([args.bloquear, args.desbloquear, args.peso, args.prioridade, args.capacidade is not None])
    resumo = resolver(grafo, capacidade, figuras=not args.sem_figuras and not alterado)
    imprimir(resumo)
    if not alterado:
        RESULTS_DIR.mkdir(exist_ok=True)
        (RESULTS_DIR / "questao1.json").write_text(json.dumps(resumo, indent=2, ensure_ascii=False), encoding="utf-8")
    return resumo


if __name__ == "__main__":
    main()
