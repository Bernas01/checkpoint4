"""Executa as duas questões de ponta a ponta: dados → algoritmos → figuras → results/.

    python run_all.py              # usa os CSVs existentes (ou gera se não existirem)
    python run_all.py --regenerar  # recria os CSVs a partir da SEED
"""
import sys

from src import questao1, questao2

if __name__ == "__main__":
    extra = ["--regenerar"] if "--regenerar" in sys.argv else []
    print("=" * 30, "QUESTÃO 1", "=" * 30)
    questao1.main(extra)
    print("\n" + "=" * 30, "QUESTÃO 2", "=" * 30)
    questao2.main(extra)
