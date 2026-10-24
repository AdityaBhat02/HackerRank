import sqlite3
import glob
import json

for p in sorted(glob.glob('dataset/evidence/databases/*')):
    conn = sqlite3.connect(':memory:')
    try:
        with open(p, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cur.fetchall()]
        for tbl in tables:
            if tbl.startswith('customer_data_') or 'replica' in tbl:
                # check columns
                cur.execute(f"PRAGMA table_info({tbl});")
                cols = [c[1] for c in cur.fetchall()]
                cur.execute(f"SELECT COUNT(*) FROM {tbl};")
                cnt = cur.fetchone()[0]
                
                # Check for tombstone
                if 'resource_id' in cols:
                    cur.execute(f"SELECT resource_id, origin_system FROM {tbl} WHERE resource_id LIKE '%tombstone%'")
                    tombstones = cur.fetchall()
                    if tombstones:
                        print(f"File: {p}, Table: {tbl}, Total rows: {cnt}, Tombstones: {len(tombstones)}: {tombstones[:3]}")
    except Exception as e:
        print(f"{p}: error ({e})")
