import sqlite3
import json

conn = sqlite3.connect(':memory:')
with open('dataset/evidence/databases/customer_data_failover_replica_20260920.sql', encoding='utf-8') as f:
    conn.executescript(f.read())

cur = conn.cursor()
cur.execute("SELECT resource_id, origin_system, record_category, record_json, captured_at FROM customer_data_failover_replica")
rows = cur.fetchall()
print(f"Total rows in customer_data_failover_replica: {len(rows)}")
for r in rows:
    res_id, origin_sys, cat, rjson_str, cap_at = r
    rj = json.loads(rjson_str)
    print(f"[{res_id}] origin={origin_sys}, cat={cat}, user={rj.get('subject_reference')}, name={rj.get('name')}, email={rj.get('email')}, phone={rj.get('phone')}, hash={rj.get('email_hash')}")
