
import json
import os
import tempfile
from unittest.mock import patch
from io import StringIO

import app as network_app
import incident_history

# Create an isolated temporary database.
fd, temporary_db = tempfile.mkstemp(suffix=".db")
os.close(fd)

original_db_name = incident_history.DB_NAME
original_devices = network_app.diagnosis.devices.copy()

def make_result(status):
    """Return the same fields as monitor.ping_device()."""
    is_up = status == "UP"
    return {
        "status": status,
        "packets_sent": 4,
        "packets_received": 4 if is_up else 0,
        "packet_loss": 0.0 if is_up else 100.0,
        "minimum_latency": 1 if is_up else None,
        "maximum_latency": 1 if is_up else None,
        "average_latency": 1 if is_up else None,
        "error": None if is_up else "Simulated test failure.",
    }

try:
    incident_history.DB_NAME = temporary_db
    incident_history.initialize_database()

    test_devices = [
        {
            "name": "Recovery Integration Test",
            "ip": "192.0.2.99",
        }
    ]

    simulated_results = [
        make_result("DOWN"),
        make_result("DOWN"),
        make_result("UP"),
    ]

    client = network_app.app.test_client()
    real_open = open

    def fake_open(file, *args, **kwargs):
        if str(file) == "devices.json":
            return StringIO(json.dumps(test_devices))
        return real_open(file, *args, **kwargs)

    # Start with a clean state for this test device.
    network_app.diagnosis.devices.pop(
        "Recovery Integration Test", None
    )

    with patch("builtins.open", side_effect=fake_open):
        with patch(
            "app.ping_device",
            side_effect=simulated_results,
        ):
            for number in range(3):
                response = client.get("/")
                assert response.status_code == 200, (
                    f"Dashboard request {number + 1} failed: "
                    f"{response.status_code}"
                )
                print(f"Dashboard request {number + 1}: PASS")

    incidents = incident_history.get_incidents(limit=20)

    assert len(incidents) == 1, (
        f"Expected one incident, found {len(incidents)}"
    )

    incident = incidents[0]

    assert incident["device_name"] == "Recovery Integration Test"
    assert incident["event_type"] == "OUTAGE"
    assert incident["end_time"] is not None, (
        "Incident was not closed after recovery."
    )
    assert incident["duration_seconds"] is not None
    assert incident["duration_seconds"] >= 0

    print("\nPASS: Dashboard confirmed the outage.")
    print("PASS: Dashboard processed the recovery.")
    print("PASS: SQLite incident was closed.")
    print("Recovery time:", incident["end_time"])
    print("Duration (seconds):", incident["duration_seconds"])
    print("\nLIVE ROUTE RECOVERY TEST PASSED.")


finally:
    incident_history.DB_NAME = original_db_name

    network_app.diagnosis.devices.clear()
    network_app.diagnosis.devices.update(original_devices)

    # Close any lingering SQLite connections before deleting the file.
    import gc
    gc.collect()

    for suffix in ("", "-journal", "-wal", "-shm"):
        extra_file = temporary_db + suffix

        if os.path.exists(extra_file):
            try:
                os.remove(extra_file)
            except PermissionError:
                print(
                    "Temporary file could not be removed yet:",
                    extra_file,
                )
