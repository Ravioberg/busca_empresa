import sqlite3, os, sys
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv

load_dotenv()
db_path = os.getenv("DATABASE_URL", "sqlite:///./cnpj.db").replace("sqlite:///", "")
conn = sqlite3.connect(db_path, timeout=30)
conn.execute("PRAGMA journal_mode=WAL")

print("=== INDICES B-TREE ===")
rows = conn.execute("SELECT name FROM sqlite_master WHERE type='index' ORDER BY name").fetchall()
for r in rows:
    print(f"  {r[0]}")

print("\n=== TABELAS FTS5 (existencia) ===")
fts = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'fts_%'").fetchall()
if fts:
    for r in fts:
        print(f"  OK: {r[0]}")
else:
    print("  NENHUMA - FTS5 nao foi criado")

print("\n=== TESTE BUSCA FTS5 (rapido - limite 1) ===")
try:
    r = conn.execute("SELECT cd_cnpjbasico, nm_razaosocial FROM fts_empresa WHERE fts_empresa MATCH 'petrobras' LIMIT 3").fetchall()
    print(f"  fts_empresa MATCH 'petrobras': {len(r)} resultado(s)")
    for row in r:
        print(f"    {row[0]} | {row[1]}")
except Exception as e:
    print(f"  ERRO fts_empresa: {e}")

try:
    r = conn.execute("SELECT nm_nomesociorazaosocial FROM fts_socio WHERE fts_socio MATCH 'silva' LIMIT 3").fetchall()
    print(f"  fts_socio MATCH 'silva': {len(r)} resultado(s)")
    for row in r:
        print(f"    {row[0]}")
except Exception as e:
    print(f"  ERRO fts_socio: {e}")

print("\n=== TESTE B-TREE (socio por CNPJ) ===")
try:
    r = conn.execute("SELECT COUNT(*) FROM socio WHERE cd_cnpjbasico = '33000167'").fetchone()
    print(f"  Petrobras (33000167): {r[0]} socio(s)")
except Exception as e:
    print(f"  ERRO: {e}")

print("\n=== MES ATUAL ===")
try:
    r = conn.execute("SELECT MAX(dt_referencia) FROM tb_processamento_mensal WHERE status='CONCLUIDO'").fetchone()
    print(f"  mes_atual = {r[0]}")
except Exception as e:
    print(f"  ERRO: {e}")

conn.close()
print("\nVerificacao concluida.")
