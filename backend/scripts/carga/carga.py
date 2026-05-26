#!/usr/bin/env python3
"""
carga.py — Carga e atualização incremental da base CNPJ da Receita Federal.

Processa todos os meses disponíveis em dados-brutos/ em ordem cronológica.
Meses já concluídos são pulados automaticamente (tb_processamento_mensal).
Cada ZIP é processado individualmente (tmp → UPSERT → drop tmp) com checkpoint.
Se interrompido, retoma exatamente do ZIP seguinte ao último concluído.

Uso:
    py -3.12 carga.py              # processa todos os meses pendentes
    py -3.12 carga.py --status     # mostra situação de cada mês
    py -3.12 carga.py --mes 2023-03  # processa apenas este mês

Variáveis (.env):
    DATABASE_URL  → padrão: sqlite:///./cnpj.db
    DADOS_BRUTOS  → padrão: ../dados-brutos
"""

import io
import os
import re
import sys
import time
import zipfile
import argparse
import ctypes
from datetime import datetime
from pathlib import Path

import warnings
warnings.filterwarnings("ignore", "pandas only supports SQLAlchemy connectable.*")

import pandas as pd
from sqlalchemy import create_engine, event, text
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------
BASE_DIR     = Path(__file__).parent.parent.parent # Raiz do backend
load_dotenv(BASE_DIR / ".env")

DADOS_BRUTOS = Path(os.getenv("DADOS_BRUTOS", str(BASE_DIR / "dados-brutos"))).resolve()
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'cnpj.db'}")
CHUNK_SIZE   = 100_000
MES_DOMINIOS = "2026-04"

# ---------------------------------------------------------------------------
# Colunas por tabela (layout oficial RF — cnpj-metadados.pdf)
# ---------------------------------------------------------------------------
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
    "cnaes":         ["cd_cnae", "ds_cnae"],
    "municipios":    ["cd_municipio", "nm_municipio"],
    "naturezas":     ["cd_naturezajuridica", "ds_naturezajuridica"],
    "qualificacoes": ["cd_qualificacao", "ds_qualificacao"],
    "motivos":       ["cd_motivosituacaocadastral", "ds_motivosituacaocadastral"],
    "paises":        ["cd_pais", "nm_pais"],
}

TABELA_DB = {
    "empresa": "empresa", "estabelecimento": "estabelecimento", "socios": "socio",
    "simples": "simples", "cnaes": "cnae", "municipios": "municipio",
    "naturezas": "natureza", "qualificacoes": "qualificacao",
    "motivos": "motivo", "paises": "pais",
}

TMP_NOMES = {
    "empresa":         "tmp_empresa",
    "estabelecimento": "tmp_estabelecimento",
    "socios":          "tmp_socios",
}

PADROES_ZIP = {
    "empresa":         "Empresas*.zip",
    "estabelecimento": "Estabelecimentos*.zip",
    "socios":          "Socios*.zip",
    "simples":         "Simples*.zip",
    "cnaes":           "Cnaes*.zip",
    "municipios":      "Municipios*.zip",
    "naturezas":       "Naturezas*.zip",
    "qualificacoes":   "Qualificacoes*.zip",
    "motivos":         "Motivos*.zip",
    "paises":          "Paises*.zip",
}

CSV_PARAMS = dict(sep=";", encoding="latin-1", header=None, dtype=str, engine="python", quoting=1)


def _is_postgres() -> bool:
    return DATABASE_URL.startswith("postgresql")

# ---------------------------------------------------------------------------
# SQL — tabelas temporárias (por ZIP, criadas e descartadas individualmente)
# ---------------------------------------------------------------------------
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
    "empresa":
        "CREATE INDEX IF NOT EXISTS ix_tmp_emp ON tmp_empresa(cd_cnpjbasico)",
    "estabelecimento":
        "CREATE INDEX IF NOT EXISTS ix_tmp_est ON tmp_estabelecimento(cd_cnpjbasico, cd_cnpjordem)",
    "socios":
        "CREATE INDEX IF NOT EXISTS ix_tmp_soc ON tmp_socios(cd_cnpjbasico, cd_cpfcnpjsocio, cd_qualificacaosocio)",
}

