"""
Repara indices de busca e FTS5 do banco SQLite sem reprocessar os ZIPs.

Uso:
    python backend/scripts/tools/reparar_busca.py
    python backend/scripts/tools/reparar_busca.py --force-fts

Use quando `carga.py validar` apontar indice faltando ou FTS vazia.
"""
import argparse
import os
import sqlite3
import time
import unicodedata
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).parent.parent.parent
load_dotenv(BASE_DIR / ".env")


def _resolve_path(value: str, default_base: Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (default_base / path).resolve()


def _db_path() -> Path:
    raw = os.getenv("DATABASE_URL", "./cnpj.db")
    if raw.startswith("sqlite:///"):
        raw = raw.replace("sqlite:///", "", 1)
    return _resolve_path(raw, BASE_DIR)


def _normalizar(texto):
    if not texto:
        return None
    return unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode("ascii").upper()


def _table_has_rows(conn: sqlite3.Connection, table: str) -> bool:
    exists = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    if not exists:
        return False
    return conn.execute(f"SELECT 1 FROM {table} LIMIT 1").fetchone() is not None


def _step(conn: sqlite3.Connection, label: str, sql: str):
    print(f"[*] {label}...", flush=True)
    t = time.time()
    conn.execute(sql)
    conn.commit()
    print(f"    OK {time.time() - t:.1f}s\n", flush=True)


def _criar_indices(conn: sqlite3.Connection):
    indices = [
        ("idx_empresa_razao", "CREATE INDEX IF NOT EXISTS idx_empresa_razao ON empresa(nm_razaosocial)"),
        ("idx_estab_basico", "CREATE INDEX IF NOT EXISTS idx_estab_basico ON estabelecimento(cd_cnpjbasico)"),
        ("idx_estab_fantasia", "CREATE INDEX IF NOT EXISTS idx_estab_fantasia ON estabelecimento(nm_nomefantasia)"),
        ("idx_socio_cnpjbasico", "CREATE INDEX IF NOT EXISTS idx_socio_cnpjbasico ON socio(cd_cnpjbasico)"),
        ("idx_socio_cpf", "CREATE INDEX IF NOT EXISTS idx_socio_cpf ON socio(cd_cpfcnpjsocio)"),
        ("idx_socio_nome", "CREATE INDEX IF NOT EXISTS idx_socio_nome ON socio(nm_nomesociorazaosocial)"),
    ]
    existentes = {
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()
    }
    for nome, sql in indices:
        if nome in existentes:
            print(f"[=] {nome}: ja existe")
            continue
        _step(conn, f"criando indice {nome}", sql)


def _recriar_fts_empresa(conn: sqlite3.Connection):
    _step(conn, "FTS empresa: removendo anterior", "DROP TABLE IF EXISTS fts_empresa")
    _step(conn, "FTS empresa: criando", """
        CREATE VIRTUAL TABLE fts_empresa
        USING fts5(
            cd_cnpjbasico        UNINDEXED,
            nm_razaosocial,
            nm_nomefantasia,
            cd_situacaocadastral UNINDEXED,
            fl_matriz            UNINDEXED,
            tokenize = 'trigram'
        )
    """)
    _step(conn, "FTS empresa: populando", """
        INSERT INTO fts_empresa(cd_cnpjbasico, nm_razaosocial, nm_nomefantasia,
                                cd_situacaocadastral, fl_matriz)
        SELECT e.cd_cnpjbasico,
               normalizar(e.nm_razaosocial),
               normalizar(est.nm_nomefantasia),
               est.cd_situacaocadastral,
               est.cd_identificadormatrizfilial
        FROM empresa e
        LEFT JOIN estabelecimento est
            ON e.cd_cnpjbasico = est.cd_cnpjbasico
           AND est.cd_cnpjordem = '0001'
    """)


def _recriar_fts_socio(conn: sqlite3.Connection):
    _step(conn, "FTS socio: removendo anterior", "DROP TABLE IF EXISTS fts_socio")
    _step(conn, "FTS socio: criando", """
        CREATE VIRTUAL TABLE fts_socio
        USING fts5(
            rowid_ref UNINDEXED,
            nm_nomesociorazaosocial,
            tokenize = 'trigram'
        )
    """)
    _step(conn, "FTS socio: populando", """
        INSERT INTO fts_socio(rowid_ref, nm_nomesociorazaosocial)
        SELECT id, normalizar(nm_nomesociorazaosocial)
        FROM socio
    """)


def _validar(conn: sqlite3.Connection) -> bool:
    ok = True
    for table in ["empresa", "estabelecimento", "socio", "fts_empresa", "fts_socio"]:
        has_rows = _table_has_rows(conn, table)
        print(f"{table:<18} {'OK' if has_rows else 'FALHOU'}")
        ok = ok and has_rows

    existentes = {
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()
    }
    for index in [
        "idx_empresa_razao",
        "idx_estab_basico",
        "idx_estab_fantasia",
        "idx_socio_cnpjbasico",
        "idx_socio_cpf",
        "idx_socio_nome",
    ]:
        exists = index in existentes
        print(f"{index:<18} {'OK' if exists else 'FALHOU'}")
        ok = ok and exists
    return ok


def main():
    parser = argparse.ArgumentParser(description="Repara indices e FTS5 do cnpj.db")
    parser.add_argument("--force-fts", action="store_true", help="Recria fts_empresa e fts_socio mesmo se ja tiverem dados")
    parser.add_argument("--force-fts-empresa", action="store_true", help="Recria fts_empresa mesmo se ja tiver dados")
    parser.add_argument("--force-fts-socio", action="store_true", help="Recria fts_socio mesmo se ja tiver dados")
    args = parser.parse_args()

    path = _db_path()
    print(f"Banco: {path}\n")
    if not path.exists():
        raise SystemExit(f"Banco nao encontrado: {path}")

    conn = sqlite3.connect(path, timeout=600)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-524288")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.create_function("normalizar", 1, _normalizar)

    try:
        _criar_indices(conn)

        if args.force_fts or args.force_fts_empresa or not _table_has_rows(conn, "fts_empresa"):
            _recriar_fts_empresa(conn)
        else:
            print("[=] fts_empresa: ja existe e tem dados")

        if args.force_fts or args.force_fts_socio or not _table_has_rows(conn, "fts_socio"):
            _recriar_fts_socio(conn)
        else:
            print("[=] fts_socio: ja existe e tem dados")

        print("\n--- Validacao ---")
        ok = _validar(conn)
        print("\nResultado:", "OK" if ok else "FALHOU")
        raise SystemExit(0 if ok else 1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
