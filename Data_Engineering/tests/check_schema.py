import sqlite3
conn = sqlite3.connect('data/credit.db')
cur = conn.cursor()
tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
for (tname,) in tables:
    cols = [c[1] for c in cur.execute(f"PRAGMA table_info({tname})")]
    print(f"{tname}: {cols}")
    # print first row to see real data
    row = cur.execute(f"SELECT * FROM {tname} LIMIT 1").fetchone()
    print(f"  sample: {row}\n")
conn.close()
