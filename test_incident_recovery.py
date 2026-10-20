
from incident_history import (
    initialize_database,
    record_outage,
    record_recovery,
    get_incidents,
)

initialize_database()

device = "Recovery Test Device"
ip = "192.0.2.50"
start = "2026-10-12 10:00:00"
end = "2026-10-12 10:05:00"

record_outage(
    device,
    ip,
    start,
    "Test outage confirmed."
)

recovered = record_recovery(
    device,
    ip,
    start,
    end,
    "Test device recovered."
)

print("Recovery recorded:", recovered)

for incident in get_incidents():
    if incident["device_name"] == device:
        print("Incident:", incident)
