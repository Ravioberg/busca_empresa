import sqlite3, os
from pathlib import Path
BASE_DIR = Path(__file__).parent.parent.parent
db_path = str(BASE_DIR / "cnpj.db")
con = sqlite3.connect(db_path)
cur = con.cursor()

# Uma passagem só com GROUP BY — evita self-join em 70M linhas
cur.execute("""
    SELECT
        COUNT(*) as empresas,
        SUM(CASE WHEN sit_matriz = '08' AND tem_filial_ativa = 1 THEN 1 ELSE 0 END) as matriz_baixada_filial_ativa,
        SUM(CASE WHEN sit_matriz = '02' AND tem_filial_ativa = 0 AND total_estab > 1 THEN 1 ELSE 0 END) as matriz_ativa_todas_filiais_baixadas
    FROM (
        SELECT
            cd_cnpjbasico,
            MAX(CASE WHEN cd_cnpjordem = '0001' THEN cd_situacaocadastral END) as sit_matriz,
            MAX(CASE WHEN cd_cnpjordem != '0001' AND cd_situacaocadastral = '02' THEN 1 ELSE 0 END) as tem_filial_ativa,
            COUNT(*) as total_estab
        FROM estabelecimento
        GROUP BY cd_cnpjbasico
    )
""")
r = cur.fetchone()
print(f"Total empresas com estabelecimentos : {r[0]:>12,}")
print(f"Matriz BAIXADA + filial ATIVA       : {r[1]:>12,}")
print(f"Matriz ATIVA + todas filiais BAIXADAS: {r[2]:>12,}")

print()
print("Exemplos (matriz baixada, filial ativa):")
cur.execute("""
    SELECT cd_cnpjbasico, sit_matriz, sit_filiais
    FROM (
        SELECT
            cd_cnpjbasico,
            MAX(CASE WHEN cd_cnpjordem = '0001' THEN cd_situacaocadastral END) as sit_matriz,
            GROUP_CONCAT(CASE WHEN cd_cnpjordem != '0001' THEN cd_cnpjordem||':'||cd_situacaocadastral END) as sit_filiais,
            MAX(CASE WHEN cd_cnpjordem != '0001' AND cd_situacaocadastral = '02' THEN 1 ELSE 0 END) as tem_filial_ativa
        FROM estabelecimento
        GROUP BY cd_cnpjbasico
    )
    WHERE sit_matriz = '08' AND tem_filial_ativa = 1
    LIMIT 5
""")
for r in cur.fetchall():
    print(f"  CNPJ basico {r[0]} | matriz={r[1]} | filiais={r[2][:80]}")

con.close()
