import sqlite3

conn = sqlite3.connect(':memory:')
conn.executescript(open('dataset/evidence/databases/customer_accounts_failover_replica_20260902.sql', encoding='utf-8').read())
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print('Tables in evidence_54:', tables)
for t in tables:
    cur.execute(f"SELECT * FROM {t} WHERE resource_id in ('account_001', 'account_002', 'account_004', 'account_005')")
    print(f"Rows in {t}:")
    for r in cur.fetchall():
        print(" ", r)