# ---------------------------------------------------------------------------
# SQL — UPSERT unificado (primeira carga e incrementais usam o mesmo SQL)
#
# INSERT tenta inserir com dt_primeiracarga = :mes.
# ON CONFLICT atualiza todos os campos EXCETO dt_primeiracarga → preservada para registros existentes.
# Duplicatas RF dentro do mesmo ZIP: segunda ocorrência faz ON CONFLICT, atualiza com dados idênticos. Seguro.
# ---------------------------------------------------------------------------
SQL_UPSERT = {
    "empresa": """
        INSERT INTO empresa (
            cd_cnpjbasico, nm_razaosocial, cd_naturezajuridica, cd_qualificacaoresponsavel,
            vl_capitalsocial, cd_porteempresa, nm_entefederativo,
            dt_primeiracarga, dt_ultimaatualizacao
        )
        SELECT
            cd_cnpjbasico, nm_razaosocial, cd_naturezajuridica, cd_qualificacaoresponsavel,
            vl_capitalsocial, cd_porteempresa, nm_entefederativo,
            :mes, :mes
        FROM tmp_empresa WHERE 1=1 ORDER BY cd_cnpjbasico
        ON CONFLICT(cd_cnpjbasico) DO UPDATE SET
            nm_razaosocial             = excluded.nm_razaosocial,
            cd_naturezajuridica        = excluded.cd_naturezajuridica,
            cd_qualificacaoresponsavel = excluded.cd_qualificacaoresponsavel,
            vl_capitalsocial           = excluded.vl_capitalsocial,
            cd_porteempresa            = excluded.cd_porteempresa,
            nm_entefederativo          = excluded.nm_entefederativo,
            dt_ultimaatualizacao       = excluded.dt_ultimaatualizacao
    """,
    "estabelecimento": """
        INSERT INTO estabelecimento (
            cd_cnpjbasico, cd_cnpjordem, cd_cnpjdv, cd_identificadormatrizfilial, nm_nomefantasia,
            cd_situacaocadastral, dt_datasituacaocadastral, cd_motivosituacaocadastral, nm_cidadeexterior,
            cd_pais, dt_datainicioatividade, cd_cnaefiscalprincipal, ds_cnaefiscalsecundaria,
            nm_tipologradouro, nm_logradouro, nm_numero, nm_complemento, nm_bairro,
            cd_cep, sg_uf, cd_municipio, cd_ddd1, nr_telefone1, cd_ddd2, nr_telefone2,
            cd_dddfax, nr_fax, nm_email, nm_situacaoespecial, dt_datasituacaoespecial,
            dt_ultimaatualizacao
        )
        SELECT
            cd_cnpjbasico, cd_cnpjordem, cd_cnpjdv, cd_identificadormatrizfilial, nm_nomefantasia,
            cd_situacaocadastral, dt_datasituacaocadastral, cd_motivosituacaocadastral, nm_cidadeexterior,
            cd_pais, dt_datainicioatividade, cd_cnaefiscalprincipal, ds_cnaefiscalsecundaria,
            nm_tipologradouro, nm_logradouro, nm_numero, nm_complemento, nm_bairro,
            cd_cep, sg_uf, cd_municipio, cd_ddd1, nr_telefone1, cd_ddd2, nr_telefone2,
            cd_dddfax, nr_fax, nm_email, nm_situacaoespecial, dt_datasituacaoespecial,
            :mes
        FROM tmp_estabelecimento WHERE 1=1 ORDER BY cd_cnpjbasico, cd_cnpjordem
        ON CONFLICT(cd_cnpjbasico, cd_cnpjordem) DO UPDATE SET
            cd_cnpjdv                    = excluded.cd_cnpjdv,
            cd_identificadormatrizfilial = excluded.cd_identificadormatrizfilial,
            nm_nomefantasia              = excluded.nm_nomefantasia,
            cd_situacaocadastral         = excluded.cd_situacaocadastral,
            dt_datasituacaocadastral     = excluded.dt_datasituacaocadastral,
            cd_motivosituacaocadastral   = excluded.cd_motivosituacaocadastral,
            nm_cidadeexterior            = excluded.nm_cidadeexterior,
            cd_pais                      = excluded.cd_pais,
            dt_datainicioatividade       = excluded.dt_datainicioatividade,
            cd_cnaefiscalprincipal       = excluded.cd_cnaefiscalprincipal,
            ds_cnaefiscalsecundaria      = excluded.ds_cnaefiscalsecundaria,
            nm_tipologradouro            = excluded.nm_tipologradouro,
            nm_logradouro                = excluded.nm_logradouro,
            nm_numero                    = excluded.nm_numero,
            nm_complemento               = excluded.nm_complemento,
            nm_bairro                    = excluded.nm_bairro,
            cd_cep                       = excluded.cd_cep,
            sg_uf                        = excluded.sg_uf,
            cd_municipio                 = excluded.cd_municipio,
            cd_ddd1                      = excluded.cd_ddd1,
            nr_telefone1                 = excluded.nr_telefone1,
            cd_ddd2                      = excluded.cd_ddd2,
            nr_telefone2                 = excluded.nr_telefone2,
            cd_dddfax                    = excluded.cd_dddfax,
            nr_fax                       = excluded.nr_fax,
            nm_email                     = excluded.nm_email,
            nm_situacaoespecial          = excluded.nm_situacaoespecial,
            dt_datasituacaoespecial      = excluded.dt_datasituacaoespecial,
            dt_ultimaatualizacao         = excluded.dt_ultimaatualizacao
    """,
    # SQLite: ON CONFLICT sem target — funciona com índice de expressão (COALESCE).
    # PostgreSQL: target explícito com a mesma expressão do índice.
    # Chave lógica: (cd_cnpjbasico, COALESCE(cd_cpfcnpjsocio, nm_nomesociorazaosocial), cd_qualificacaosocio)
    "socios_sqlite": """
        INSERT INTO socio (
            cd_cnpjbasico, cd_identificadorsocio, nm_nomesociorazaosocial, cd_cpfcnpjsocio,
            cd_qualificacaosocio, dt_dataentradasociedade, cd_pais, cd_cpfrepresentantelegal,
            nm_nomerepresentante, cd_qualificacaorepresentantelegal, cd_faixaetaria,
            dt_ultimaatualizacao
        )
        SELECT
            cd_cnpjbasico, cd_identificadorsocio, nm_nomesociorazaosocial, cd_cpfcnpjsocio,
            cd_qualificacaosocio, dt_dataentradasociedade, cd_pais, cd_cpfrepresentantelegal,
            nm_nomerepresentante, cd_qualificacaorepresentantelegal, cd_faixaetaria,
            :mes
        FROM tmp_socios WHERE 1=1 ORDER BY cd_cnpjbasico, cd_cpfcnpjsocio, cd_qualificacaosocio
        ON CONFLICT DO UPDATE SET
            cd_identificadorsocio             = excluded.cd_identificadorsocio,
            nm_nomesociorazaosocial           = excluded.nm_nomesociorazaosocial,
            dt_dataentradasociedade           = excluded.dt_dataentradasociedade,
            cd_pais                           = excluded.cd_pais,
            cd_cpfrepresentantelegal          = excluded.cd_cpfrepresentantelegal,
            nm_nomerepresentante              = excluded.nm_nomerepresentante,
            cd_qualificacaorepresentantelegal = excluded.cd_qualificacaorepresentantelegal,
            cd_faixaetaria                    = excluded.cd_faixaetaria,
            dt_ultimaatualizacao              = excluded.dt_ultimaatualizacao
    """,
    "socios_postgres": """
        INSERT INTO socio (
            cd_cnpjbasico, cd_identificadorsocio, nm_nomesociorazaosocial, cd_cpfcnpjsocio,
            cd_qualificacaosocio, dt_dataentradasociedade, cd_pais, cd_cpfrepresentantelegal,
            nm_nomerepresentante, cd_qualificacaorepresentantelegal, cd_faixaetaria,
            dt_ultimaatualizacao
        )
        SELECT
            cd_cnpjbasico, cd_identificadorsocio, nm_nomesociorazaosocial, cd_cpfcnpjsocio,
            cd_qualificacaosocio, dt_dataentradasociedade, cd_pais, cd_cpfrepresentantelegal,
            nm_nomerepresentante, cd_qualificacaorepresentantelegal, cd_faixaetaria,
            :mes
        FROM tmp_socios WHERE 1=1 ORDER BY cd_cnpjbasico, cd_cpfcnpjsocio, cd_qualificacaosocio
        ON CONFLICT (cd_cnpjbasico, COALESCE(cd_cpfcnpjsocio, nm_nomesociorazaosocial), cd_qualificacaosocio)
        DO UPDATE SET
            cd_identificadorsocio             = excluded.cd_identificadorsocio,
            nm_nomesociorazaosocial           = excluded.nm_nomesociorazaosocial,
            dt_dataentradasociedade           = excluded.dt_dataentradasociedade,
            cd_pais                           = excluded.cd_pais,
            cd_cpfrepresentantelegal          = excluded.cd_cpfrepresentantelegal,
            nm_nomerepresentante              = excluded.nm_nomerepresentante,
            cd_qualificacaorepresentantelegal = excluded.cd_qualificacaorepresentantelegal,
            cd_faixaetaria                    = excluded.cd_faixaetaria,
            dt_ultimaatualizacao              = excluded.dt_ultimaatualizacao
    """,
}

