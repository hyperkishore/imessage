"""
SQLite database for storing sender profile.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'imessage.db')


def get_connection():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables."""
    conn = get_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS sender (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            name TEXT NOT NULL,
            phone TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


def get_sender() -> dict | None:
    """Get the registered sender profile."""
    conn = get_connection()
    row = conn.execute('SELECT name, phone FROM sender WHERE id = 1').fetchone()
    conn.close()
    if row:
        return {'name': row['name'], 'phone': row['phone']}
    return None


def save_sender(name: str, phone: str) -> None:
    """Save or update sender profile."""
    conn = get_connection()
    conn.execute('''
        INSERT INTO sender (id, name, phone) VALUES (1, ?, ?)
        ON CONFLICT(id) DO UPDATE SET name = ?, phone = ?
    ''', (name, phone, name, phone))
    conn.commit()
    conn.close()


# Initialize on import
init_db()
