import sqlite3
import glob

for p in sorted(glob.glob('dataset/evidence/databases/*')):
    conn = sqlite3.connect(':memory:')
    try:
        with open(p, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cur.fetchall()]
        print(f"{p}: {tables}")
    except Exception as e:
        print(f"{p}: error ({e})")
