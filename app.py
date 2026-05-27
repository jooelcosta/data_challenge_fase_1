# =========================================================
# SCRIPT APENAS PARA TESTES

import subprocess
import sys
import time

# Lista dos scripts a serem executados
scripts = [
    "src.partidos"

]

#Executa cada script em sequência
for script in scripts:
    print(f"\nExecutando {script}...")
    time.sleep(5)
    subprocess.run([sys.executable,"-m", script], check=True)
