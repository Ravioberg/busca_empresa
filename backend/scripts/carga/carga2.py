#!/usr/bin/env python3
"""
carga2.py — Carga orientada para:
- historico de socios (processa todos os meses com Socios*.zip, em ordem cronologica)
- foto atual de empresa/estabelecimento (processa apenas o mes mais recente)
- dominios/simples sempre atualizados pelo mes mais recente (recarrega a cada execucao)

Uso:
    py -3.12 carga2.py
    py -3.12 carga2.py --status
    py -3.12 carga2.py --mes 2026-05   # processa historico de socios so deste mes
"""

import argparse
import ctypes
import io
import os
import re
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path

import warnings
warnings.filterwarnings("ignore", "pandas only supports SQLAlchemy connectable.*")

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, event, text

load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.parent.parent # Raiz do backend
DADOS_BRUTOS = Path(os.getenv("DADOS_BRUTOS", str(BASE_DIR / "dados-brutos"))).resolve()
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'cnpj.db'}")
CHUNK_SIZE = 100_000
CK_PREFIX = "carga2::"

COLS = {
    "empresa": [
        "cd_cnpjbasico", "nm_razaosocial", "cd_naturezajuridica",
        "cd_qualificacaoresponsavel", "vl_capitalsocial", "cd_porteempresa", "nm_entefederativo",
    ],
    "estabelecimento": [
        "cd_cnpjbasico", "cd_cnpjordem", "cd_cnpjdv", "cd_identificadormatrizfilial", "nm_nomefantasia",
        "cd_situacaocadastral", "dt_datasituacaocadastral", "cd_motivosituacaocadastral", "nm_cidadeexterior",
        "cd_pais", "dt_datainicioatividade", "cd_cnaefiscalprincipal", "ds_cnaefiscalsecundaria",
        "nm_tipologradouro", "nm_logradouro", "nm_numero", "nm_complemento", "nm_bairro",
        "cd_cep", "sg_uf", "cd_municipio", "cd_ddd1", "nr_telefone1", "cd_ddd2", "nr_telefone2",
        "cd_dddfax", "nr_fax", "nm_email", "nm_situacaoespecial", "dt_datasituacaoespecial",
    ],
    "socios": [
        "cd_cnpjbasico", "cd_identificadorsocio", "nm_nomesociorazaosocial", "cd_cpfcnpjsocio",
        "cd_qualificacaosocio", "dt_dataentradasociedade", "cd_pais", "cd_cpfrepresentantelegal",
        "nm_nomerepresentante", "cd_qualificacaorepresentantelegal", "cd_faixaetaria",
    ],
    "simples": [
        "cd_cnpjbasico", "fl_opcaosimples", "dt_dataopcaosimples", "dt_dataexclusaosimples",
        "fl_opcaomei", "dt_dataopcaomei", "dt_dataexclusaomei",
    ],
    "cnaes": ["cd_cnae", "ds_cnae"],
    "municipios": ["cd_municipio", "nm_municipio"],
    "naturezas": ["cd_naturezajuridica", "ds_naturezajuridica"],
    "qualificacoes": ["cd_qualificacao", "ds_qualificacao"],
    "motivos": ["cd_motivosituacaocadastral", "ds_motivosituacaocadastral"],
    "paises": ["cd_pais", "nm_pais"],
}

TABELA_DB = {
    "empresa": "empresa",
    "estabelecimento": "estabelecimento",
    "socios": "socio",
    "simples": "simples",
    "cnaes": "cnae",
    "municipios": "municipio",
    "naturezas": "natureza",
    "qualificacoes": "qualificacao",
    "motivos": "motivo",
    "paises": "pais",
}

PADROES_ZIP = {
    "empresa": "Empresas*.zip",
    "estabelecimento": "Estabelecimentos*.zip",
    "socios": "Socios*.zip",
    "simples": "Simples*.zip",
    "cnaes": "Cnaes*.zip",
    "municipios": "Municipios*.zip",
    "naturezas": "Naturezas*.zip",
    "qualificacoes": "Qualificacoes*.zip",
    "motivos": "Motivos*.zip",
    "paises": "Paises*.zip",
}

TMP_NOMES = {
    "empresa": "tmp_empresa",
    "estabelecimento": "tmp_estabelecimento",
    "socios": "tmp_socios",
}

