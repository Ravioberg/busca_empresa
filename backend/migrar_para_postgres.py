"""
Script de migração SQLite → PostgreSQL.

Passos:
1. Configure DATABASE_URL no .env apontando para o PostgreSQL
2. Execute: py -3.12 migrar_para_postgres.py

O script cria as tabelas, ativa pg_trgm e cria os índices de busca.
A migração dos dados em si é feita re-rodando o carga.py contra o Postgres,
ou usando o modo --apenas-indices se os dados já foram importados.
"""
import sys
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "")

if not (DATABASE_URL.startswith("postgresql") or DATABASE_URL.startswith("postgres")):
    print("ERRO: DATABASE_URL não aponta para PostgreSQL.")
    print(f"  Atual: {DATABASE_URL}")
    sys.exit(1)

from sqlalchemy import create_engine, text
import models  # garante que todos os models são importados
from database import Base

engine = create_engine(DATABASE_URL)

print("Conectado ao PostgreSQL.")

with engine.connect() as conn:

    print("\n[1/3] Criando tabelas...")
    Base.metadata.create_all(bind=engine)
    print("      Tabelas criadas.")

    print("\n[2/3] Ativando extensão pg_trgm (busca por substring)...")
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
    conn.commit()
    print("      pg_trgm ativo.")

    print("\n[3/3] Criando índices GIN trigram para busca por nome...")

    indices = [
        ("idx_empresa_razao_trgm",
         "CREATE INDEX IF NOT EXISTS idx_empresa_razao_trgm ON empresa USING GIN(nm_razaosocial gin_trgm_ops)"),

        ("idx_estab_fantasia_trgm",
         "CREATE INDEX IF NOT EXISTS idx_estab_fantasia_trgm ON estabelecimento USING GIN(nm_nomefantasia gin_trgm_ops)"),

        ("idx_socio_nome_trgm",
         "CREATE INDEX IF NOT EXISTS idx_socio_nome_trgm ON socio USING GIN(nm_nomesociorazaosocial gin_trgm_ops)"),

        ("idx_socio_cpf_trgm",
         "CREATE INDEX IF NOT EXISTS idx_socio_cpf_trgm ON socio USING GIN(cd_cpfcnpjsocio gin_trgm_ops)"),

        ("idx_socio_cnpjbasico",
         "CREATE INDEX IF NOT EXISTS idx_socio_cnpjbasico ON socio(cd_cnpjbasico)"),

        ("idx_estab_cnpjbasico",
         "CREATE INDEX IF NOT EXISTS idx_estab_cnpjbasico ON estabelecimento(cd_cnpjbasico)"),
    ]

    for nome, sql in indices:
        print(f"      [{nome}]...", end=" ", flush=True)
        conn.execute(text(sql))
        conn.commit()
        print("OK")

print("\nMigração concluída.")
print("Próximo passo: rode o carga.py com o DATABASE_URL apontando para o PostgreSQL.")
