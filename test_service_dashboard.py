
from unittest.mock import patch
import app as application

# Use Flask's test client without starting the web server.
client = application.app.test_client()

# Mock monitoring and database operations so the test
# does not alter real monitoring history or incident records.
with (
    patch.object(application, "ping_device") as mock_ping,
    patch.object(application, "check_tcp_port") as mock_tcp,
    patch.object(application, "save_history"),
    patch.object(application, "get_incidents", return_value=[]),
    patch.object(application, "get_open_incidents", return_value=[]),
    patch.object(application, "record_outage"),
    patch.object(application, "record_recovery"),
):
    mock_ping.return_value = {
    "status": "UP",
    "latency_ms": 1.0,
    "average_latency": 1.0,
    "packet_loss": 0,
    "error": None,
}
    # First request: the TCP service fails.
    mock_tcp.return_value = {
        "status": "CLOSED_OR_UNREACHABLE",
        "latency_ms": None,
        "error": "Simulated test failure",
    }
    client.get("/")

    # Second request: another failure should trigger an alert.
    response = client.get("/")
    page = response.get_data(as_text=True)

    print("SERVICE_FAILURE displayed:", "SERVICE_FAILURE" in page)

    # Next request: the service recovers.
    mock_tcp.return_value = {
        "status": "OPEN",
        "latency_ms": 1.0,
        "error": None,
    }
    response = client.get("/")
    page = response.get_data(as_text=True)

    print("SERVICE_RECOVERED displayed:", "SERVICE_RECOVERED" in page)