CSV_PARAMS = dict(sep=";", encoding="latin-1", header=None, dtype=str, engine="python", quoting=1)

SQL_CREATE_TMP = {
    "empresa": """CREATE TABLE IF NOT EXISTS tmp_empresa (
        cd_cnpjbasico TEXT, nm_razaosocial TEXT, cd_naturezajuridica TEXT,
        cd_qualificacaoresponsavel TEXT, vl_capitalsocial TEXT, cd_porteempresa TEXT, nm_entefederativo TEXT
    )""",
    "estabelecimento": """CREATE TABLE IF NOT EXISTS tmp_estabelecimento (
        cd_cnpjbasico TEXT, cd_cnpjordem TEXT, cd_cnpjdv TEXT, cd_identificadormatrizfilial TEXT,
        nm_nomefantasia TEXT, cd_situacaocadastral TEXT, dt_datasituacaocadastral TEXT,
        cd_motivosituacaocadastral TEXT, nm_cidadeexterior TEXT, cd_pais TEXT, dt_datainicioatividade TEXT,
        cd_cnaefiscalprincipal TEXT, ds_cnaefiscalsecundaria TEXT, nm_tipologradouro TEXT,
        nm_logradouro TEXT, nm_numero TEXT, nm_complemento TEXT, nm_bairro TEXT,
        cd_cep TEXT, sg_uf TEXT, cd_municipio TEXT, cd_ddd1 TEXT, nr_telefone1 TEXT,
        cd_ddd2 TEXT, nr_telefone2 TEXT, cd_dddfax TEXT, nr_fax TEXT, nm_email TEXT,
        nm_situacaoespecial TEXT, dt_datasituacaoespecial TEXT
    )""",
    "socios": """CREATE TABLE IF NOT EXISTS tmp_socios (
        cd_cnpjbasico TEXT, cd_identificadorsocio TEXT, nm_nomesociorazaosocial TEXT,
        cd_cpfcnpjsocio TEXT, cd_qualificacaosocio TEXT, dt_dataentradasociedade TEXT,
        cd_pais TEXT, cd_cpfrepresentantelegal TEXT, nm_nomerepresentante TEXT,
        cd_qualificacaorepresentantelegal TEXT, cd_faixaetaria TEXT
    )""",
}

SQL_INDEX_TMP = {
    "empresa": "CREATE INDEX IF NOT EXISTS ix_tmp_emp ON tmp_empresa(cd_cnpjbasico)",
    "estabelecimento": "CREATE INDEX IF NOT EXISTS ix_tmp_est ON tmp_estabelecimento(cd_cnpjbasico, cd_cnpjordem)",
    "socios": "CREATE INDEX IF NOT EXISTS ix_tmp_soc ON tmp_socios(cd_cnpjbasico, cd_cpfcnpjsocio, cd_qualificacaosocio)",
}