# ---------------------------------------------------------------------------
# Helpers — SQLite e ZIP
# ---------------------------------------------------------------------------

def _to_sql(df, table: str, engine):
    """Escreve df na tabela usando conexão sqlite3 nativa (compatível pandas 3.x + SQLAlchemy 2.x)."""
    conn = engine.raw_connection()
    try:
        df.to_sql(table, conn, if_exists="append", index=False)
        conn.commit()
    finally:
        conn.close()


def _configurar_sqlite(engine):
    # Aplica PRAGMAs em TODA conexão nova criada pelo pool.
    # Sem isso, se o pool criar uma segunda conexão ela fica com os defaults lentos
    # (synchronous=NORMAL, cache=2000 páginas, temp_store=FILE, mmap=0).
    def _on_connect(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode       = WAL")
        cur.execute("PRAGMA synchronous        = OFF")
        cur.execute("PRAGMA cache_size         = -1048576")  # 1 GB
        cur.execute("PRAGMA temp_store         = MEMORY")
        cur.execute("PRAGMA mmap_size          = 137438953472")  # 128 GB (virtual, não aloca RAM física)
        cur.execute("PRAGMA threads            = 4")
        cur.execute("PRAGMA wal_autocheckpoint = 0")  # desliga auto-checkpoint; usamos PASSIVE manual por ZIP
        cur.close()

    event.listen(engine, "connect", _on_connect)

    # Inicializa a primeira conexão do pool (dispara _on_connect imediatamente).
    with engine.connect() as conn:
        conn.commit()


INDEXES_POR_TABELA = {
    "empresa":         [("ix_emp_razao",    "ON empresa(nm_razaosocial)")],
    "estabelecimento": [("ix_est_basico",   "ON estabelecimento(cd_cnpjbasico)"),
                        ("ix_est_fantasia", "ON estabelecimento(nm_nomefantasia)")],
    "socios":          [("ix_soc_basico",   "ON socio(cd_cnpjbasico)"),
                        ("ix_soc_cpf",      "ON socio(cd_cpfcnpjsocio)"),
                        ("ix_soc_nome",     "ON socio(nm_nomesociorazaosocial)")],
}
INDEXES_SECUNDARIOS = [ix for ixs in INDEXES_POR_TABELA.values() for ix in ixs]


def _todos_indexes_existem(engine) -> bool:
    with engine.connect() as conn:
        existentes = {r[0] for r in conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='index'"
        )).fetchall()}
    return all(nome in existentes for nome, _ in INDEXES_SECUNDARIOS)


