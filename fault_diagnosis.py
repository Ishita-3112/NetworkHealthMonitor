
from datetime import datetime


class FaultDiagnosis:
    def __init__(self, failure_threshold=2):
        self.failure_threshold = failure_threshold
        self.devices = {}

    def update(self, name, ip, status):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if name not in self.devices:
            self.devices[name] = {
                "ip": ip,
                "consecutive_failures": 0,
                "outage_active": False,
                "outage_started_at": None
            }

        device = self.devices[name]
        device["ip"] = ip

        if status == "DOWN":
            device["consecutive_failures"] += 1

            if (
                device["consecutive_failures"] >= self.failure_threshold
                and not device["outage_active"]
            ):
                device["outage_active"] = True
                device["outage_started_at"] = now

                return {
                    "event": "OUTAGE_CONFIRMED",
                    "device": name,
                    "ip": ip,
                    "time": now,
                    "message": (
                        f"{name} is DOWN after "
                        f"{device['consecutive_failures']} "
                        "consecutive failed checks."
                    )
                }

            return {
                "event": "FAILURE_RECORDED",
                "device": name,
                "ip": ip,
                "time": now,
                "message": (
                    f"Failed check {device['consecutive_failures']} "
                    f"for {name}."
                )
            }

        if status in ("UP", "DEGRADED"):
            was_down = device["outage_active"]

            device["consecutive_failures"] = 0
            device["outage_active"] = False

            if was_down:
                started_at = device["outage_started_at"]
                device["outage_started_at"] = None

                return {
                    "event": "RECOVERED",
                    "device": name,
                    "ip": ip,
                    "time": now,
                    "outage_started_at": started_at,
                    "message": f"{name} has recovered."
                }

            return {
                "event": "HEALTHY",
                "device": name,
                "ip": ip,
                "time": now,
                "message": f"{name} is responding."
            }

        return {
            "event": "CHECK_ERROR",
            "device": name,
            "ip": ip,
            "time": now,
            "message": (
                f"Could not classify the check result for {name}: "
                f"{status}"
            )
        }
    



if __name__ == "__main__":
    diagnosis = FaultDiagnosis(failure_threshold=2)

    test_cases = [
        ("Failure Test Device", "192.0.2.1", "DOWN"),
        ("Failure Test Device", "192.0.2.1", "DOWN"),
        ("Failure Test Device", "192.0.2.1", "UP"),
    ]

    for name, ip, status in test_cases:
        result = diagnosis.update(name, ip, status)
        print(result["event"], "-", result["message"])