SQL_UPSERT = {
    "empresa": """
        INSERT INTO empresa (
            cd_cnpjbasico, nm_razaosocial, cd_naturezajuridica, cd_qualificacaoresponsavel,
            vl_capitalsocial, cd_porteempresa, nm_entefederativo, dt_primeiracarga, dt_ultimaatualizacao
        )
        SELECT
            cd_cnpjbasico, nm_razaosocial, cd_naturezajuridica, cd_qualificacaoresponsavel,
            vl_capitalsocial, cd_porteempresa, nm_entefederativo, :mes, :mes
        FROM tmp_empresa WHERE 1=1 ORDER BY cd_cnpjbasico
        ON CONFLICT(cd_cnpjbasico) DO UPDATE SET
            nm_razaosocial = excluded.nm_razaosocial,
            cd_naturezajuridica = excluded.cd_naturezajuridica,
            cd_qualificacaoresponsavel = excluded.cd_qualificacaoresponsavel,
            vl_capitalsocial = excluded.vl_capitalsocial,
            cd_porteempresa = excluded.cd_porteempresa,
            nm_entefederativo = excluded.nm_entefederativo,
            dt_ultimaatualizacao = excluded.dt_ultimaatualizacao
    """,
    "estabelecimento": """
        INSERT INTO estabelecimento (
            cd_cnpjbasico, cd_cnpjordem, cd_cnpjdv, cd_identificadormatrizfilial, nm_nomefantasia,
            cd_situacaocadastral, dt_datasituacaocadastral, cd_motivosituacaocadastral, nm_cidadeexterior,
            cd_pais, dt_datainicioatividade, cd_cnaefiscalprincipal, ds_cnaefiscalsecundaria,
            nm_tipologradouro, nm_logradouro, nm_numero, nm_complemento, nm_bairro,
            cd_cep, sg_uf, cd_municipio, cd_ddd1, nr_telefone1, cd_ddd2, nr_telefone2,
            cd_dddfax, nr_fax, nm_email, nm_situacaoespecial, dt_datasituacaoespecial, dt_ultimaatualizacao
        )
        SELECT
            cd_cnpjbasico, cd_cnpjordem, cd_cnpjdv, cd_identificadormatrizfilial, nm_nomefantasia,
            cd_situacaocadastral, dt_datasituacaocadastral, cd_motivosituacaocadastral, nm_cidadeexterior,
            cd_pais, dt_datainicioatividade, cd_cnaefiscalprincipal, ds_cnaefiscalsecundaria,
            nm_tipologradouro, nm_logradouro, nm_numero, nm_complemento, nm_bairro,
            cd_cep, sg_uf, cd_municipio, cd_ddd1, nr_telefone1, cd_ddd2, nr_telefone2,
            cd_dddfax, nr_fax, nm_email, nm_situacaoespecial, dt_datasituacaoespecial, :mes
        FROM tmp_estabelecimento WHERE 1=1 ORDER BY cd_cnpjbasico, cd_cnpjordem
        ON CONFLICT(cd_cnpjbasico, cd_cnpjordem) DO UPDATE SET
            cd_cnpjdv = excluded.cd_cnpjdv,
            cd_identificadormatrizfilial = excluded.cd_identificadormatrizfilial,
            nm_nomefantasia = excluded.nm_nomefantasia,
            cd_situacaocadastral = excluded.cd_situacaocadastral,
            dt_datasituacaocadastral = excluded.dt_datasituacaocadastral,
            cd_motivosituacaocadastral = excluded.cd_motivosituacaocadastral,
            nm_cidadeexterior = excluded.nm_cidadeexterior,
            cd_pais = excluded.cd_pais,
            dt_datainicioatividade = excluded.dt_datainicioatividade,
            cd_cnaefiscalprincipal = excluded.cd_cnaefiscalprincipal,
            ds_cnaefiscalsecundaria = excluded.ds_cnaefiscalsecundaria,
            nm_tipologradouro = excluded.nm_tipologradouro,
            nm_logradouro = excluded.nm_logradouro,
            nm_numero = excluded.nm_numero,
            nm_complemento = excluded.nm_complemento,
            nm_bairro = excluded.nm_bairro,
            cd_cep = excluded.cd_cep,
            sg_uf = excluded.sg_uf,
            cd_municipio = excluded.cd_municipio,
            cd_ddd1 = excluded.cd_ddd1,
            nr_telefone1 = excluded.nr_telefone1,
            cd_ddd2 = excluded.cd_ddd2,
            nr_telefone2 = excluded.nr_telefone2,
            cd_dddfax = excluded.cd_dddfax,
            nr_fax = excluded.nr_fax,
            nm_email = excluded.nm_email,
            nm_situacaoespecial = excluded.nm_situacaoespecial,
            dt_datasituacaoespecial = excluded.dt_datasituacaoespecial,
            dt_ultimaatualizacao = excluded.dt_ultimaatualizacao
    """,
    "socios": """
        INSERT INTO socio (
            cd_cnpjbasico, cd_identificadorsocio, nm_nomesociorazaosocial, cd_cpfcnpjsocio,
            cd_qualificacaosocio, dt_dataentradasociedade, cd_pais, cd_cpfrepresentantelegal,
            nm_nomerepresentante, cd_qualificacaorepresentantelegal, cd_faixaetaria, dt_ultimaatualizacao
        )
        SELECT
            cd_cnpjbasico, cd_identificadorsocio, nm_nomesociorazaosocial, cd_cpfcnpjsocio,
            cd_qualificacaosocio, dt_dataentradasociedade, cd_pais, cd_cpfrepresentantelegal,
            nm_nomerepresentante, cd_qualificacaorepresentantelegal, cd_faixaetaria, :mes
        FROM tmp_socios WHERE 1=1 ORDER BY cd_cnpjbasico, cd_cpfcnpjsocio, cd_qualificacaosocio
        ON CONFLICT(cd_cnpjbasico, cd_cpfcnpjsocio, cd_qualificacaosocio) DO UPDATE SET
            cd_identificadorsocio = excluded.cd_identificadorsocio,
            nm_nomesociorazaosocial = excluded.nm_nomesociorazaosocial,
            dt_dataentradasociedade = excluded.dt_dataentradasociedade,
            cd_pais = excluded.cd_pais,
            cd_cpfrepresentantelegal = excluded.cd_cpfrepresentantelegal,
            nm_nomerepresentante = excluded.nm_nomerepresentante,
            cd_qualificacaorepresentantelegal = excluded.cd_qualificacaorepresentantelegal,
            cd_faixaetaria = excluded.cd_faixaetaria,
            dt_ultimaatualizacao = excluded.dt_ultimaatualizacao
    """,
}


