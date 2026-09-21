"""Configurações globais do projeto.

SEED é o identificador do grupo: toda a geração de dados usa esta semente,
portanto qualquer pessoa que execute o projeto obtém exatamente as mesmas
instâncias. Para trocar de instância basta alterar SEED e reexecutar.
"""
from pathlib import Path

SEED = 564360

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
FIG_DIR = ROOT / "figures"
RESULTS_DIR = ROOT / "results"

INTEGRANTES = [
    ("Felipe Bernardes", "RM564360"),
    ("Guilherme Romero", "RM564431"),
]
