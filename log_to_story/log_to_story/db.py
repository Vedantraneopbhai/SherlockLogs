import sqlite3
from datetime import datetime

_db_path = None

def init_db(path):
    global _db_path
    _db_path = path
    conn = sqlite3.connect(_db_path)
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT,
        narrative TEXT,
        recs TEXT,
        created_at TEXT
    )
    ''')
    conn.commit()
    conn.close()


def save_analysis(file_path, narrative, recs):
    conn = sqlite3.connect(_db_path)
    cur = conn.cursor()
    cur.execute('INSERT INTO analyses (file_path, narrative, recs, created_at) VALUES (?, ?, ?, ?)',
                (file_path, narrative, repr(recs), datetime.utcnow().isoformat()))
    conn.commit()
    rowid = cur.lastrowid
    conn.close()
    return rowid


def get_all_analyses():
    """Retrieve all past analyses from the database."""
    conn = sqlite3.connect(_db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute('SELECT id, file_path, narrative, recs, created_at FROM analyses ORDER BY created_at DESC LIMIT 50')
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_analysis_by_id(analysis_id):
    """Retrieve a single analysis by ID."""
    conn = sqlite3.connect(_db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute('SELECT id, file_path, narrative, recs, created_at FROM analyses WHERE id = ?', (analysis_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None
