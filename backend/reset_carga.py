"""
Limpa as tabelas de dados principais e controles de carga,
mantendo dominios (cnae, municipio, natureza, qualificacao, motivo, pais) e simples intactos.
"""
import sys
from pathlib import Path
from sqlalchemy import create_engine, text

BASE_DIR = Path(__file__).parent
DATABASE_URL = f"sqlite:///{BASE_DIR / 'cnpj.db'}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False, "timeout": 60})

TABELAS_LIMPAR = [
    "socio",
    "estabelecimento",
    "empresa",
    "tb_checkpoint_carga",
    "tb_processamento_mensal",
    "tmp_empresa",
    "tmp_estabelecimento",
    "tmp_socios",
]

with engine.connect() as conn:
    for tabela in TABELAS_LIMPAR:
        try:
            conn.execute(text(f"DELETE FROM {tabela}"))
            print(f"  {tabela}: limpa")
        except Exception as e:
            print(f"  {tabela}: nao encontrada ou ja vazia ({e})")
    conn.commit()

print("\nPronto. Dominios e Simples mantidos. Rode carga.py para reiniciar.")