def _dropar_todos_indexes(engine):
    with engine.connect() as conn:
        for nome, _ in INDEXES_SECUNDARIOS:
            conn.execute(text(f"DROP INDEX IF EXISTS {nome}"))
        conn.commit()
    with engine.connect() as conn:
        conn.execute(text("PRAGMA wal_checkpoint(PASSIVE)"))


def _criar_indexes_principais(engine):
    print("  Criando indices nas tabelas principais...")
    t_ck = time.time()
    print("  WAL checkpoint...", end="\r")
    with engine.connect() as conn:
        ck = conn.execute(text("PRAGMA wal_checkpoint(TRUNCATE)")).fetchone()
    print(f"  WAL checkpoint: {ck[2]}/{ck[1]} frames ({time.time() - t_ck:.1f}s)")
    with engine.connect() as conn:
        conn.execute(text("PRAGMA cache_size = -2097152"))  # 2 GB durante criação
        for nome, defn in INDEXES_SECUNDARIOS:
            ti = time.time()
            print(f"    {nome}...", end="\r")
            conn.execute(text(f"CREATE INDEX IF NOT EXISTS {nome} {defn}"))
            conn.commit()
            conn.execute(text("PRAGMA wal_checkpoint(PASSIVE)"))
            print(f"    {nome}: {time.time() - ti:.1f}s")
        conn.execute(text("PRAGMA cache_size = -1048576"))  # restaura 1 GB
        conn.commit()
    print("  Indices criados.")


def _garantir_indexes_tabela(engine, tabela: str):
    """No-op se todos os índices da tabela existem. Se algum falta (crash anterior), recria com otimizações."""
    with engine.connect() as conn:
        existentes = {r[0] for r in conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='index'"
        )).fetchall()}

    faltando = [(nome, defn) for nome, defn in INDEXES_POR_TABELA[tabela] if nome not in existentes]
    if not faltando:
        return

    print(f"  [garantir] {tabela}: {len(faltando)} indice(s) ausente(s) — recriando...")
    with engine.connect() as conn:
        conn.execute(text("PRAGMA wal_checkpoint(TRUNCATE)"))
    with engine.connect() as conn:
        conn.execute(text("PRAGMA cache_size = -2097152"))  # 2 GB durante criação
        for nome, defn in faltando:
            t_idx = time.time()
            print(f"    {nome}...", end="\r")
            conn.execute(text(f"CREATE INDEX IF NOT EXISTS {nome} {defn}"))
            conn.commit()
            print(f"    {nome}: {time.time() - t_idx:.1f}s")
        conn.execute(text("PRAGMA cache_size = -1048576"))  # restaura 1 GB
        conn.commit()
    with engine.connect() as conn:
        conn.execute(text("PRAGMA wal_checkpoint(PASSIVE)"))


def _dropar_indexes_tabela(engine, tabela: str):
    with engine.connect() as conn:
        for nome, _ in INDEXES_POR_TABELA[tabela]:
            conn.execute(text(f"DROP INDEX IF EXISTS {nome}"))
        conn.commit()
    # Checkpoint em conexão separada — dentro do mesmo with a conexão age como reader
    # e limita o que o PASSIVE consegue checkpointar.
    with engine.connect() as conn:
        conn.execute(text("PRAGMA wal_checkpoint(PASSIVE)"))


def _recriar_indexes_tabela(engine, tabela: str):
    t0 = time.time()
    # Usa conexão única para todos os índices da tabela:
    # - cache_size 2 GB aplicado a todos os CREATE INDEX (mais memória para sort, evita spill em disco)
    # - wal_checkpoint(PASSIVE) entre cada índice mantém o WAL pequeno para o próximo scan
    with engine.connect() as conn:
        conn.execute(text("PRAGMA cache_size = -2097152"))  # 2 GB temporariamente
        for nome, defn in INDEXES_POR_TABELA[tabela]:
            ti = time.time()
            print(f"    {nome}...", end="\r")
            conn.execute(text(f"CREATE INDEX IF NOT EXISTS {nome} {defn}"))
            conn.commit()
            conn.execute(text("PRAGMA wal_checkpoint(PASSIVE)"))
            print(f"    {nome}: {time.time() - ti:.1f}s")
        conn.execute(text("PRAGMA cache_size = -1048576"))  # restaura 1 GB
        conn.commit()
    print(f"  Indices de {tabela} recriados em {time.time() - t0:.1f}s")


def _listar_zips(mes: str, tabela: str) -> list[Path]:
    pasta = DADOS_BRUTOS / mes
    return sorted(pasta.glob(PADROES_ZIP[tabela]))


