"""
Gera cnpj_demo.db — banco de demonstração com dados fictícios.

Uso:
    py -3.12 gerar_demo.py

Depois edite o .env:
    DATABASE_URL=sqlite:///./cnpj_demo.db

E reinicie o uvicorn.
"""
import sqlite3
import unicodedata
import os

from pathlib import Path
BASE_DIR = Path(__file__).parent.parent.parent
DB_PATH = str(BASE_DIR / "cnpj_demo.db")
MES_ATUAL = "2026-04"
MES_ANTIGO = "2023-06"

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=NORMAL")


def norm(t):
    if not t:
        return None
    return unicodedata.normalize("NFD", t).encode("ascii", "ignore").decode("ascii").upper()


conn.create_function("normalizar", 1, norm)

# ── Tabelas principais ────────────────────────────────────────────────────────

conn.executescript("""
CREATE TABLE tb_processamento_mensal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dt_referencia TEXT, dt_processado TEXT,
    qtd_inseridos_empresa INTEGER DEFAULT 0,
    qtd_atualizados_empresa INTEGER DEFAULT 0,
    qtd_inseridos_estabelecimento INTEGER DEFAULT 0,
    qtd_atualizados_estabelecimento INTEGER DEFAULT 0,
    qtd_inseridos_socios INTEGER DEFAULT 0,
    qtd_atualizados_socios INTEGER DEFAULT 0,
    status TEXT
);

CREATE TABLE tb_checkpoint_carga (
    mes TEXT, tabela TEXT,
    qtd_inseridos INTEGER DEFAULT 0,
    PRIMARY KEY (mes, tabela)
);

CREATE TABLE empresa (
    cd_cnpjbasico TEXT PRIMARY KEY,
    nm_razaosocial TEXT,
    cd_naturezajuridica TEXT,
    cd_qualificacaoresponsavel TEXT,
    vl_capitalsocial TEXT,
    cd_porteempresa TEXT,
    nm_entefederativo TEXT,
    dt_primeiracarga TEXT,
    dt_ultimaatualizacao TEXT
);

CREATE TABLE estabelecimento (
    cd_cnpjbasico TEXT NOT NULL,
    cd_cnpjordem TEXT NOT NULL,
    cd_cnpjdv TEXT,
    cd_identificadormatrizfilial TEXT,
    nm_nomefantasia TEXT,
    cd_situacaocadastral TEXT,
    dt_datasituacaocadastral TEXT,
    cd_motivosituacaocadastral TEXT,
    nm_cidadeexterior TEXT,
    cd_pais TEXT,
    dt_datainicioatividade TEXT,
    cd_cnaefiscalprincipal TEXT,
    ds_cnaefiscalsecundaria TEXT,
    nm_tipologradouro TEXT,
    nm_logradouro TEXT,
    nm_numero TEXT,
    nm_complemento TEXT,
    nm_bairro TEXT,
    cd_cep TEXT,
    sg_uf TEXT,
    cd_municipio TEXT,
    cd_ddd1 TEXT, nr_telefone1 TEXT,
    cd_ddd2 TEXT, nr_telefone2 TEXT,
    cd_dddfax TEXT, nr_fax TEXT,
    nm_email TEXT,
    nm_situacaoespecial TEXT,
    dt_datasituacaoespecial TEXT,
    dt_ultimaatualizacao TEXT,
    PRIMARY KEY (cd_cnpjbasico, cd_cnpjordem)
);

CREATE TABLE socio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cd_cnpjbasico TEXT,
    cd_identificadorsocio TEXT,
    nm_nomesociorazaosocial TEXT,
    cd_cpfcnpjsocio TEXT,
    cd_qualificacaosocio TEXT,
    dt_dataentradasociedade TEXT,
    cd_pais TEXT,
    cd_cpfrepresentantelegal TEXT,
    nm_nomerepresentante TEXT,
    cd_qualificacaorepresentantelegal TEXT,
    cd_faixaetaria TEXT,
    dt_ultimaatualizacao TEXT,
    UNIQUE (cd_cnpjbasico, cd_cpfcnpjsocio, cd_qualificacaosocio)
);

CREATE TABLE simples (
    cd_cnpjbasico TEXT PRIMARY KEY,
    fl_opcaosimples TEXT,
    dt_dataopcaosimples TEXT,
    dt_dataexclusaosimples TEXT,
    fl_opcaomei TEXT,
    dt_dataopcaomei TEXT,
    dt_dataexclusaomei TEXT
);

CREATE TABLE cnae (
    cd_cnae TEXT PRIMARY KEY,
    ds_cnae TEXT
);

CREATE TABLE municipio (
    cd_municipio TEXT PRIMARY KEY,
    nm_municipio TEXT
);

CREATE TABLE natureza (
    cd_naturezajuridica TEXT PRIMARY KEY,
    ds_naturezajuridica TEXT
);

CREATE TABLE qualificacao (
    cd_qualificacao TEXT PRIMARY KEY,
    ds_qualificacao TEXT
);

CREATE TABLE motivo (
    cd_motivosituacaocadastral TEXT PRIMARY KEY,
    ds_motivosituacaocadastral TEXT
);

CREATE TABLE pais (
    cd_pais TEXT PRIMARY KEY,
    nm_pais TEXT
);
""")

