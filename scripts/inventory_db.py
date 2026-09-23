import sqlite3
import os

def inventory():
    dbs = [
        os.path.abspath('backend/geoguide.db'),
        os.path.abspath('geoguide.db'),
        os.path.abspath('data/source/ps13_original.sqlite')
    ]
    for db in dbs:
        if os.path.exists(db):
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = [r[0] for r in cur.fetchall()]
            print(f"=== DB: {db} ===")
            print(f"Total tables: {len(tables)}")
            for t in sorted(tables):
                cur.execute(f"SELECT count(*) FROM {t}")
                cnt = cur.fetchone()[0]
                print(f"  - {t}: {cnt} rows")
            conn.close()

if __name__ == '__main__':
    inventory()
