"""
SQLite database for sender registry and message queue.
Thread-safe with WAL mode and connection pooling.
"""
import sqlite3
import os
import secrets
import hashlib
import threading
from datetime import datetime, timedelta
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), 'imessage.db')

# Thread-local storage for connections
_local = threading.local()


def get_connection() -> sqlite3.Connection:
    """Get thread-local database connection with WAL mode."""
    if not hasattr(_local, 'connection') or _local.connection is None:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        # Enable WAL mode for better concurrency
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=5000')  # 5 second timeout on locks
        conn.execute('PRAGMA synchronous=NORMAL')  # Good balance of safety/speed
        _local.connection = conn
    return _local.connection


@contextmanager
def get_db():
    """Context manager for database operations with automatic commit/rollback."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def hash_token(token: str) -> str:
    """Hash a token for secure storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def init_db():
    """Initialize database tables."""
    with get_db() as conn:
        # Local sender profile (Phase 1)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS sender (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                name TEXT NOT NULL,
                phone TEXT NOT NULL
            )
        ''')

        # Registered senders/agents (Phase 2) - token is now hashed
        conn.execute('''
            CREATE TABLE IF NOT EXISTS agents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                token_hash TEXT UNIQUE NOT NULL,
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
                retry_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                sent_at TEXT,
                FOREIGN KEY (agent_id) REFERENCES agents(id)
            )
        ''')

        # Create indexes for better query performance
        conn.execute('CREATE INDEX IF NOT EXISTS idx_queue_agent_status ON message_queue(agent_id, status)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_queue_created ON message_queue(created_at)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_agents_online ON agents(is_online)')

        # Migration: rename token to token_hash if old schema exists
        try:
            conn.execute('ALTER TABLE agents RENAME COLUMN token TO token_hash')
        except sqlite3.OperationalError:
            pass  # Column already renamed or doesn't exist


# === Phase 1: Local sender ===

def get_sender() -> dict | None:
    """Get the local sender profile."""
    with get_db() as conn:
        row = conn.execute('SELECT name, phone FROM sender WHERE id = 1').fetchone()
        if row:
            return {'name': row['name'], 'phone': row['phone']}
        return None


def save_sender(name: str, phone: str) -> None:
    """Save or update local sender profile."""
    with get_db() as conn:
        conn.execute('''
            INSERT INTO sender (id, name, phone) VALUES (1, ?, ?)
            ON CONFLICT(id) DO UPDATE SET name = ?, phone = ?
        ''', (name, phone, name, phone))


# === Phase 2: Agent registry ===

def register_agent(name: str, phone: str) -> dict:
    """Register a new agent and return its token (unhashed, for client)."""
    token = secrets.token_urlsafe(32)
    token_hashed = hash_token(token)

    with get_db() as conn:
        cursor = conn.execute(
            'INSERT INTO agents (name, phone, token_hash) VALUES (?, ?, ?)',
            (name, phone, token_hashed)
        )
        agent_id = cursor.lastrowid

    # Return unhashed token to client (only time it's available)
    return {'id': agent_id, 'token': token}


def get_agent_by_token(token: str) -> dict | None:
    """Get agent by token (hashes token for lookup)."""
    token_hashed = hash_token(token)
    with get_db() as conn:
        row = conn.execute(
            'SELECT id, name, phone, is_online, last_seen FROM agents WHERE token_hash = ?',
            (token_hashed,)
        ).fetchone()
        if row:
            return dict(row)
        return None


def get_agent_by_id(agent_id: int) -> dict | None:
    """Get agent by ID."""
    with get_db() as conn:
        row = conn.execute(
            'SELECT id, name, phone, is_online, last_seen FROM agents WHERE id = ?',
            (agent_id,)
        ).fetchone()
        if row:
            return dict(row)
        return None


def get_all_agents() -> list[dict]:
    """Get all registered agents with online status updated."""
    # First, mark stale agents as offline (no heartbeat in 30 seconds)
    mark_stale_agents_offline()

    with get_db() as conn:
        rows = conn.execute(
            'SELECT id, name, phone, is_online, last_seen FROM agents ORDER BY name'
        ).fetchall()
        return [dict(row) for row in rows]


def update_agent_heartbeat(agent_id: int) -> None:
    """Update agent's last seen timestamp and mark online."""
    with get_db() as conn:
        conn.execute(
            'UPDATE agents SET is_online = 1, last_seen = ? WHERE id = ?',
            (datetime.utcnow().isoformat(), agent_id)
        )


def mark_agent_offline(agent_id: int) -> None:
    """Mark an agent as offline."""
    with get_db() as conn:
        conn.execute('UPDATE agents SET is_online = 0 WHERE id = ?', (agent_id,))


def mark_stale_agents_offline(timeout_seconds: int = 30) -> None:
    """Mark agents as offline if no heartbeat within timeout."""
    cutoff = (datetime.utcnow() - timedelta(seconds=timeout_seconds)).isoformat()
    with get_db() as conn:
        conn.execute(
            'UPDATE agents SET is_online = 0 WHERE is_online = 1 AND last_seen < ?',
            (cutoff,)
        )


# === Phase 2: Message queue ===

def queue_message(agent_id: int, recipient_phone: str, message_text: str) -> int:
    """Add a message to the queue for a specific agent."""
    # Verify agent exists
    agent = get_agent_by_id(agent_id)
    if not agent:
        raise ValueError(f"Agent {agent_id} not found")

    with get_db() as conn:
        cursor = conn.execute(
            'INSERT INTO message_queue (agent_id, recipient_phone, message_text) VALUES (?, ?, ?)',
            (agent_id, recipient_phone, message_text)
        )
        return cursor.lastrowid


def get_pending_messages(agent_id: int, limit: int = 10) -> list[dict]:
    """Get pending messages for an agent."""
    with get_db() as conn:
        rows = conn.execute(
            '''SELECT id, recipient_phone, message_text, created_at
               FROM message_queue
               WHERE agent_id = ? AND status = 'queued'
               ORDER BY created_at
               LIMIT ?''',
            (agent_id, limit)
        ).fetchall()
        return [dict(row) for row in rows]


def update_message_status(message_id: int, status: str, error: str = None) -> None:
    """Update message status (sent/failed)."""
    with get_db() as conn:
        sent_at = datetime.utcnow().isoformat() if status == 'sent' else None

        if status == 'failed':
            # Increment retry count on failure
            conn.execute(
                '''UPDATE message_queue
                   SET status = ?, error = ?, retry_count = retry_count + 1
                   WHERE id = ?''',
                (status, error, message_id)
            )
        else:
            conn.execute(
                'UPDATE message_queue SET status = ?, error = ?, sent_at = ? WHERE id = ?',
                (status, error, sent_at, message_id)
            )


def retry_failed_messages(agent_id: int, max_retries: int = 3) -> int:
    """Reset failed messages for retry (up to max_retries attempts)."""
    with get_db() as conn:
        cursor = conn.execute(
            '''UPDATE message_queue
               SET status = 'queued', error = NULL
               WHERE agent_id = ? AND status = 'failed' AND retry_count < ?''',
            (agent_id, max_retries)
        )
        return cursor.rowcount


def expire_old_messages(hours: int = 24) -> int:
    """Mark old queued messages as expired."""
    cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
    with get_db() as conn:
        cursor = conn.execute(
            '''UPDATE message_queue
               SET status = 'expired', error = 'Message expired after 24 hours'
               WHERE status = 'queued' AND created_at < ?''',
            (cutoff,)
        )
        return cursor.rowcount


def get_queue_stats(agent_id: int = None) -> dict:
    """Get message queue statistics."""
    with get_db() as conn:
        if agent_id:
            row = conn.execute(
                '''SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'queued' THEN 1 ELSE 0 END) as queued,
                    SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                    SUM(CASE WHEN status = 'expired' THEN 1 ELSE 0 END) as expired
                   FROM message_queue WHERE agent_id = ?''',
                (agent_id,)
            ).fetchone()
        else:
            row = conn.execute(
                '''SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'queued' THEN 1 ELSE 0 END) as queued,
                    SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                    SUM(CASE WHEN status = 'expired' THEN 1 ELSE 0 END) as expired
                   FROM message_queue'''
            ).fetchone()
        return dict(row)


def cleanup_old_messages(days: int = 7) -> int:
    """Delete messages older than specified days (keeps DB size manageable)."""
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    with get_db() as conn:
        cursor = conn.execute(
            'DELETE FROM message_queue WHERE created_at < ? AND status IN (?, ?, ?)',
            (cutoff, 'sent', 'failed', 'expired')
        )
        return cursor.rowcount


# Initialize on import
init_db()