def _abrir_stream(zip_path: Path):
    """Abre o CSV dentro de um ZIP como stream de texto (sem extrair para disco)."""
    zf = zipfile.ZipFile(zip_path, "r")
    nomes = [n for n in zf.namelist() if not n.endswith("/")]
    if not nomes:
        zf.close()
        return None, None
    raw = zf.open(nomes[0])
    return zf, io.TextIOWrapper(raw, encoding="latin-1")


# ---------------------------------------------------------------------------
# Helpers — checkpoint por ZIP
# ---------------------------------------------------------------------------

def _get_checkpoint(engine, mes: str, tabela: str):
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT qtd_inseridos FROM tb_checkpoint_carga WHERE mes = :m AND tabela = :t"),
            {"m": mes, "t": tabela}
        ).fetchone()
    return row[0] if row else None


def _salvar_checkpoint(engine, mes: str, tabela: str, qtd: int):
    with engine.connect() as conn:
        conn.execute(
            text("INSERT OR IGNORE INTO tb_checkpoint_carga (mes, tabela, qtd_inseridos) VALUES (:m, :t, :q)"),
            {"m": mes, "t": tabela, "q": qtd}
        )
        conn.commit()


def _limpar_checkpoints(engine, mes: str):
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM tb_checkpoint_carga WHERE mes = :m"), {"m": mes})
        conn.commit()


# ---------------------------------------------------------------------------
# Helpers — tabela de controle
# ---------------------------------------------------------------------------

def _mes_status(engine, mes: str):
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT status FROM tb_processamento_mensal WHERE dt_referencia = :m ORDER BY id DESC LIMIT 1"),
            {"m": mes}
        ).fetchone()
    return row[0] if row else None


