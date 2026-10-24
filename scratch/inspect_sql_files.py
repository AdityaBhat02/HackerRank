import glob
import sqlite3
import os

print("--- Inspecting SQL Files ---")
for p in glob.glob('dataset/evidence/databases/*.sql'):
    fname = os.path.basename(p)
    conn = sqlite3.connect(':memory:')
    try:
        with open(p, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        conn.executescript(sql_script)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cur.fetchall()]
        table_counts = {}
        for t in tables:
            cur.execute(f"SELECT COUNT(*) FROM \"{t}\"")
            table_counts[t] = cur.fetchone()[0]
        print(f"{fname} -> Tables: {table_counts}")
    except Exception as e:
        print(f"Error executing {fname}: {e}")
    finally:
        conn.close()
