
# ============================================================
# PROJETO ED-ANTAQ-01
# TESTE DO AMBIENTE LOCAL
# ============================================================

import sys
import pandas as pd
import sqlite3

print("=" * 45)
print("PROJETO ED-ANTAQ-01")
print("=" * 45)

print("Python:", sys.version.split()[0])
print("Pandas:", pd.__version__)
print("SQLite:", sqlite3.sqlite_version)

print("\nAmbiente configurado com sucesso!")
