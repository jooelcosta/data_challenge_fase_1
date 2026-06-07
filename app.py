# =========================================================
# SCRIPT APENAS PARA TESTES

import argparse
import subprocess
import sys
import time
from datetime import date, timedelta

parser = argparse.ArgumentParser(description="Pipeline de dados — Câmara Legislativa")

parser.add_argument(
    "--data-inicio",
    type=str,
    # padrão: ontem (garante um dia completo fechado)
    default=str(date.today() - timedelta(days=1)),
    help="Data de início da extração no formato YYYY-MM-DD",
)

parser.add_argument(
    "--data-fim",
    type=str,
    # padrão: hoje
    default=str(date.today()),
    help="Data de fim da extração no formato YYYY-MM-DD",
)

args = parser.parse_args()

print(f"Iniciando extração: {args.data_inicio} → {args.data_fim}")

# Lista dos scripts a serem executados
scripts = [
    "src.deputados",
    "src.partidos",
    "src.proposicoes",
    "src.votacoes",
    "src.despesas",
]

# Executa cada script em sequência
for script in scripts:
    print(f"\nExecutando {script}...")
    time.sleep(5)
    subprocess.run(
        [
            sys.executable,
            "-m",
            script,
            "--data-inicio",
            args.data_inicio,
            "--data-fim",
            args.data_fim,
        ],
        check=True,  # lança exceção se o script falhar — interrompe o pipeline
    )
print("\nPipeline finalizado com sucesso!")
