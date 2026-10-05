"""
Smart Cardiac Chest Belt - Database Module
SQLite persistence layer managing sessions, sensor telemetry, and alerts.
Stores data in smartcardiac.db.
"""

import sqlite3
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd

import config


class DatabaseManager:
    """Thread-safe SQLite manager for the Smart Cardiac Chest Belt."""

    def __init__(self, db_path: str = config.DATABASE_PATH):
        self.db_path = db_path
        self._lock = threading.Lock()
        self.init_database()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def init_database(self):
        """Initializes tables for sessions, sensor telemetry, and alerts."""
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()

            # 1. Sessions table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    duration REAL DEFAULT 0.0,
                    average_hr REAL,
                    min_hr REAL,
                    max_hr REAL,
                    average_rr REAL,
                    average_temperature REAL,
                    max_temperature REAL,
                    fall_count INTEGER DEFAULT 0
                );
            """)

            # 2. Sensor Telemetry Time-Series table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sensor_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    timestamp INTEGER NOT NULL,
                    ecg REAL,
                    heart_rate REAL,
                    rr_interval REAL,
                    temperature REAL,
                    accel_x REAL,
                    accel_y REAL,
                    accel_z REAL,
                    fall INTEGER DEFAULT 0,
                    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
                );
            """)

            # 3. Clinical & System Alerts table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER,
                    timestamp TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
                );
            """)

            # Fast index on session_id
            cur.execute("CREATE INDEX IF NOT EXISTS idx_sensor_sid ON sensor_data(session_id);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_alerts_sid ON alerts(session_id);")

            conn.commit()
            conn.close()

    def start_session(self) -> int:
        """Begins a new monitoring session and returns its ID."""
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur.execute(
                "INSERT INTO sessions (start_time, fall_count) VALUES (?, 0);",
                (now_iso,)
            )
            session_id = cur.lastrowid
            conn.commit()
            conn.close()
            return session_id

    def end_session(self, session_id: int, duration: float,
                    avg_hr: Optional[float] = None,
                    min_hr: Optional[float] = None,
                    max_hr: Optional[float] = None,
                    avg_rr: Optional[float] = None,
                    avg_temp: Optional[float] = None,
                    max_temp: Optional[float] = None,
                    fall_count: int = 0):
        """Finalizes a monitoring session with summary parameters."""
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            end_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur.execute("""
                UPDATE sessions
                SET end_time = ?,
                    duration = ?,
                    average_hr = ?,
                    min_hr = ?,
                    max_hr = ?,
                    average_rr = ?,
                    average_temperature = ?,
                    max_temperature = ?,
                    fall_count = ?
                WHERE id = ?;
            """, (end_iso, duration, avg_hr, min_hr, max_hr, avg_rr, avg_temp, max_temp, fall_count, session_id))
            conn.commit()
            conn.close()

    def log_sensor_data_batch(self, session_id: int, records: List[Dict[str, Any]]):
        """Batch inserts queued sensor telemetry records."""
        if not records:
            return
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            rows = [
                (
                    session_id,
                    r.get("timestamp", int(datetime.now().timestamp() * 1000)),
                    r.get("ecg"),
                    r.get("heart_rate"),
                    r.get("rr_interval"),
                    r.get("temperature"),
                    r.get("accel_x"),
                    r.get("accel_y"),
                    r.get("accel_z"),
                    1 if r.get("fall") else 0
                )
                for r in records
            ]
            cur.executemany("""
                INSERT INTO sensor_data (
                    session_id, timestamp, ecg, heart_rate, rr_interval,
                    temperature, accel_x, accel_y, accel_z, fall
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, rows)
            conn.commit()
            conn.close()

    def log_alert(self, session_id: Optional[int], alert_type: str,
                  message: str, severity: str, timestamp_str: Optional[str] = None):
        """Logs an alert event to the database."""
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            ts = timestamp_str or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur.execute("""
                INSERT INTO alerts (session_id, timestamp, alert_type, message, severity)
                VALUES (?, ?, ?, ?, ?);
            """, (session_id, ts, alert_type, message, severity))
            conn.commit()
            conn.close()

    def get_session(self, session_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves a single session record by ID."""
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM sessions WHERE id = ?;", (session_id,))
            row = cur.fetchone()
            conn.close()
            return dict(row) if row else None

    def get_session_sensor_data(self, session_id: int) -> pd.DataFrame:
        """Retrieves all sensor records for a session as a pandas DataFrame."""
        with self._lock:
            conn = self._get_connection()
            query = """
                SELECT timestamp, ecg, heart_rate, rr_interval, temperature,
                       accel_x, accel_y, accel_z, fall
                FROM sensor_data
                WHERE session_id = ?
                ORDER BY timestamp ASC;
            """
            df = pd.read_sql_query(query, conn, params=(session_id,))
            conn.close()
            return df

    def get_session_alerts(self, session_id: int) -> List[Dict[str, Any]]:
        """Retrieves all logged alerts for a given session."""
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT timestamp, alert_type, message, severity
                FROM alerts
                WHERE session_id = ?
                ORDER BY id ASC;
            """, (session_id,))
            rows = cur.fetchall()
            conn.close()
            return [dict(r) for r in rows]

    def export_session_to_csv(self, session_id: int, file_path: str) -> bool:
        """Exports sensor telemetry of a session to a CSV file."""
        df = self.get_session_sensor_data(session_id)
        if df.empty:
            return False
        df.to_csv(file_path, index=False)
        return True


# Global database singleton
db = DatabaseManager()
