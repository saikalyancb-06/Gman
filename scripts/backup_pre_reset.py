import os
import json
import sqlite3
import datetime
import shutil

def perform_backup_and_inventory():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'backups'))
    os.makedirs(backup_dir, exist_ok=True)
    
    sqlite_db = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend', 'geoguide.db'))
    backup_db_path = os.path.join(backup_dir, f"geoguide_pre_reset_{timestamp}.db")
    backup_sql_path = os.path.join(backup_dir, f"geoguide_pre_reset_{timestamp}.sql")
    manifest_path = os.path.join(backup_dir, f"inventory_manifest_{timestamp}.json")
    
    inventory = {
        "timestamp": timestamp,
        "backup_db_path": backup_db_path,
        "backup_sql_path": backup_sql_path,
        "source_sqlite": sqlite_db,
        "tables": {},
        "total_rows": 0
    }
    
    if os.path.exists(sqlite_db):
        # 1. Copy binary db
        shutil.copy2(sqlite_db, backup_db_path)
        print(f"[OK] Binary backup created at: {backup_db_path}")
        
        # 2. Dump SQL and inspect tables
        conn = sqlite3.connect(sqlite_db)
        with open(backup_sql_path, 'w', encoding='utf-8') as f:
            for line in conn.iterdump():
                f.write(f"{line}\n")
        print(f"[OK] SQL dump created at: {backup_sql_path}")
        
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [r[0] for r in cur.fetchall()]
        
        for t in sorted(tables):
            cur.execute(f"PRAGMA table_info({t})")
            columns = [dict(col_id=r[0], name=r[1], type=r[2], notnull=r[3], pk=r[5]) for r in cur.fetchall()]
            cur.execute(f"SELECT count(*) FROM {t}")
            cnt = cur.fetchone()[0]
            inventory["tables"][t] = {
                "row_count": cnt,
                "columns": columns
            }
            inventory["total_rows"] += cnt
        
        conn.close()
    
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(inventory, f, indent=2)
    print(f"[OK] Manifest created at: {manifest_path} with {len(inventory['tables'])} tables and {inventory['total_rows']} rows.")

if __name__ == '__main__':
    perform_backup_and_inventory()
