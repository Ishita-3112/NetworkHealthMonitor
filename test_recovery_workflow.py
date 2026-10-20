
from fault_diagnosis import FaultDiagnosis
from incident_history import (
    initialize_database,
    record_outage,
    record_recovery,
    get_incidents,
)
from datetime import datetime, timedelta

# Use a unique test device to protect existing incidents.
device_name = "Recovery Workflow Test"
ip_address = "192.0.2.99"

initialize_database()

# Create an independent diagnosis instance.
diagnosis = FaultDiagnosis(failure_threshold=2)

# Simulate two consecutive failed checks.
diagnosis.update(device_name, ip_address, "DOWN")
outage_event = diagnosis.update(device_name, ip_address, "DOWN")

assert outage_event["event"] == "OUTAGE_CONFIRMED"

# Set a predictable 90-second test duration.
start_time = datetime.now().replace(microsecond=0)
end_time = start_time + timedelta(seconds=90)

start_text = start_time.strftime("%Y-%m-%d %H:%M:%S")
end_text = end_time.strftime("%Y-%m-%d %H:%M:%S")

# Save the test outage.
record_outage(
    device_name,
    ip_address,
    start_text,
    "Temporary recovery workflow test."
)

# Simulate the device recovering.
recovery_event = diagnosis.update(
    device_name, ip_address, "UP"
)

assert recovery_event["event"] == "RECOVERED"

# Close the test incident in SQLite.
closed = record_recovery(
    device_name,
    ip_address,
    start_text,
    end_text,
    recovery_event["message"],
)

assert closed is True, "No open test incident was closed."

# Verify the database record.
test_incidents = [
    incident
    for incident in get_incidents(limit=100)
    if incident["device_name"] == device_name
    and incident["ip_address"] == ip_address
]

assert len(test_incidents) == 1, (
    f"Expected one test record, found {len(test_incidents)}"
)

incident = test_incidents[0]

assert incident["end_time"] == end_text
assert incident["duration_seconds"] == 90.0

print("PASS: Outage was detected.")
print("PASS: Recovery event was generated.")
print("PASS: Incident was closed in SQLite.")
print("PASS: Recovery timestamp and 90-second duration are correct.")
print("Test incident ID:", incident["id"])
