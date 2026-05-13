import sqlite3
db = r"c:\Users\roberg\Documents\DA\Pythagoras\busca_empresa\backend\cnpj.db"
conn = sqlite3.connect(db)
result = conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
conn.close()
print(f"Checkpoint: {result}")
print("Lock liberado.")
