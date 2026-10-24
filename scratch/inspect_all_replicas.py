import sqlite3
import glob

files = sorted(glob.glob('dataset/evidence/databases/*.sql'))
for p in files:
    conn = sqlite3.connect(':memory:')
    try:
        with open(p, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cur.fetchall()]
        
        rep_tables = [t for t in tables if t.startswith('customer_data_') and t != 'customer_data_inventory']
        if rep_tables:
            print(f"\n=== {p} ===")
            for t in rep_tables:
                cur.execute(f"SELECT COUNT(*) FROM {t}")
                cnt = cur.fetchone()[0]
                cur.execute(f"SELECT DISTINCT origin_system FROM {t}")
                origs = [r[0] for r in cur.fetchall()]
                print(f"  {t} ({cnt} rows): origin_systems={origs}")
    except Exception as e:
        print(f"{p}: error {e}")