# ── Lookup tables ─────────────────────────────────────────────────────────────

conn.executemany("INSERT INTO cnae VALUES (?,?)", [
    ("6201500", "Desenvolvimento de programas de computador sob encomenda"),
    ("6202300", "Desenvolvimento e licenciamento de programas de computador customizáveis"),
    ("6203100", "Desenvolvimento e licenciamento de programas de computador não customizáveis"),
    ("7020400", "Atividades de consultoria em gestão empresarial"),
    ("6911701", "Serviços advocatícios"),
    ("4120400", "Construção de edifícios"),
    ("4211101", "Construção de rodovias e ferrovias"),
    ("4312600", "Perfurações e sondagens"),
    ("4711302", "Comércio varejista de mercadorias em geral"),
    ("6619302", "Correspondentes de instituições financeiras"),
])

conn.executemany("INSERT INTO municipio VALUES (?,?)", [
    ("7107", "SAO PAULO"),
    ("6001", "RIO DE JANEIRO"),
    ("4123", "BELO HORIZONTE"),
    ("8105", "CURITIBA"),
    ("8901", "PORTO ALEGRE"),
])

conn.executemany("INSERT INTO natureza VALUES (?,?)", [
    ("2062", "Sociedade Empresária Limitada"),
    ("2305", "Empresário (Individual)"),
    ("2135", "Sociedade Anônima Fechada"),
])

conn.executemany("INSERT INTO qualificacao VALUES (?,?)", [
    ("05", "Administrador"),
    ("08", "Conselheiro de Administração"),
    ("10", "Diretor"),
    ("16", "Presidente"),
    ("17", "Procurador"),
    ("20", "Sócio"),
    ("22", "Sócio-Administrador"),
    ("49", "Sócio-Ostensivo"),
])

conn.executemany("INSERT INTO motivo VALUES (?,?)", [
    ("00", "Sem Motivo"),
    ("01", "Extinção Por Encerramento Liquidação Voluntária"),
    ("63", "Omissão de Declarações"),
    ("78", "Baixa Iniciativa Própria"),
])

conn.executemany("INSERT INTO pais VALUES (?,?)", [
    ("105", "BRASIL"),
])

# ── tb_processamento_mensal ───────────────────────────────────────────────────

conn.execute("""
    INSERT INTO tb_processamento_mensal
        (dt_referencia, dt_processado, qtd_inseridos_empresa, qtd_inseridos_socios, status)
    VALUES (?, '2026-04-15 10:00:00', 4, 9, 'CONCLUIDO')
""", (MES_ATUAL,))

# ── Empresas ──────────────────────────────────────────────────────────────────
# (basico, razao, natureza, qualif_resp, capital, porte, ente, dt_carga, dt_atualizacao)

