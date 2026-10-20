
import sqlite3

DB_NAME = "incident_history.db"

connection = sqlite3.connect(DB_NAME)

try:
    connection.execute("BEGIN IMMEDIATE")

    cursor = connection.execute("""
        DELETE FROM incidents
        WHERE id IN (1, 3)
          AND device_name = ?
          AND ip_address = ?
          AND end_time IS NULL
    """, ("Failure Test Device", "192.0.2.1"))

    print("Duplicate records removed:", cursor.rowcount)

    connection.commit()

    print("\nRemaining incident records:")
    rows = connection.execute("""
        SELECT id, device_name, start_time, end_time
        FROM incidents
        ORDER BY id
    """).fetchall()

    for row in rows:
        print(row)

except Exception:
    connection.rollback()
    raise

finally:
    connection.close()
