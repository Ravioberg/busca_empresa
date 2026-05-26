import sqlite3, os
from pathlib import Path
BASE_DIR = Path(__file__).parent.parent.parent
db_path = str(BASE_DIR / "cnpj.db")
con = sqlite3.connect(db_path)
cur = con.cursor()

print("=" * 60)
print("DIAGNOSTICO DO BANCO DE DADOS")
print("=" * 60)

# 1. Totais gerais
print("\n--- Totais por tabela ---")
for tabela in ['empresa', 'estabelecimento', 'socio', 'simples']:
    cur.execute(f'SELECT COUNT(*) FROM {tabela}')
    print(f"  {tabela:<20}: {cur.fetchone()[0]:>14,}")

# 2. Consistencia empresa: total vs soma por dt_primeiracarga
print("\n--- Consistencia empresa ---")
cur.execute('SELECT COUNT(*) FROM empresa')
total_emp = cur.fetchone()[0]
cur.execute('SELECT SUM(c) FROM (SELECT COUNT(*) as c FROM empresa GROUP BY dt_primeiracarga)')
soma_pc = cur.fetchone()[0]
print(f"  Total empresa           : {total_emp:>14,}")
print(f"  Soma por dt_primeiracarga: {soma_pc:>14,}")
print(f"  Bate: {total_emp == soma_pc}  |  Diferenca: {total_emp - soma_pc:,}")

# 3. Faixa de datas
print("\n--- Faixa de datas ---")
cur.execute('SELECT MIN(dt_primeiracarga), MAX(dt_primeiracarga) FROM empresa')
r = cur.fetchone()
print(f"  empresa.dt_primeiracarga : {r[0]} a {r[1]}")
cur.execute('SELECT MIN(dt_ultimaatualizacao), MAX(dt_ultimaatualizacao) FROM empresa')
r = cur.fetchone()
print(f"  empresa.dt_ultimaatual   : {r[0]} a {r[1]}")
cur.execute('SELECT MIN(dt_ultimaatualizacao), MAX(dt_ultimaatualizacao) FROM estabelecimento')
r = cur.fetchone()
print(f"  estabelecimento.dt_ultima: {r[0]} a {r[1]}")
cur.execute('SELECT MIN(dt_ultimaatualizacao), MAX(dt_ultimaatualizacao) FROM socio')
r = cur.fetchone()
print(f"  socio.dt_ultima          : {r[0]} a {r[1]}")

# 4. Cruzamento: tracking vs dt_primeiracarga real
print("\n--- Tracking (tb_processamento) vs Real (dt_primeiracarga) ---")
cur.execute('''
    SELECT dt_referencia, qtd_inseridos_empresa
    FROM tb_processamento_mensal
    WHERE status = 'CONCLUIDO'
    ORDER BY dt_referencia, id DESC
''')
proc = {}
for row in cur.fetchall():
    if row[0] not in proc:
        proc[row[0]] = row[1]

cur.execute('SELECT dt_primeiracarga, COUNT(*) FROM empresa GROUP BY dt_primeiracarga ORDER BY dt_primeiracarga')
real = dict(cur.fetchall())

print(f"  {'Mes':<10} {'Tracking':>12} {'Real':>12} {'Diff':>10}  Status")
print(f"  {'-'*10} {'-'*12} {'-'*12} {'-'*10}  ------")
total_track = 0
total_real = 0
for mes in sorted(set(list(proc.keys()) + list(real.keys()))):
    t = proc.get(mes, 0)
    r = real.get(mes, 0)
    d = r - t
    total_track += t
    total_real += r
    if d == 0:
        flag = 'OK'
    elif d > 0:
        flag = f'DIFF +{d:,}'
    else:
        flag = f'DIFF {d:,}'
    marker = '  <---' if d != 0 else ''
    print(f"  {mes:<10} {t:>12,} {r:>12,} {d:>10,}  {flag}{marker}")
print(f"  {'TOTAL':<10} {total_track:>12,} {total_real:>12,} {total_real - total_track:>10,}")

# 5. Meses faltando (nenhum registro com aquela data)
print("\n--- Meses com 0 empresas novas (dt_primeiracarga) ---")
meses_esperados = []
from datetime import date
d = date(2023, 3, 1)
while d <= date(2026, 4, 1):
    meses_esperados.append(d.strftime('%Y-%m'))
    if d.month == 12:
        d = d.replace(year=d.year+1, month=1)
    else:
        d = d.replace(month=d.month+1)

for mes in meses_esperados:
    if mes not in real:
        print(f"  {mes}: NENHUMA empresa com dt_primeiracarga neste mes!")
    elif real[mes] == 0:
        print(f"  {mes}: 0 empresas (suspeito)")

# 6. Anomalia 2024-11 vs 2024-12
print("\n--- Anomalia 2024-11 vs 2024-12 (atualizados empresa) ---")
cur.execute('''
    SELECT dt_referencia, qtd_inseridos_empresa, qtd_atualizados_empresa
    FROM tb_processamento_mensal
    WHERE status = 'CONCLUIDO' AND dt_referencia IN ('2024-11', '2024-12')
    ORDER BY dt_referencia, id DESC
''')
for row in cur.fetchall():
    print(f"  {row[0]}: inseridos={row[1]:,}  atualizados={row[2]:,}")
print("  Obs: 'atualizados' = total de linhas no arquivo RF daquele mes")
print("  Uma diferenca de 1 significa que a RF tinha 1 empresa a menos no arquivo de dez/2024")
print("  Isso e normal: a RF pode cancelar/anular CNPJs entre meses")
print("  O registro ainda existe no banco (UPSERT nunca deleta)")

con.close()
print("\n" + "=" * 60)
print("FIM DO DIAGNOSTICO")
print("=" * 60)
