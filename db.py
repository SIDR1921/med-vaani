import sqlite3
from datetime import datetime,timedelta
import config

def get_conn():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            display_name TEXT NOT NULL,
            normalized_name TEXT NOT NULL,
            age INTEGER,
            village TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL REFERENCES patients(id),
            systolic INTEGER,
            diastolic INTEGER,
            symptoms TEXT,
            reminders TEXT,
            source_excerpt TEXT,
            recorded_by INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS consents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL REFERENCES patients(id),
            visit_id INTEGER REFERENCES visits(id),
            method TEXT NOT NULL,
            attested_by INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor INTEGER NOT NULL,
            action TEXT NOT NULL,
            detail TEXT,
            created_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_patients_lookup
            ON patients(normalized_name, village);
        CREATE INDEX IF NOT EXISTS idx_visits_patient
            ON visits(patient_id, created_at);
        """)
    conn.commit()
    conn.close()

def _now():
    return datetime.utcnow().isoformat(timespec="seconds")

def create_patient(conn, display_name, normalized_name, age , village):
    cur = conn.execute(
        "INSERT INTO patients (display_name, normalized_name, age, village, created_at) VALUES (?, ?, ?, ?, ?)",
        (display_name, normalized_name, age, village, _now())
    )
    return cur.lastrowid

def save_visit(conn, patient_id, record , reminders, recorded_by):
    cur = conn.execute(
        "INSERT INTO visits (patient_id, systolic, diastolic, symptoms, reminders, source_excerpt, recorded_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (patient_id, record.get("systolic"), record.get("diastolic"), record.get("symptoms"), reminders, record.get("source_excerpt"), recorded_by, _now())
    )
    return cur.lastrowid

def record_consent(conn, patient_id, visit_id, attested_by, method="worker_attested_verbal"):
    conn.execute(
        "INSERT INTO consents (patient_id, visit_id, method, attested_by, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (patient_id, visit_id, method, attested_by, _now()),
    )

def log_action(conn, actor, action, detail=""):
    conn.execute(
        "INSERT INTO audit_log (actor, action, detail, created_at) VALUES (?, ?, ?, ?)",
        (actor, action, detail, _now()),
    )


def visit_history(conn, patient_id, limit=3):
    return conn.execute(
        "SELECT systolic, diastolic, created_at FROM visits "
        "WHERE patient_id = ? ORDER BY created_at DESC LIMIT ?",
        (patient_id, limit),
    ).fetchall()


def purge_expired(conn):
    """DPDP retention: delete visit data older than RETENTION_DAYS."""
    cutoff = (datetime.utcnow() - timedelta(days=config.RETENTION_DAYS)).isoformat()
    cur = conn.execute("DELETE FROM visits WHERE created_at < ?", (cutoff,))
    return cur.rowcount

