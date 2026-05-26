import sqlite3, os
from pathlib import Path
BASE_DIR = Path(__file__).parent.parent.parent
db_path = str(BASE_DIR / "cnpj.db")
conn = sqlite3.connect(db_path)
rows = conn.execute("SELECT name FROM sqlite_master WHERE type='index' ORDER BY name").fetchall()
print(f"{len(rows)} índices encontrados:")
for r in rows:
    print(" ", r[0])
conn.close()