conn.executemany("""
    INSERT INTO empresa VALUES (?,?,?,?,?,?,?,?,?)
""", [
    ("12345678", "PYTHAGORAS TECNOLOGIA LTDA",              "2062", "22", "50000,00",  "01", "", MES_ATUAL, MES_ATUAL),
    ("23456789", "PYTHAGORAS CONSULTORIA EMPRESARIAL LTDA", "2062", "22", "30000,00",  "01", "", MES_ATUAL, MES_ATUAL),
    ("34567890", "SOLAR ENGENHARIA E CONSTRUCOES LTDA",     "2062", "10", "200000,00", "03", "", MES_ATUAL, MES_ATUAL),
    ("45678901", "TECH INOVACOES LTDA",                     "2062", "20", "10000,00",  "00", "", MES_ATUAL, MES_ATUAL),
    ("56789012", "DISTRIBUIDORA CENTRAL COMERCIO LTDA",     "2062", "20", "80000,00",  "01", "", MES_ATUAL, MES_ATUAL),
])

# ── Estabelecimentos ──────────────────────────────────────────────────────────
# (basico, ordem, dv, matfil, fantasia, situacao, dt_sit, motivo, cidade_ext, pais,
#  dt_inicio, cnae_princ, cnae_sec, tipo_log, logradouro, numero, compl, bairro,
#  cep, uf, municipio, ddd1, tel1, ddd2, tel2, dddfax, fax, email, sit_esp, dt_sit_esp, dt_atu)

conn.executemany("""
    INSERT INTO estabelecimento VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
""", [
    ("12345678","0001","90","1","PYTHAGORAS TECH",    "02","20150301","00","","105","20150301","6201500","6202300,6203100","RUA","PAULISTA","1000","CONJ 51","BELA VISTA","01310100","SP","7107","11","33445566","","","","","contato@pythagoras.com.br","","",MES_ATUAL),
    ("23456789","0001","72","1","PYTHAGORAS CONSULT", "02","20180601","00","","105","20180601","7020400","6201500",        "AV", "BRIGADEIRO","500","SALA 12","JARDIM PAULISTA","01401000","SP","7107","11","22334455","","","","","consultoria@pythagoras.com.br","","",MES_ATUAL),
    ("34567890","0001","45","1","SOLAR ENGENHARIA",   "02","20190101","00","","105","20190101","4120400","4211101,4312600","AV", "ATLANTICA","200","","COPACABANA","22010000","RJ","6001","21","99887766","","","","","solar@engenharia.com.br","","",MES_ATUAL),
    ("45678901","0001","12","1",None,                 "08","20240101","78","","105","20200901","6201500","",              "RUA","FUNCHAL","200","","VILA OLIMPIA","04551060","MG","4123","31","12345678","","","","","","","",MES_ANTIGO),
    ("56789012","0001","34","1","DISTRIBUIDORA CENTRAL","02","20210301","00","","105","20210301","4711302","6619302",     "RUA","DAS FLORES","50","","CENTRO","80010100","SP","8105","41","33221100","","","","","","","",MES_ATUAL),
])

# ── Sócios ────────────────────────────────────────────────────────────────────
# (basico, id_socio, nome, cpf, qualif, entrada, pais, cpf_rep, nm_rep, qualif_rep, faixa, dt_atu)

NOME_MARIA = "MARIA SILVA"
CPF_MARIA = "***123456**"
NOME_JOAO = "JOAO SANTOS"
CPF_JOAO = "***234567**"
NOME_CARLOS = "CARLOS PEREIRA"
CPF_CARLOS = "***345678**"

socios = [
    # MARIA SILVA — ativa em 2 empresas, ex-sócia em 1
    ("12345678", "1", NOME_MARIA, CPF_MARIA, "22", "20150301", "105", "", "", "", "5", MES_ATUAL),
    ("23456789", "1", NOME_MARIA, CPF_MARIA, "05", "20180601", "105", "", "", "", "5", MES_ATUAL),
    ("45678901", "1", NOME_MARIA, CPF_MARIA, "20", "20200901", "105", "", "", "", "5", MES_ANTIGO),  # ex-sócia

    # JOAO SANTOS — ativo em 2 empresas (em comum com MARIA)
    ("12345678", "1", NOME_JOAO, CPF_JOAO, "20", "20150301", "105", "", "", "", "4", MES_ATUAL),
    ("23456789", "1", NOME_JOAO, CPF_JOAO, "20", "20180601", "105", "", "", "", "4", MES_ATUAL),

    # CARLOS PEREIRA — ativo em 2 empresas (1 em comum com MARIA)
    ("12345678", "1", NOME_CARLOS, CPF_CARLOS, "22", "20150301", "105", "", "", "", "6", MES_ATUAL),
    ("34567890", "1", NOME_CARLOS, CPF_CARLOS, "22", "20190101", "105", "", "", "", "6", MES_ATUAL),

    # ANA OLIVEIRA — ativa em 1 empresa
    ("34567890","1","ANA OLIVEIRA",   "***456789**","20","20190101","105","","","","4",MES_ATUAL),

    # ROBERTO MENDES — ativo em 1 empresa
    ("56789012","1","ROBERTO MENDES", "***567890**","22","20210301","105","","","","5",MES_ATUAL),
]

