"""Camada de acesso ao banco de dados SQLite."""
from __future__ import annotations

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "esmaltes.db"
UPLOAD_DIR = DATA_DIR / "uploads"

SCHEMA = """
CREATE TABLE IF NOT EXISTS esmaltes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    etiqueta        INTEGER UNIQUE NOT NULL,
    marca           TEXT,
    serie           TEXT,
    cor             TEXT,
    validade        TEXT,            -- ISO date (YYYY-MM-DD), dia 01 do mês
    data_cadastro   TEXT NOT NULL,   -- ISO date
    status          TEXT NOT NULL DEFAULT 'Prateleira',
    motivo          TEXT,
    data_removido   TEXT
);

CREATE TABLE IF NOT EXISTS fotos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    esmalte_id  INTEGER NOT NULL,
    arquivo     TEXT NOT NULL,
    criada_em   TEXT NOT NULL,
    FOREIGN KEY (esmalte_id) REFERENCES esmaltes(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_esmaltes_status   ON esmaltes(status);
CREATE INDEX IF NOT EXISTS idx_esmaltes_validade ON esmaltes(validade);
CREATE INDEX IF NOT EXISTS idx_fotos_esmalte     ON fotos(esmalte_id);
"""


def get_conn() -> sqlite3.Connection:
    DATA_DIR.mkdir(exist_ok=True)
    UPLOAD_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = get_conn()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def proxima_etiqueta(conn: sqlite3.Connection) -> int:
    """Retorna o próximo número de etiqueta na sequência (máximo + 1)."""
    row = conn.execute("SELECT COALESCE(MAX(etiqueta), 0) AS m FROM esmaltes").fetchone()
    return int(row["m"]) + 1
