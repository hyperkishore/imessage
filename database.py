"""
SQLite database for sender registry and message queue.
"""
import sqlite3
import os
import secrets
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'imessage.db')


def get_connection():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables."""
    conn = get_connection()

    # Local sender profile (Phase 1 - kept for backward compatibility)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS sender (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            name TEXT NOT NULL,
            phone TEXT NOT NULL
        )
    ''')

    # Registered senders/agents (Phase 2)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            token TEXT UNIQUE NOT NULL,
            is_online INTEGER DEFAULT 0,
            last_seen TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Message queue (Phase 2)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS message_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id INTEGER NOT NULL,
            recipient_phone TEXT NOT NULL,
            message_text TEXT NOT NULL,
            status TEXT DEFAULT 'queued',
            error TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            sent_at TEXT,
            FOREIGN KEY (agent_id) REFERENCES agents(id)
        )
    ''')

    conn.commit()
    conn.close()


# === Phase 1: Local sender ===

def get_sender() -> dict | None:
    """Get the local sender profile."""
    conn = get_connection()
    row = conn.execute('SELECT name, phone FROM sender WHERE id = 1').fetchone()
    conn.close()
    if row:
        return {'name': row['name'], 'phone': row['phone']}
    return None


def save_sender(name: str, phone: str) -> None:
    """Save or update local sender profile."""
    conn = get_connection()
    conn.execute('''
        INSERT INTO sender (id, name, phone) VALUES (1, ?, ?)
        ON CONFLICT(id) DO UPDATE SET name = ?, phone = ?
    ''', (name, phone, name, phone))
    conn.commit()
    conn.close()


# === Phase 2: Agent registry ===

def register_agent(name: str, phone: str) -> dict:
    """Register a new agent and return its token."""
    token = secrets.token_urlsafe(32)
    conn = get_connection()
    cursor = conn.execute(
        'INSERT INTO agents (name, phone, token) VALUES (?, ?, ?)',
        (name, phone, token)
    )
    agent_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {'id': agent_id, 'token': token}


def get_agent_by_token(token: str) -> dict | None:
    """Get agent by token."""
    conn = get_connection()
    row = conn.execute(
        'SELECT id, name, phone, is_online, last_seen FROM agents WHERE token = ?',
        (token,)
    ).fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def get_all_agents() -> list[dict]:
    """Get all registered agents."""
    conn = get_connection()
    rows = conn.execute(
        'SELECT id, name, phone, is_online, last_seen FROM agents ORDER BY name'
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_agent_heartbeat(agent_id: int) -> None:
    """Update agent's last seen timestamp and mark online."""
    conn = get_connection()
    conn.execute(
        'UPDATE agents SET is_online = 1, last_seen = ? WHERE id = ?',
        (datetime.utcnow().isoformat(), agent_id)
    )
    conn.commit()
    conn.close()


def mark_agent_offline(agent_id: int) -> None:
    """Mark an agent as offline."""
    conn = get_connection()
    conn.execute('UPDATE agents SET is_online = 0 WHERE id = ?', (agent_id,))
    conn.commit()
    conn.close()


# === Phase 2: Message queue ===

def queue_message(agent_id: int, recipient_phone: str, message_text: str) -> int:
    """Add a message to the queue for a specific agent."""
    conn = get_connection()
    cursor = conn.execute(
        'INSERT INTO message_queue (agent_id, recipient_phone, message_text) VALUES (?, ?, ?)',
        (agent_id, recipient_phone, message_text)
    )
    message_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return message_id


def get_pending_messages(agent_id: int, limit: int = 10) -> list[dict]:
    """Get pending messages for an agent."""
    conn = get_connection()
    rows = conn.execute(
        '''SELECT id, recipient_phone, message_text, created_at
           FROM message_queue
           WHERE agent_id = ? AND status = 'queued'
           ORDER BY created_at
           LIMIT ?''',
        (agent_id, limit)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_message_status(message_id: int, status: str, error: str = None) -> None:
    """Update message status (sent/failed)."""
    conn = get_connection()
    sent_at = datetime.utcnow().isoformat() if status == 'sent' else None
    conn.execute(
        'UPDATE message_queue SET status = ?, error = ?, sent_at = ? WHERE id = ?',
        (status, error, sent_at, message_id)
    )
    conn.commit()
    conn.close()


def get_queue_stats(agent_id: int = None) -> dict:
    """Get message queue statistics."""
    conn = get_connection()
    if agent_id:
        row = conn.execute(
            '''SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'queued' THEN 1 ELSE 0 END) as queued,
                SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
               FROM message_queue WHERE agent_id = ?''',
            (agent_id,)
        ).fetchone()
    else:
        row = conn.execute(
            '''SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'queued' THEN 1 ELSE 0 END) as queued,
                SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
               FROM message_queue'''
        ).fetchone()
    conn.close()
    return dict(row)


# Initialize on import
init_db()
