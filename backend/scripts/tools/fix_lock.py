import sqlite3, os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent.parent
load_dotenv(BASE_DIR / ".env")

db_path_raw = os.getenv("DATABASE_URL", "sqlite:///./cnpj.db")
if db_path_raw.startswith("sqlite:///./"):
    db = str(BASE_DIR / db_path_raw.replace("sqlite:///./", ""))
else:
    db = db_path_raw.replace("sqlite:///", "")

print(f"Banco: {db}")
conn = sqlite3.connect(db)
result = conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
conn.close()
print(f"Checkpoint: {result}")
print("Lock liberado.")
