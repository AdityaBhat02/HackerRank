import sqlite3

conn = sqlite3.connect(':memory:')
with open('dataset/evidence/databases/customer_data_reporting_replica_20260305.sql', encoding='utf-8') as f:
    conn.executescript(f.read())
cur = conn.cursor()
cur.execute("SELECT * FROM customer_data_reporting_replica WHERE resource_id='legal_hold_5622'")
print(cur.fetchall())
