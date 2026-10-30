import sqlite3
import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SOURCE = BASE_DIR / "db.sqlite3"
BACKUP_DIR = BASE_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True)

filename = "sams_backup_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".sqlite3"
destination = BACKUP_DIR / filename

with sqlite3.connect(str(SOURCE)) as original:
    with sqlite3.connect(str(destination)) as backup:
        original.backup(backup)

with sqlite3.connect(str(destination)) as check:
    integrity = check.execute("PRAGMA integrity_check").fetchone()[0]

if integrity != "ok":
    raise RuntimeError("Backup integrity check failed")

print("SUCCESS:", destination)
print("INTEGRITY:", integrity)
