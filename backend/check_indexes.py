import sqlite3
conn = sqlite3.connect("cnpj.db")
rows = conn.execute("SELECT name FROM sqlite_master WHERE type='index' ORDER BY name").fetchall()
print(f"{len(rows)} índices encontrados:")
for r in rows:
    print(" ", r[0])
conn.close()
