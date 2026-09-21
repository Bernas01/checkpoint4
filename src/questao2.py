"""Pipeline completo da Questão 2.

Uso:
    python -m src.questao2                          # dados, análise, experimento e figuras
    python -m src.questao2 --regiao Nordeste        # muda a região da análise principal
    python -m src.questao2 --inicio 48 --fim 200    # restringe a um intervalo de horas
    python -m src.questao2 --sem-experimento        # pula a Parte D (mais rápido)
"""
from __future__ import annotations

import argparse
import csv
import json

from .brute_force import intervalo_critico_forca_bruta
from .config import DATA_DIR, FIG_DIR, RESULTS_DIR, SEED
from .dados_q2 import ARQ, carregar_csv, gerar_dados, salvar_csv, serie_criticidade
from .divide_conquer import intervalo_critico_dc
from .estruturas import IndiceEnergia
from .experimento import extrapolar, rodar
from .metricas import Contador
from . import visualizacao_q2 as viz

FIG_Q2 = FIG_DIR / "questao2"


def obter_indice(regenerar: bool = False) -> IndiceEnergia:
    if regenerar or not (DATA_DIR / ARQ).exists():
        salvar_csv(gerar_dados(seed=SEED))
    return IndiceEnergia(carregar_csv())


def analisar_regiao(indice: IndiceEnergia, regiao: str, inicio: int = 0, fim: int | None = None) -> dict:
    serie = indice.serie(regiao)[inicio:fim]
    if not serie:
        raise ValueError("intervalo vazio")
    crit = serie_criticidade(serie)
    c_fb, c_dc = Contador(), Contador()
    fb = intervalo_critico_forca_bruta(crit, c_fb)
    dc, arvore = intervalo_critico_dc(crit, c_dc, profundidade_registro=3)
    return {"regiao": regiao, "serie": serie, "crit": crit, "fb": fb, "dc": dc, "arvore": arvore,
            "ops_fb": c_fb.operacoes, "ops_dc": c_dc.operacoes}


def resumo_estruturas(indice: IndiceEnergia) -> dict:
    return {
        "observacoes": len(indice.registros),
        "regioes": indice.regioes,
        "consumo_por_regiao_MWh": {k: round(v) for k, v in indice.consumo_por_regiao().items()},
        "consumo_medio_por_hora": {h: round(v, 1) for h, v in indice.consumo_medio_por_hora().items()},
        "top5_picos": [(r.timestamp.isoformat(), r.regiao, r.consumo) for r in indice.picos(5)],
        "horas_em_sobrecarga": len(indice.sobrecarga),
        "periodos_criticos_Sudeste": [(a.isoformat(), b.isoformat()) for a, b in indice.periodos_criticos("Sudeste")],
    }


def main(argv: list[str] | None = None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--regenerar", action="store_true")
    ap.add_argument("--regiao", default=None, help="padrão: região de maior criticidade acumulada")
    ap.add_argument("--inicio", type=int, default=0, help="primeira hora (índice) analisada")
    ap.add_argument("--fim", type=int, default=None, help="última hora (exclusiva)")
    ap.add_argument("--sem-experimento", action="store_true")
    ap.add_argument("--sem-figuras", action="store_true")
    args = ap.parse_args(argv)

    indice = obter_indice(args.regenerar)
    print(f"{len(indice.registros)} observações, regiões: {', '.join(indice.regioes)}")
    analises = {r: analisar_regiao(indice, r, args.inicio, args.fim) for r in indice.regioes}
    for a in analises.values():
        s = a["serie"]
        print(f"  {a['regiao']:<13} FB: [{a['fb'].inicio},{a['fb'].fim}] {a['fb'].soma:8.2f} ({a['ops_fb']:,} ops) | "
              f"D&C: [{a['dc'].inicio},{a['dc'].fim}] {a['dc'].soma:8.2f} ({a['ops_dc']:,} ops) | "
              f"{s[a['dc'].inicio].timestamp:%d/%m %Hh} → {s[a['dc'].fim].timestamp:%d/%m %Hh}")
    regiao = args.regiao or max(analises, key=lambda r: analises[r]["dc"].soma)
    principal = analises[regiao]

    resumo = {
        "seed": SEED,
        "estruturas": resumo_estruturas(indice),
        "por_regiao": {
            r: {"inicio": a["serie"][a["dc"].inicio].timestamp.isoformat(),
                "fim": a["serie"][a["dc"].fim].timestamp.isoformat(),
                "indices": [a["dc"].inicio, a["dc"].fim], "criticidade": round(a["dc"].soma, 2),
                "horas": a["dc"].fim - a["dc"].inicio + 1, "fb_igual_dc": abs(a["fb"].soma - a["dc"].soma) < 1e-9,
                "ops_fb": a["ops_fb"], "ops_dc": a["ops_dc"]}
            for r, a in analises.items()},
        "regiao_principal": regiao,
    }

    if not args.sem_figuras:
        viz.figura_serie(principal["serie"], principal["crit"], principal["dc"], regiao, FIG_Q2 / "fig1_serie_temporal.png")
        viz.figura_decomposicao(principal["arvore"], principal["crit"], principal["serie"],
                                FIG_Q2 / "fig2_dividir_conquistar.png")

    if not args.sem_experimento:
        print("Experimento de escalabilidade:")
        linhas = rodar()
        resumo["escalabilidade"] = linhas
        resumo["extrapolacao_1M"] = extrapolar(linhas)
        RESULTS_DIR.mkdir(exist_ok=True)
        with open(RESULTS_DIR / "escalabilidade_q2.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(linhas[0].keys()))
            w.writeheader(); w.writerows(linhas)
        if not args.sem_figuras:
            viz.figura_escalabilidade(linhas, FIG_Q2 / "fig3_escalabilidade.png")
        e = resumo["extrapolacao_1M"]
        print(f"Projeção n=1.000.000: força bruta ≈ {e['forca_bruta_s'] / 3600:.1f} h | "
              f"D&C ≈ {e['dividir_conquistar_s']:.1f} s")

    alterado = args.inicio != 0 or args.fim is not None or args.sem_experimento
    if not alterado:
        RESULTS_DIR.mkdir(exist_ok=True)
        (RESULTS_DIR / "questao2.json").write_text(json.dumps(resumo, indent=2, ensure_ascii=False, default=str),
                                                  encoding="utf-8")
    return resumo


if __name__ == "__main__":
    main()