conn.executemany("""
    INSERT INTO socio
        (cd_cnpjbasico, cd_identificadorsocio, nm_nomesociorazaosocial,
         cd_cpfcnpjsocio, cd_qualificacaosocio, dt_dataentradasociedade,
         cd_pais, cd_cpfrepresentantelegal, nm_nomerepresentante,
         cd_qualificacaorepresentantelegal, cd_faixaetaria, dt_ultimaatualizacao)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
""", socios)

# ── Simples Nacional ──────────────────────────────────────────────────────────

conn.executemany("INSERT INTO simples VALUES (?,?,?,?,?,?,?)", [
    ("12345678","S","20150301",None,"N",None,None),
    ("23456789","S","20180601",None,"N",None,None),
    ("34567890","N",None,None,"N",None,None),
    ("45678901","S","20200901","20240101","N",None,None),
    ("56789012","S","20210301",None,"N",None,None),
])

# ── Índices B-tree ────────────────────────────────────────────────────────────

conn.executescript("""
    CREATE INDEX IF NOT EXISTS idx_socio_cnpjbasico ON socio(cd_cnpjbasico);
    CREATE INDEX IF NOT EXISTS idx_socio_cpf        ON socio(cd_cpfcnpjsocio);
    CREATE INDEX IF NOT EXISTS idx_estab_fantasia   ON estabelecimento(nm_nomefantasia);
""")

# ── FTS5 — busca empresa ──────────────────────────────────────────────────────

conn.executescript("""
    DROP TABLE IF EXISTS fts_empresa;
    CREATE VIRTUAL TABLE fts_empresa USING fts5(
        cd_cnpjbasico        UNINDEXED,
        nm_razaosocial,
        nm_nomefantasia,
        cd_situacaocadastral UNINDEXED,
        fl_matriz            UNINDEXED,
        tokenize = 'trigram'
    );
""")

conn.execute("""
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
""")

# ── FTS5 — busca sócio ────────────────────────────────────────────────────────

conn.executescript("""
    DROP TABLE IF EXISTS fts_socio;
    CREATE VIRTUAL TABLE fts_socio USING fts5(
        rowid_ref UNINDEXED,
        nm_nomesociorazaosocial,
        tokenize = 'trigram'
    );
""")

conn.execute("""
    INSERT INTO fts_socio(rowid_ref, nm_nomesociorazaosocial)
    SELECT id, normalizar(nm_nomesociorazaosocial) FROM socio
""")

conn.commit()
conn.close()

print("=" * 55)
print("  cnpj_demo.db criado com sucesso!")
print("=" * 55)
print()
print("Dados incluídos:")
print("  5 empresas  — PYTHAGORAS TECNOLOGIA, PYTHAGORAS CONSULTORIA,")
print("                SOLAR ENGENHARIA, TECH INOVACOES (baixada),")
print("                DISTRIBUIDORA CENTRAL")
print("  5 sócios    — MARIA SILVA, JOAO SANTOS, CARLOS PEREIRA,")
print("                ANA OLIVEIRA, ROBERTO MENDES")
print()
print("Para usar este banco, edite o arquivo .env na pasta backend:")
print("  DATABASE_URL=sqlite:///./cnpj_demo.db")
print()
print("Depois reinicie o uvicorn:")
print("  py -3.12 -m uvicorn app.main:app --reload")
