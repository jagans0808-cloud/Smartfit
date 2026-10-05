"""
SmartFit - Database Layer
Integrates the existing OA Risk Screening schema with SmartFit Multimodal Fitness Extensions.
Uses SQLite for offline-first, local healthcare and athletic monitoring.
"""

import sqlite3
import hashlib
import hmac
import base64
import json
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "smartfit.db"

SECRET = os.getenv("SMARTFIT_SECRET", "smartfit-biomedfinix-secret-key-2026")
TOKEN_EXPIRY_SECONDS = 8 * 3600  # 8 hours

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 210000)
    return base64.b64encode(salt + dk).decode()

def verify_password(password: str, encoded: str) -> bool:
    try:
        raw = base64.b64decode(encoded)
        salt, expected = raw[:16], raw[16:]
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 210000)
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False

def init_db():
    conn = get_db()
    conn.executescript("""
    -- 1. Patients Table (Reused from OA Schema)
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        contact TEXT NOT NULL,
        place TEXT NOT NULL,
        age INTEGER NOT NULL,
        gender TEXT NOT NULL,
        height REAL NOT NULL,
        weight REAL NOT NULL,
        pain_side TEXT NOT NULL,
        created_at TEXT NOT NULL
    );

    -- 2. OA Screenings Table (Reused from OA Schema)
    CREATE TABLE IF NOT EXISTS screenings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        data_quality TEXT DEFAULT 'GOOD',
        firmware_version TEXT DEFAULT 'v3.0',
        model_version TEXT DEFAULT 'OAI-Calibrated-v2.1',
        features_json TEXT NOT NULL,
        result_json TEXT NOT NULL,
        quality_json TEXT DEFAULT '{}',
        baseline_comparison_json TEXT DEFAULT '{}',
        FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
    );

    -- 3. Calibrations Table (Reused from OA Schema)
    CREATE TABLE IF NOT EXISTS calibrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        zero_offset_deg REAL NOT NULL,
        flex_baseline_adc INTEGER,
        heel_tare_adc INTEGER,
        forefoot_tare_adc INTEGER,
        operator_notes TEXT,
        FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
    );

    -- 4. SmartFit Exercise Sessions Table (Multimodal & Random Forest)
    CREATE TABLE IF NOT EXISTS exercise_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT UNIQUE NOT NULL,
        patient_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        exercise_name TEXT NOT NULL,
        rep_count INTEGER DEFAULT 0,
        duration_seconds INTEGER DEFAULT 0,
        form_score REAL DEFAULT 0.0,
        knee_rom REAL DEFAULT 0.0,
        avg_heart_rate REAL DEFAULT 0.0,
        avg_spo2 REAL DEFAULT 0.0,
        device_status_json TEXT DEFAULT '{}',
        features_json TEXT NOT NULL,
        classification_result_json TEXT NOT NULL,
        notes TEXT DEFAULT '',
        FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
    );

    -- 5. Device Telemetry Snapshots
    CREATE TABLE IF NOT EXISTS telemetry_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        source_device TEXT NOT NULL,
        packet_json TEXT NOT NULL
    );
    """)

    # Seed default staff & demo patient if empty
    cur = conn.cursor()
    patient_count = cur.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
    if patient_count == 0:
        demo_pid = "SF-1001"
        now = time.strftime("%Y-%m-%dT%H:%M:%S")
        cur.execute("""
            INSERT INTO patients (patient_id, name, username, password_hash, contact, place, age, gender, height, weight, pain_side, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            demo_pid,
            "Rohan Sharma",
            "rohan_s",
            hash_password("rohan1234"),
            "9876543210",
            "New Delhi, India",
            28,
            "Male",
            176.0,
            74.5,
            "Right",
            now
        ))

        demo_pid2 = "SF-1002"
        cur.execute("""
            INSERT INTO patients (patient_id, name, username, password_hash, contact, place, age, gender, height, weight, pain_side, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            demo_pid2,
            "Ananya Patel",
            "ananya_p",
            hash_password("ananya1234"),
            "9823456789",
            "Mumbai, India",
            52,
            "Female",
            162.0,
            68.0,
            "Bilateral",
            now
        ))
        conn.commit()

    conn.close()

if __name__ == "__main__":
    init_db()
    print("SmartFit database initialized at", DB_PATH)
