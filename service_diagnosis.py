
from datetime import datetime


class ServiceDiagnosis:
    """Track repeated TCP service failures and recovery."""

    def __init__(self, failure_threshold=2):
        self.failure_threshold = failure_threshold
        self.services = {}

    def update(self, device_name, ip, port, status):
        key = (device_name, ip, port)

        if key not in self.services:
            self.services[key] = {
                "consecutive_failures": 0,
                "alert_active": False,
            }

        state = self.services[key]
        event = None

        if status == "OPEN":
            state["consecutive_failures"] = 0

            if state["alert_active"]:
                state["alert_active"] = False
                event = "SERVICE_RECOVERED"

        elif status == "CLOSED_OR_UNREACHABLE":
            state["consecutive_failures"] += 1

            if (
                state["consecutive_failures"] >= self.failure_threshold
                and not state["alert_active"]
            ):
                state["alert_active"] = True
                event = "SERVICE_FAILURE"

        if event:
            if event == "SERVICE_FAILURE":
                message = (
                    f"{device_name}: TCP port {port} failed "
                    f"{state['consecutive_failures']} consecutive "
                    "checks. The host or service may be unreachable."
                )
            else:
                message = (
                    f"{device_name}: TCP port {port} is reachable "
                    "again after a service warning."
                )

            return {
                "event": event,
                "device_name": device_name,
                "ip": ip,
                "port": port,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "message": message,
            }

        return None
