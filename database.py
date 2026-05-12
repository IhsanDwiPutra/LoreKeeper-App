"""
database.py – SQLite schema initialisation for LoreKeeper App.

Tables
------
LoreEntry      : catatan lore (judul, kategori, isi cerita)
GameEvent      : event timeline (nama event, lokasi)
EventCondition : kondisi trigger terstruktur untuk setiap GameEvent
GameVariable   : variabel status global pemain (nama, tipe data, nilai default)
"""

import sqlite3
import os

# Lokasi file database di direktori yang sama dengan modul ini
DB_PATH = os.path.join(os.path.dirname(__file__), "lorekeeper.db")

# DDL statements sesuai design.md
_SCHEMA = """
CREATE TABLE IF NOT EXISTS LoreEntry (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    title    TEXT    NOT NULL,
    category TEXT    NOT NULL,
    content  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS GameEvent (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    event_name TEXT NOT NULL,
    location   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS EventCondition (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id      INTEGER NOT NULL,
    variable_name TEXT    NOT NULL,
    operator      TEXT    NOT NULL,
    target_value  TEXT    NOT NULL,
    FOREIGN KEY (event_id) REFERENCES GameEvent(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS GameVariable (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL UNIQUE,
    var_type      TEXT    NOT NULL,
    default_value TEXT    NOT NULL
);
"""


def get_connection() -> sqlite3.Connection:
    """Buka koneksi ke database dan aktifkan foreign keys."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # hasil query bisa diakses seperti dict
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _migrate_db(conn: sqlite3.Connection) -> None:
    """Tambahkan kolom baru ke tabel yang sudah ada jika belum ada (migrasi ringan)."""
    # --- Migrasi LoreEntry: tambah kolom media jika belum ada ---
    lore_columns = {
        row[1]
        for row in conn.execute("PRAGMA table_info(LoreEntry)").fetchall()
    }
    migrations = [
        ("image_path", "ALTER TABLE LoreEntry ADD COLUMN image_path TEXT"),
        ("audio_path", "ALTER TABLE LoreEntry ADD COLUMN audio_path TEXT"),
    ]
    for column_name, sql in migrations:
        if column_name not in lore_columns:
            conn.execute(sql)
            print(f"[LoreKeeper] Kolom '{column_name}' ditambahkan ke LoreEntry.")

    # --- Migrasi GameEvent: hapus kolom trigger_condition (SQLite rename dance) ---
    event_columns = {
        row[1]
        for row in conn.execute("PRAGMA table_info(GameEvent)").fetchall()
    }
    if "trigger_condition" in event_columns:
        print("[LoreKeeper] Migrasi GameEvent: menghapus kolom 'trigger_condition'...")
        conn.executescript("""
            BEGIN;

            CREATE TABLE IF NOT EXISTS GameEvent_new (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                event_name TEXT NOT NULL,
                location   TEXT NOT NULL
            );

            INSERT INTO GameEvent_new (id, event_name, location)
            SELECT id, event_name, location FROM GameEvent;

            DROP TABLE GameEvent;

            ALTER TABLE GameEvent_new RENAME TO GameEvent;

            COMMIT;
        """)
        print("[LoreKeeper] Kolom 'trigger_condition' berhasil dihapus dari GameEvent.")

    # --- Migrasi EventCondition: buat tabel jika belum ada ---
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    if "EventCondition" not in tables:
        conn.execute("""
            CREATE TABLE EventCondition (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id      INTEGER NOT NULL,
                variable_name TEXT    NOT NULL,
                operator      TEXT    NOT NULL,
                target_value  TEXT    NOT NULL,
                FOREIGN KEY (event_id) REFERENCES GameEvent(id) ON DELETE CASCADE
            )
        """)
        print("[LoreKeeper] Tabel 'EventCondition' berhasil dibuat.")


def init_db() -> None:
    """Buat tabel-tabel jika belum ada, lalu jalankan migrasi kolom."""
    with get_connection() as conn:
        conn.executescript(_SCHEMA)
        _migrate_db(conn)
    print(f"[LoreKeeper] Database siap di: {DB_PATH}")
