import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')
DB_PATH = Path(os.getenv('DB_PATH', str(ROOT / 'storage' / 'aevia.sqlite3')))
SCHEMA = """
CREATE TABLE IF NOT EXISTS municipalities (
    id INTEGER PRIMARY KEY, name TEXT NOT NULL, uf TEXT NOT NULL,
    latitude REAL, longitude REAL, search_key TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_municipalities_search ON municipalities(search_key);
CREATE TABLE IF NOT EXISTS cache (
    cache_key TEXT PRIMARY KEY, body TEXT NOT NULL, expires_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS contributions (
    id TEXT PRIMARY KEY, created_at TEXT NOT NULL,
    city_id INTEGER, city_name TEXT NOT NULL, latitude REAL NOT NULL, longitude REAL NOT NULL,
    place_name TEXT NOT NULL, historic_year INTEGER, title TEXT NOT NULL,
    story TEXT NOT NULL, author_name TEXT NOT NULL, license TEXT NOT NULL,
    rights_basis TEXT NOT NULL DEFAULT 'registro_anterior', rights_reference TEXT NOT NULL DEFAULT '',
    source_reference TEXT NOT NULL, image_file TEXT,
    image_hash TEXT, consent INTEGER NOT NULL, ai_consent INTEGER NOT NULL,
    ai_status TEXT NOT NULL DEFAULT 'nao_avaliada', ai_report TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pendente', reviewer_note TEXT NOT NULL DEFAULT '',
    reviewed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_contributions_status ON contributions(status);
CREATE INDEX IF NOT EXISTS idx_contributions_city ON contributions(city_id);
CREATE INDEX IF NOT EXISTS idx_contributions_image_hash ON contributions(image_hash);
"""

_lock = threading.Lock()

def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(DB_PATH), timeout=10)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA foreign_keys=ON')
    return db

@contextmanager
def database():
    with _lock:
        db = connect()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

def initialize():
    with database() as db:
        db.executescript(SCHEMA)
        existing={col[1] for col in db.execute('PRAGMA table_info(contributions)').fetchall()}
        if 'rights_basis' not in existing:
            db.execute("ALTER TABLE contributions ADD COLUMN rights_basis TEXT NOT NULL DEFAULT 'registro_anterior'")
        if 'rights_reference' not in existing:
            db.execute("ALTER TABLE contributions ADD COLUMN rights_reference TEXT NOT NULL DEFAULT ''")

