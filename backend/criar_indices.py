"""
Cria índices B-tree e tabelas FTS5 no banco SQLite.
Execute sempre que o schema do FTS mudar: py -3.12 criar_indices.py

Tempo estimado: 30-60 minutos dependendo do hardware.
O FTS5 é recriado do zero (DROP + CREATE) para garantir consistência.
"""
import time
import unicodedata
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

db_path = os.getenv("DATABASE_URL", "sqlite:///./cnpj.db").replace("sqlite:///", "")
print(f"Banco: {db_path}\n")

conn = sqlite3.connect(db_path, timeout=600)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA cache_size=-524288")
conn.execute("PRAGMA synchronous=NORMAL")
conn.execute("PRAGMA temp_store=MEMORY")


def _normalizar(texto):
    """Remove acentos e converte para uppercase — conteúdo indexado no FTS5."""
    if not texto:
        return None
    return unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode("ascii").upper()


conn.create_function("normalizar", 1, _normalizar)


def step(descricao, sql):
    print(f"[→] {descricao}...", flush=True)
    t = time.time()
    conn.execute(sql)
    conn.commit()
    print(f"    ✓ {time.time() - t:.1f}s\n", flush=True)


# ── Índices B-tree ─────────────────────────────────────────────────────────────

step(
    "Índice socio.cd_cnpjbasico  (crítico: página de detalhe da empresa)",
    "CREATE INDEX IF NOT EXISTS idx_socio_cnpjbasico ON socio(cd_cnpjbasico)"
)

step(
    "Índice socio.cd_cpfcnpjsocio  (busca por CPF)",
    "CREATE INDEX IF NOT EXISTS idx_socio_cpf ON socio(cd_cpfcnpjsocio)"
)

step(
    "Índice estabelecimento.nm_nomefantasia  (JOIN na busca por nome de empresa)",
    "CREATE INDEX IF NOT EXISTS idx_estab_fantasia ON estabelecimento(nm_nomefantasia)"
)

# ── FTS5 — busca por nome de empresa ──────────────────────────────────────────
# Armazena nomes normalizados (sem acentos, uppercase) para busca accent-insensitive.
# O DROP garante recriação limpa quando este script for executado novamente.
step("FTS5 empresa — removendo tabela anterior", "DROP TABLE IF EXISTS fts_empresa")

step(
    "FTS5 empresa — criando tabela virtual",
    """
    CREATE VIRTUAL TABLE fts_empresa
    USING fts5(
        cd_cnpjbasico        UNINDEXED,
        nm_razaosocial,
        nm_nomefantasia,
        cd_situacaocadastral UNINDEXED,
        fl_matriz            UNINDEXED,
        tokenize = 'trigram'
    )
    """
)

step(
    "FTS5 empresa — populando com nomes normalizados (pode demorar ~20-30 min)",
    """
    INSERT INTO fts_empresa(cd_cnpjbasico, nm_razaosocial, nm_nomefantasia,
                            cd_situacaocadastral, fl_matriz)
    SELECT e.cd_cnpjbasico,
           normalizar(e.nm_razaosocial),
           normalizar(est.nm_nomefantasia),
           est.cd_situacaocadastral,
           est.cd_identificadormatrizfilial
    FROM empresa e
    LEFT JOIN estabelecimento est
        ON e.cd_cnpjbasico = est.cd_cnpjbasico AND est.cd_cnpjordem = '0001'
    """
)

# ── FTS5 — busca por nome de sócio ────────────────────────────────────────────
step("FTS5 socio — removendo tabela anterior", "DROP TABLE IF EXISTS fts_socio")

step(
    "FTS5 socio — criando tabela virtual",
    """
    CREATE VIRTUAL TABLE fts_socio
    USING fts5(
        rowid_ref UNINDEXED,
        nm_nomesociorazaosocial,
        tokenize = 'trigram'
    )
    """
)

step(
    "FTS5 socio — populando com nomes normalizados (pode demorar ~10 min)",
    """
    INSERT INTO fts_socio(rowid_ref, nm_nomesociorazaosocial)
    SELECT id, normalizar(nm_nomesociorazaosocial)
    FROM socio
    """
)

conn.close()
print("Concluído! Reinicie o servidor uvicorn.")