def _to_sql(df, table: str, engine):
    conn = engine.raw_connection()
    try:
        df.to_sql(table, conn, if_exists="append", index=False)
        conn.commit()
    finally:
        conn.close()


def _configurar_sqlite(engine):
    def _on_connect(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode = WAL")
        cur.execute("PRAGMA synchronous = OFF")
        cur.execute("PRAGMA cache_size = -524288")  # 512 MB
        cur.execute("PRAGMA temp_store = MEMORY")
        cur.execute("PRAGMA threads = 4")
        cur.close()

    event.listen(engine, "connect", _on_connect)
    with engine.connect() as conn:
        conn.commit()


def _listar_meses() -> list[str]:
    padrao = re.compile(r"^\d{4}-\d{2}$")
    if not DADOS_BRUTOS.exists():
        return []
    return sorted([p.name for p in DADOS_BRUTOS.iterdir() if p.is_dir() and padrao.match(p.name)])


def _listar_zips(mes: str, tipo: str) -> list[Path]:
    return sorted((DADOS_BRUTOS / mes).glob(PADROES_ZIP[tipo]))


def _abrir_stream(zip_path: Path):
    zf = zipfile.ZipFile(zip_path, "r")
    nomes = [n for n in zf.namelist() if not n.endswith("/")]
    if not nomes:
        zf.close()
        return None, None
    raw = zf.open(nomes[0])
    return zf, io.TextIOWrapper(raw, encoding="latin-1")


def _ck_get(engine, mes: str, key: str):
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT qtd_inseridos FROM tb_checkpoint_carga WHERE mes=:m AND tabela=:t"),
            {"m": mes, "t": key},
        ).fetchone()
    return row[0] if row else None


def _ck_set(engine, mes: str, key: str, qtd: int):
    with engine.connect() as conn:
        conn.execute(
            text("INSERT OR REPLACE INTO tb_checkpoint_carga (mes, tabela, qtd_inseridos) VALUES (:m, :t, :q)"),
            {"m": mes, "t": key, "q": qtd},
        )
        conn.commit()


