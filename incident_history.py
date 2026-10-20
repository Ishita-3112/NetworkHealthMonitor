
import sqlite3
from datetime import datetime

DB_NAME = "incident_history.db"


def initialize_database():
    """Create the incident table if it does not exist."""
    with sqlite3.connect(DB_NAME) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_name TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                event_type TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                duration_seconds REAL,
                message TEXT
            )
        """)


def record_outage(device_name, ip_address, start_time, message):
    """Save a newly confirmed outage."""
    with sqlite3.connect(DB_NAME) as connection:
        connection.execute("""
            INSERT INTO incidents (
                device_name, ip_address, event_type,
                start_time, message
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            device_name,
            ip_address,
            "OUTAGE",
            start_time,
            message
        ))


def record_recovery(
    device_name, ip_address, start_time, end_time, message
):
    """Close the latest unresolved outage for a device."""
    with sqlite3.connect(DB_NAME) as connection:
        row = connection.execute("""
            SELECT id, start_time
            FROM incidents
            WHERE device_name = ?
              AND ip_address = ?
              AND event_type = 'OUTAGE'
              AND end_time IS NULL
            ORDER BY id DESC
            LIMIT 1
        """, (device_name, ip_address)).fetchone()

        if row is None:
            return False

        # Use the stored outage start time for accurate duration.
        try:
            start = datetime.strptime(
                row[1], "%Y-%m-%d %H:%M:%S"
            )
            end = datetime.strptime(
                end_time, "%Y-%m-%d %H:%M:%S"
            )
            duration = max(0, (end - start).total_seconds())
        except ValueError:
            duration = None

        connection.execute("""
            UPDATE incidents
            SET end_time = ?,
                duration_seconds = ?,
                message = ?
            WHERE id = ?
        """, (end_time, duration, message, row[0]))

        return True


def get_incidents(limit=50):
    """Return the newest incidents first."""
    with sqlite3.connect(DB_NAME) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute("""
            SELECT *
            FROM incidents
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()

        return [dict(row) for row in rows]
def get_open_incidents():
    """Return all outages that have not yet recovered."""
    with sqlite3.connect(DB_NAME) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute("""
            SELECT device_name, ip_address, start_time
            FROM incidents
            WHERE event_type = 'OUTAGE'
              AND end_time IS NULL
            ORDER BY id DESC
        """).fetchall()

        return [dict(row) for row in rows]

if __name__ == "__main__":
    initialize_database()
    print("Incident history database initialized successfully.")
    print(f"Existing incident records: {len(get_incidents())}")