def _registrar(engine, mes: str, stats: dict, status: str):
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO tb_processamento_mensal (
                dt_referencia, dt_processado,
                qtd_inseridos_empresa, qtd_atualizados_empresa,
                qtd_inseridos_estabelecimento, qtd_atualizados_estabelecimento,
                qtd_inseridos_socios, qtd_atualizados_socios, status
            ) VALUES (
                :mes, :ts,
                :ie, :ae, :iest, :aest, :is_, :as_, :st
            )
        """), {
            "mes": mes,
            "ts":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ie":  stats.get("inseridos_empresa", 0),
            "ae":  stats.get("atualizados_empresa", 0),
            "iest": stats.get("inseridos_estabelecimento", 0),
            "aest": stats.get("atualizados_estabelecimento", 0),
            "is_": stats.get("inseridos_socios", 0),
            "as_": stats.get("atualizados_socios", 0),
            "st":  status,
        })
        conn.commit()


# ---------------------------------------------------------------------------
# Carga de domínios e Simples (uma única vez, do mês mais recente)
# ---------------------------------------------------------------------------

def _carregar_dominios_e_simples(engine):
    dominios = ["cnaes", "municipios", "naturezas", "qualificacoes", "motivos", "paises"]
    for tabela in dominios:
        tabela_db = TABELA_DB[tabela]
        with engine.connect() as conn:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {tabela_db}")).scalar()
        if count and count > 0:
            print(f"  {tabela_db}: ja carregado ({count:,} registros)")
            continue
        zips = _listar_zips(MES_DOMINIOS, tabela)
        if not zips:
            print(f"  [AVISO] {tabela}: nenhum ZIP em {MES_DOMINIOS}")
            continue
        total = 0
        for zp in zips:
            zf, stream = _abrir_stream(zp)
            if stream is None:
                continue
            try:
                df = pd.read_csv(stream, names=COLS[tabela], **CSV_PARAMS)
                _to_sql(df, tabela_db, engine)
                total += len(df)
            finally:
                zf.close()
        print(f"  {tabela_db}: {total:,} registros")

    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM simples")).scalar()
    if count and count > 0:
        print(f"  simples: ja carregado ({count:,} registros)")
        return
    zips = _listar_zips(MES_DOMINIOS, "simples")
    if not zips:
        print(f"  [AVISO] simples: nenhum ZIP em {MES_DOMINIOS}")
        return
    total = 0
    for zp in zips:
        zf, stream = _abrir_stream(zp)
        if stream is None:
            continue
        raw = engine.raw_connection()
        try:
            for chunk in pd.read_csv(stream, names=COLS["simples"], chunksize=CHUNK_SIZE, **CSV_PARAMS):
                chunk.to_sql("simples", raw, if_exists="append", index=False)
                total += len(chunk)
                print(f"    simples: {total:,}...", end="\r")
            raw.commit()
        finally:
            raw.close()
            zf.close()
    print(f"\n  simples: {total:,} registros")


# ---------------------------------------------------------------------------
# Processamento por ZIP — tmp isolada por ZIP, UPSERT, descarte
# ---------------------------------------------------------------------------

def _processar_zip(engine, mes: str, tabela: str, zp: Path) -> int:
    """
    Carrega um ZIP em tmp limpa, executa UPSERT na tabela principal, descarta tmp.
    Usa uma única conexão raw para todos os chunks (um commit ao final do ZIP).
    Duplicatas RF dentro do ZIP são resolvidas pelo ON CONFLICT DO UPDATE (idempotente).
    Retorna número de linhas lidas do ZIP.
    """
    tmp_nome = TMP_NOMES[tabela]

    with engine.connect() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {tmp_nome}"))
        conn.execute(text(SQL_CREATE_TMP[tabela]))
        conn.commit()

    zf, stream = _abrir_stream(zp)
    if stream is None:
        return 0

    zip_total = 0
    t_leitura = time.time()
    raw = engine.raw_connection()
    try:
        for chunk in pd.read_csv(stream, names=COLS[tabela], chunksize=CHUNK_SIZE, **CSV_PARAMS):
            chunk.to_sql(tmp_nome, raw, if_exists="append", index=False)
            zip_total += len(chunk)
            print(f"    {zp.name}: {zip_total:,} lidas...", end="\r")
        raw.commit()
    finally:
        raw.close()
        zf.close()

    t_upsert = time.time()
    print(f"\n  {zp.name}: {zip_total:,} linhas lidas ({t_upsert - t_leitura:.1f}s) → upsert...")
    upsert_key = tabela
    if tabela == "socios":
        upsert_key = "socios_postgres" if _is_postgres() else "socios_sqlite"
    with engine.connect() as conn:
        conn.execute(text("PRAGMA cache_size = -2097152"))  # 2 GB durante UPSERT
        conn.execute(text(SQL_INDEX_TMP[tabela]))
        conn.execute(text(SQL_UPSERT[upsert_key]), {"mes": mes})
        conn.execute(text(f"DROP TABLE IF EXISTS {tmp_nome}"))
        conn.commit()
        conn.execute(text("PRAGMA cache_size = -1048576"))  # restaura 1 GB
        conn.commit()
    print(f"  {zp.name}: concluido upsert ({time.time() - t_upsert:.1f}s)")
    with engine.connect() as conn:
        conn.execute(text("PRAGMA wal_checkpoint(TRUNCATE)"))

    return zip_total


# ---------------------------------------------------------------------------
# Processamento por mês — unificado (primeira carga e incrementais)
# ---------------------------------------------------------------------------

def _ha_mes_concluido(engine) -> bool:
    with engine.connect() as conn:
        count = conn.execute(
            text("SELECT COUNT(*) FROM tb_processamento_mensal WHERE status = 'CONCLUIDO'")
        ).scalar()
    return (count or 0) > 0


def _processar_tabelas(engine, mes: str, deferred_indexes: bool = False,
                       tabelas: list | None = None) -> dict:
    """
    Processa empresa, estabelecimento e socios via UPSERT por ZIP com checkpoints.
    Mesma lógica para primeira carga e incrementais — o UPSERT é idempotente nos dois casos.
    deferred_indexes=True: modo batch — sem drop/recreate por tabela; main() recria tudo no final.
    tabelas: subconjunto a processar neste mês; None = todas as três.
    """
    if tabelas is None:
        tabelas = ["empresa", "estabelecimento", "socios"]
    stats = {}

    for tabela in ["empresa", "estabelecimento", "socios"]:
        if tabela not in tabelas:
            continue
        tabela_db = TABELA_DB[tabela]
        zips = _listar_zips(mes, tabela)
        if not zips:
            print(f"  [AVISO] {tabela}: nenhum ZIP em {mes}")
            continue

        print(f"\n  --- {tabela_db} ---")

        # Compatibilidade: checkpoint de tabela do código anterior (chave sem "::") indica tabela concluída.
        if _get_checkpoint(engine, mes, tabela) is not None:
            print(f"  {tabela_db}: ja concluida (checkpoint anterior) — pulando.")
            stats[f"inseridos_{tabela}"]   = 0
            stats[f"atualizados_{tabela}"] = 0
            continue

        # Detecta checkpoints de ZIP órfãos: ZIP checkpoints existem mas tabela vazia.
        with engine.connect() as conn:
            ck_zip_count = conn.execute(text(
                "SELECT COUNT(*) FROM tb_checkpoint_carga WHERE mes=:m AND tabela LIKE :p"
            ), {"m": mes, "p": f"{tabela}::%"}).scalar() or 0

        if ck_zip_count > 0:
            # SELECT 1 LIMIT 1 — para na primeira linha encontrada, O(1), não varre a tabela.
            with engine.connect() as conn:
                tabela_vazia = not conn.execute(text(
                    f"SELECT 1 FROM {tabela_db} LIMIT 1"
                )).fetchone()
            if tabela_vazia:
                print(f"  {tabela_db}: checkpoints de ZIP encontrados mas tabela vazia — limpando para reprocessar.")
                with engine.connect() as conn:
                    conn.execute(text(
                        "DELETE FROM tb_checkpoint_carga WHERE mes=:m AND tabela LIKE :p"
                    ), {"m": mes, "p": f"{tabela}::%"})
                    conn.commit()
                ck_zip_count = 0

        tem_trabalho = ck_zip_count < len(zips)

        if not tem_trabalho:
            # Todos os ZIPs desta tabela já foram processados.
            # Em modo deferred, main() garante os índices no final; fora dele, safety net aqui.
            if not deferred_indexes:
                _garantir_indexes_tabela(engine, tabela)
            zip_total = sum(
                _get_checkpoint(engine, mes, f"{tabela}::{zp.name}") or 0
                for zp in zips
            )
            print(f"  {tabela_db}: 0 inseridos | {zip_total:,} atualizados")
            stats[f"inseridos_{tabela}"]   = 0
            stats[f"atualizados_{tabela}"] = zip_total
            continue

        # Tem ZIPs a processar: drop → process → recreate (pulado em modo deferred).
        if not deferred_indexes:
            _dropar_indexes_tabela(engine, tabela)
        # MAX(rowid) é O(1) — lê só a folha mais à direita do B-tree.
        # INSERT atribui rowid = MAX+1; ON CONFLICT DO UPDATE nunca altera rowid.
        # Logo: depois_rowid - antes_rowid = número exato de linhas novas.
        with engine.connect() as conn:
            antes_rowid = conn.execute(text(
                f"SELECT COALESCE(MAX(rowid), 0) FROM {tabela_db}"
            )).scalar()

        zip_total = 0
        for zp in zips:
            ck_key = f"{tabela}::{zp.name}"
            qtd_ck = _get_checkpoint(engine, mes, ck_key)
            if qtd_ck is not None:
                print(f"  {zp.name}: checkpoint ({qtd_ck:,} linhas) — pulando.")
                zip_total += qtd_ck
                continue

            qtd = _processar_zip(engine, mes, tabela, zp)
            zip_total += qtd
            _salvar_checkpoint(engine, mes, ck_key, qtd)

        if not deferred_indexes:
            # TRUNCATE: garante WAL zerado antes do CREATE INDEX.
            t_ck = time.time()
            print(f"  WAL checkpoint...", end="\r")
            with engine.connect() as conn:
                ck = conn.execute(text("PRAGMA wal_checkpoint(TRUNCATE)")).fetchone()
            print(f"  WAL checkpoint: {ck[2]}/{ck[1]} frames ({time.time() - t_ck:.1f}s)")
            _recriar_indexes_tabela(engine, tabela)

        with engine.connect() as conn:
            depois_rowid = conn.execute(text(
                f"SELECT COALESCE(MAX(rowid), 0) FROM {tabela_db}"
            )).scalar()
        inseridos   = depois_rowid - antes_rowid
        atualizados = zip_total - inseridos
        print(f"  {tabela_db}: {inseridos:,} inseridos | {atualizados:,} atualizados")
        stats[f"inseridos_{tabela}"]   = inseridos
        stats[f"atualizados_{tabela}"] = atualizados

    return stats


def processar_mes(engine, mes: str, forcar: bool = False, deferred_indexes: bool = False,
                  tabelas: list | None = None):
    status = _mes_status(engine, mes)

    if status == "CONCLUIDO" and not forcar:
        print(f"[{mes}] ja processado — pulando.")
        return

    if status == "ERRO":
        print(f"[{mes}] run anterior com ERRO — retomando do ultimo ZIP concluido...")

    tabelas_label = ", ".join(tabelas) if tabelas else "empresa, estabelecimento, socios"
    print(f"\n{'='*60}")
    print(f"  Processando: {mes}  [{tabelas_label}]")
    print(f"{'='*60}")
    t0 = time.time()

    eh_primeiro = not _ha_mes_concluido(engine)
    if not deferred_indexes:
        print(f"  Modo: {'PRIMEIRA CARGA' if eh_primeiro else 'INCREMENTAL'}")

    try:
        stats = _processar_tabelas(engine, mes, deferred_indexes=deferred_indexes, tabelas=tabelas)

        if eh_primeiro and not deferred_indexes:
            _criar_indexes_principais(engine)

        _limpar_checkpoints(engine, mes)
        _registrar(engine, mes, stats, "CONCLUIDO")
        with engine.connect() as conn:
            conn.execute(text("PRAGMA wal_checkpoint(TRUNCATE)"))

        elapsed = time.time() - t0
        m, s = divmod(int(elapsed), 60)
        print(f"  Concluido em {m}m {s}s")
        if not tabelas or "empresa" in tabelas:
            print(f"  Empresa:        +{stats.get('inseridos_empresa', 0):>10,}  ~{stats.get('atualizados_empresa', 0):>10,}")
        if not tabelas or "estabelecimento" in tabelas:
            print(f"  Estabelecimento:+{stats.get('inseridos_estabelecimento', 0):>10,}  ~{stats.get('atualizados_estabelecimento', 0):>10,}")
        if not tabelas or "socios" in tabelas:
            print(f"  Socios:         +{stats.get('inseridos_socios', 0):>10,}  ~{stats.get('atualizados_socios', 0):>10,}")

    except Exception as e:
        _registrar(engine, mes, {}, "ERRO")
        print(f"  ERRO ao processar {mes}: {e}")
        raise


# ---------------------------------------------------------------------------
# Listar meses disponíveis em dados-brutos/
# ---------------------------------------------------------------------------

def _listar_meses_disponiveis() -> list[str]:
    padrao = re.compile(r"^\d{4}-\d{2}$")
    meses = [
        p.name for p in sorted(DADOS_BRUTOS.iterdir())
        if p.is_dir() and padrao.match(p.name)
        and any(p.glob("Empresas*.zip"))
    ]
    return meses


def _show_status(engine):
    meses = _listar_meses_disponiveis()
    print(f"\n{'Mes':<10} {'Status':<12} {'Inseridos emp':>14} {'Atual. emp':>11} {'Inseridos est':>14} {'Inseridos soc':>14}")
    print("-" * 80)
    for mes in meses:
        with engine.connect() as conn:
            row = conn.execute(text("""
                SELECT status, qtd_inseridos_empresa, qtd_atualizados_empresa,
                       qtd_inseridos_estabelecimento, qtd_inseridos_socios
                FROM tb_processamento_mensal
                WHERE dt_referencia = :m ORDER BY id DESC LIMIT 1
            """), {"m": mes}).fetchone()
        if row:
            print(f"{mes:<10} {row[0]:<12} {row[1]:>14,} {row[2]:>11,} {row[3]:>14,} {row[4]:>14,}")
        else:
            print(f"{mes:<10} {'pendente':<12}")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _prevenir_sleep():
    """Impede o Windows de entrar em sleep enquanto o processo roda (ES_SYSTEM_REQUIRED)."""
    try:
        ES_CONTINUOUS      = 0x80000000
        ES_SYSTEM_REQUIRED = 0x00000001
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
        print("  [sleep] bloqueado pelo processo (SetThreadExecutionState)")
    except Exception:
        pass


def _restaurar_sleep():
    try:
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)  # ES_CONTINUOUS apenas
    except Exception:
        pass


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    _prevenir_sleep()
    try:
        _main()
    finally:
        _restaurar_sleep()


def _main():

    parser = argparse.ArgumentParser(description="Carga incremental da base CNPJ")
    parser.add_argument("--mes",    metavar="YYYY-MM", help="Processa apenas este mes")
    parser.add_argument("--status", action="store_true", help="Mostra situacao de cada mes")
    args = parser.parse_args()

    print(f"Banco        : {DATABASE_URL}")
    print(f"dados-brutos : {DADOS_BRUTOS}")
    print()

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

    print("Criando tabelas (se nao existirem)...")
    Base.metadata.create_all(bind=engine)

    # Índice de expressão que resolve NULL != NULL para estrangeiros sem CPF/CNPJ.
    # COALESCE(cd_cpfcnpjsocio, nm_nomesociorazaosocial) — se não tem CPF, usa o nome como chave.
    # Mesmo SQL funciona em SQLite e PostgreSQL.
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS ix_socio_chave_natural
            ON socio(cd_cnpjbasico,
                     COALESCE(cd_cpfcnpjsocio, nm_nomesociorazaosocial),
                     cd_qualificacaosocio)
        """))
        conn.commit()
    print("Indice ix_socio_chave_natural: OK")

    if args.status:
        _show_status(engine)
        return

    print("\n--- Dominios e Simples ---")
    _carregar_dominios_e_simples(engine)

    if args.mes:
        meses = [args.mes]
    else:
        meses = _listar_meses_disponiveis()

    pendentes = [m for m in meses if _mes_status(engine, m) != "CONCLUIDO"]

    # Modo batch: se há mais de um mês pendente OU se os índices secundários estão ausentes
    # (run anterior interrompido antes do CREATE INDEX final), processa sem drop/recreate por tabela
    # e cria todos os índices UMA VEZ ao final — economiza N×(drop+create) por tabela.
    deferred = not _todos_indexes_existem(engine) or len(pendentes) > 1

    # Modo otimizado para carga com múltiplos meses (carga inicial ou releitura):
    # - empresa + estabelecimento: apenas do mês mais recente (último snapshot contém tudo)
    # - socios: todos os meses (histórico de saída só existe nos snapshots anteriores)
    # Carga incremental (1 mês) processa sempre as três tabelas normalmente.
    otimizado = len(pendentes) > 1 and not args.mes

    if pendentes:
        if deferred:
            if otimizado:
                print(f"\n{len(pendentes)} mes(es) pendentes — modo batch otimizado.")
                print(f"  empresa + estabelecimento: apenas {pendentes[-1]} (ultimo snapshot)")
                print(f"  socios: todos os {len(pendentes)} meses (historico completo)")
            else:
                print(f"\n{len(pendentes)} mes(es) a processar — modo batch (indices criados ao final).")
            _dropar_todos_indexes(engine)
        else:
            print(f"\n{len(pendentes)} mes(es) a processar.")
        print()

        inicio_total = time.time()
        for mes in pendentes:
            if otimizado:
                tabelas = ["empresa", "estabelecimento", "socios"] if mes == pendentes[-1] else ["socios"]
            else:
                tabelas = None  # todas as tabelas
            processar_mes(engine, mes, deferred_indexes=deferred, tabelas=tabelas)

        elapsed = time.time() - inicio_total
        h, rem = divmod(int(elapsed), 3600)
        m, s   = divmod(rem, 60)
        print(f"\nCarga completa em {h}h {m}m {s}s")
    else:
        print("\nTodos os meses ja foram processados.")

    # Garante índices no final (cria apenas os ausentes — idempotente).
    if deferred:
        print("\n--- Criando indices secundarios ---")
        _criar_indexes_principais(engine)

    _show_status(engine)


if __name__ == "__main__":
    main()