def _registrar(engine, mes: str, stats: dict, status: str):
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO tb_processamento_mensal (
                dt_referencia, dt_processado,
                qtd_inseridos_empresa, qtd_atualizados_empresa,
                qtd_inseridos_estabelecimento, qtd_atualizados_estabelecimento,
                qtd_inseridos_socios, qtd_atualizados_socios, status
            ) VALUES (
                :mes, :ts, :ie, :ae, :iest, :aest, :is_, :as_, :st
            )
        """), {
            "mes": mes,
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ie": stats.get("inseridos_empresa", 0),
            "ae": stats.get("atualizados_empresa", 0),
            "iest": stats.get("inseridos_estabelecimento", 0),
            "aest": stats.get("atualizados_estabelecimento", 0),
            "is_": stats.get("inseridos_socios", 0),
            "as_": stats.get("atualizados_socios", 0),
            "st": status,
        })
        conn.commit()


def _processar_zip(engine, mes: str, tabela: str, zp: Path) -> int:
    tmp = TMP_NOMES[tabela]
    with engine.connect() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {tmp}"))
        conn.execute(text(SQL_CREATE_TMP[tabela]))
        conn.commit()

    zf, stream = _abrir_stream(zp)
    if stream is None:
        return 0

    total = 0
    raw = engine.raw_connection()
    try:
        for chunk in pd.read_csv(stream, names=COLS[tabela], chunksize=CHUNK_SIZE, **CSV_PARAMS):
            chunk.to_sql(tmp, raw, if_exists="append", index=False)
            total += len(chunk)
            print(f"    {zp.name}: {total:,} linhas...", end="\r")
        raw.commit()
    finally:
        raw.close()
        zf.close()

    with engine.connect() as conn:
        conn.execute(text(SQL_INDEX_TMP[tabela]))
        conn.execute(text(SQL_UPSERT[tabela]), {"mes": mes})
        conn.execute(text(f"DROP TABLE IF EXISTS {tmp}"))
        conn.commit()
        conn.execute(text("PRAGMA wal_checkpoint(PASSIVE)"))
    print(f"    {zp.name}: concluido ({total:,})")
    return total


def _processar_tabela_mes(engine, mes: str, tabela: str, usar_checkpoint: bool = True) -> tuple[int, int]:
    tabela_db = TABELA_DB[tabela]
    zips = _listar_zips(mes, tabela)
    if not zips:
        print(f"  [AVISO] {tabela}: nenhum ZIP em {mes}")
        return 0, 0

    with engine.connect() as conn:
        antes = conn.execute(text(f"SELECT COALESCE(MAX(rowid), 0) FROM {tabela_db}")).scalar()

    total_linhas = 0
    for zp in zips:
        ck_key = f"{CK_PREFIX}{tabela}::{zp.name}"
        ck = _ck_get(engine, mes, ck_key) if usar_checkpoint else None
        if ck is not None:
            print(f"    {zp.name}: checkpoint ({ck:,})")
            total_linhas += ck
            continue

        qtd = _processar_zip(engine, mes, tabela, zp)
        total_linhas += qtd
        if usar_checkpoint:
            _ck_set(engine, mes, ck_key, qtd)

    with engine.connect() as conn:
        depois = conn.execute(text(f"SELECT COALESCE(MAX(rowid), 0) FROM {tabela_db}")).scalar()

    inseridos = (depois or 0) - (antes or 0)
    atualizados = max(0, total_linhas - inseridos)
    print(f"  {tabela_db}: +{inseridos:,} | ~{atualizados:,}")
    return inseridos, atualizados


def _recarregar_dominios_e_simples(engine, mes: str):
    print(f"\n--- Dominios e Simples (sempre do mes mais recente: {mes}) ---")
    dominios = ["cnaes", "municipios", "naturezas", "qualificacoes", "motivos", "paises"]
    for tipo in dominios:
        tabela = TABELA_DB[tipo]
        with engine.connect() as conn:
            conn.execute(text(f"DELETE FROM {tabela}"))
            conn.commit()
        total = 0
        for zp in _listar_zips(mes, tipo):
            zf, stream = _abrir_stream(zp)
            if stream is None:
                continue
            try:
                df = pd.read_csv(stream, names=COLS[tipo], **CSV_PARAMS)
                _to_sql(df, tabela, engine)
                total += len(df)
            finally:
                zf.close()
        print(f"  {tabela}: {total:,} registros")

    with engine.connect() as conn:
        conn.execute(text("DELETE FROM simples"))
        conn.commit()
    total = 0
    for zp in _listar_zips(mes, "simples"):
        zf, stream = _abrir_stream(zp)
        if stream is None:
            continue
        raw = engine.raw_connection()
        try:
            for chunk in pd.read_csv(stream, names=COLS["simples"], chunksize=CHUNK_SIZE, **CSV_PARAMS):
                chunk.to_sql("simples", raw, if_exists="append", index=False)
                total += len(chunk)
            raw.commit()
        finally:
            raw.close()
            zf.close()
    print(f"  simples: {total:,} registros")


def _show_status(engine):
    meses = _listar_meses()
    print(f"\n{'Mes':<10} {'Status':<10} {'+Emp':>10} {'~Emp':>10} {'+Est':>10} {'~Est':>10} {'+Soc':>10} {'~Soc':>10}")
    print("-" * 96)
    for mes in meses:
        with engine.connect() as conn:
            row = conn.execute(text("""
                SELECT status, qtd_inseridos_empresa, qtd_atualizados_empresa,
                       qtd_inseridos_estabelecimento, qtd_atualizados_estabelecimento,
                       qtd_inseridos_socios, qtd_atualizados_socios
                FROM tb_processamento_mensal
                WHERE dt_referencia = :m ORDER BY id DESC LIMIT 1
            """), {"m": mes}).fetchone()
        if row:
            print(f"{mes:<10} {row[0]:<10} {row[1]:>10,} {row[2]:>10,} {row[3]:>10,} {row[4]:>10,} {row[5]:>10,} {row[6]:>10,}")
        else:
            print(f"{mes:<10} {'pendente':<10}")
    print()


def _prevenir_sleep():
    try:
        ES_CONTINUOUS = 0x80000000
        ES_SYSTEM_REQUIRED = 0x00000001
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
    except Exception:
        pass


def _restaurar_sleep():
    try:
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
    except Exception:
        pass


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Carga com historico de socios + foto atual de empresas")
    parser.add_argument("--status", action="store_true", help="Mostra status por mes")
    parser.add_argument("--mes", metavar="YYYY-MM", help="Processa socios apenas deste mes")
    args = parser.parse_args()

    print(f"Banco        : {DATABASE_URL}")
    print(f"dados-brutos : {DADOS_BRUTOS}")

    if not DADOS_BRUTOS.exists():
        print(f"ERRO: dados-brutos nao encontrado: {DADOS_BRUTOS}")
        sys.exit(1)

    # Adiciona a raiz do projeto e a pasta app ao path
    root_path = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(root_path))
    sys.path.insert(0, str(root_path / "app"))

    from app.database import Base
    from app import models  # noqa: F401

    sqlite_args = {"check_same_thread": False, "timeout": 120} if DATABASE_URL.startswith("sqlite") else {}
    engine = create_engine(DATABASE_URL, connect_args=sqlite_args)
    if DATABASE_URL.startswith("sqlite"):
        _configurar_sqlite(engine)

    print("\nCriando tabelas (se nao existirem)...")
    Base.metadata.create_all(bind=engine)

    if args.status:
        _show_status(engine)
        return

    meses = _listar_meses()
    if not meses:
        print("ERRO: nenhuma pasta mensal encontrada em dados-brutos.")
        return
    mes_mais_recente = meses[-1]
    print(f"\nMes mais recente detectado: {mes_mais_recente}")

    _recarregar_dominios_e_simples(engine, mes_mais_recente)

    # Foto atual de empresa/estabelecimento: apenas ultimo mes
    print(f"\n--- Foto atual (empresa/estabelecimento) em {mes_mais_recente} ---")
    ie, ae = _processar_tabela_mes(engine, mes_mais_recente, "empresa")
    iest, aest = _processar_tabela_mes(engine, mes_mais_recente, "estabelecimento")

    # Historico de socios: todos os meses (ou apenas --mes)
    if args.mes:
        meses_socios = [args.mes]
    else:
        meses_socios = [m for m in meses if _listar_zips(m, "socios")]

    if not meses_socios:
        print("\n[AVISO] nenhum mes com Socios*.zip encontrado.")
        return

    inicio = time.time()
    for mes in meses_socios:
        print(f"\n{'=' * 60}\nProcessando socios: {mes}\n{'=' * 60}")
        try:
            is_, as_ = _processar_tabela_mes(engine, mes, "socios")
            stats = {
                "inseridos_empresa": ie if mes == mes_mais_recente else 0,
                "atualizados_empresa": ae if mes == mes_mais_recente else 0,
                "inseridos_estabelecimento": iest if mes == mes_mais_recente else 0,
                "atualizados_estabelecimento": aest if mes == mes_mais_recente else 0,
                "inseridos_socios": is_,
                "atualizados_socios": as_,
            }
            _registrar(engine, mes, stats, "CONCLUIDO")
        except Exception as exc:
            _registrar(engine, mes, {}, "ERRO")
            print(f"ERRO no mes {mes}: {exc}")
            raise

    elapsed = int(time.time() - inicio)
    h, rem = divmod(elapsed, 3600)
    m, s = divmod(rem, 60)
    print(f"\nCarga2 concluida em {h}h {m}m {s}s")
    _show_status(engine)


if __name__ == "__main__":
    _prevenir_sleep()
    try:
        main()
    finally:
        _restaurar_sleep()
