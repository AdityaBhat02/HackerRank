import sqlite3
import glob

for p in sorted(glob.glob('dataset/evidence/databases/*.sql')):
    conn = sqlite3.connect(':memory:')
    try:
        with open(p, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cur.fetchall()]
        if 'customer_data_primary' in tables and len(tables) > 1:
            other_tbl = [t for t in tables if t != 'customer_data_primary'][0]
            cur.execute(f"SELECT resource_id FROM customer_data_primary")
            p_res = set(r[0] for r in cur.fetchall())
            cur.execute(f"SELECT resource_id FROM {other_tbl}")
            o_res = set(r[0] for r in cur.fetchall())
            print(f"{p}:")
            print(f"  primary count: {len(p_res)}, {other_tbl} count: {len(o_res)}")
            print(f"  in primary but not in {other_tbl}: {p_res - o_res}")
            print(f"  in {other_tbl} but not in primary: {o_res - p_res}")
    except Exception as e:
        print(f"{p}: error {e}")
