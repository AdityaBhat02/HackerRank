import sqlite3
import json

conn = sqlite3.connect(':memory:')
with open('dataset/evidence/databases/customer_data_failover_replica_20260920.sql', 'r', encoding='utf-8') as f:
    conn.executescript(f.read())
cur = conn.cursor()
cur.execute("SELECT resource_id, origin_system, record_json FROM customer_data_failover_replica")
rows = cur.fetchall()
print(f"Total rows in customer_data_failover_replica: {len(rows)}")
for r in rows:
    res_id, orig, rjson_str = r
    try:
        rj = json.loads(rjson_str)
    except:
        rj = rjson_str
    print(f"[{orig}] {res_id} -> {rj}")
