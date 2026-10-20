import socket
from datetime import datetime
import platform
import re
import subprocess
import time
import json


def ping_device(ip, count=4, timeout=10):
    """
    Check network reachability using ICMP ping.

    Args:
        ip (str): IP address or hostname to check.
        count (int): Number of ping packets to send.
        timeout (int): Maximum time allowed for the command, in seconds.

    Returns:
        dict: Network status, packet statistics, and latency measurements.
    """

    # Initialize default values
    packets_sent = count
    packets_received = 0
    packet_loss = 100.0
    minimum = None
    maximum = None
    average = None
    error = None

    system = platform.system()

    # Build the appropriate ping command
    if system == "Windows":
        command = ["ping", "-n", str(count), "-w", "2000", ip]
    elif system in ("Linux", "Darwin"):
        command = ["ping", "-c", str(count), "-W", "2", ip]
    else:
        return {
            "status": "ERROR",
            "packets_sent": 0,
            "packets_received": 0,
            "packet_loss": 100.0,
            "minimum_latency": None,
            "maximum_latency": None,
            "average_latency": None,
            "error": f"Unsupported operating system: {system}"
        }

    start_time = time.time()

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=timeout
        )

        output = result.stdout + "\n" + result.stderr

        # Windows packet statistics
        windows_match = re.search(
            r"Packets:\s*Sent\s*=\s*(\d+),\s*"
            r"Received\s*=\s*(\d+),\s*Lost\s*=\s*(\d+)",
            output,
            re.IGNORECASE
        )

        # Linux/macOS packet statistics
        unix_match = re.search(
            r"(\d+)\s+packets transmitted,\s*"
            r"(\d+)\s+(?:packets )?received",
            output,
            re.IGNORECASE
        )

        if windows_match:
            packets_sent = int(windows_match.group(1))
            packets_received = int(windows_match.group(2))

        elif unix_match:
            packets_sent = int(unix_match.group(1))
            packets_received = int(unix_match.group(2))

        # Calculate packet loss from observed packet counts
        if packets_sent > 0:
            lost = packets_sent - packets_received
            packet_loss = max(
                0.0,
                min(100.0, (lost / packets_sent) * 100)
            )

        # Windows latency statistics
        windows_latency = re.search(
            r"Minimum\s*=\s*(\d+)ms,\s*"
            r"Maximum\s*=\s*(\d+)ms,\s*"
            r"Average\s*=\s*(\d+)ms",
            output,
            re.IGNORECASE
        )

        # Linux/macOS latency statistics
        unix_latency = re.search(
            r"rtt min/avg/max/(?:mdev|stddev)\s*=\s*"
            r"([\d.]+)/([\d.]+)/([\d.]+)",
            output,
            re.IGNORECASE
        )

        if windows_latency:
            minimum = int(windows_latency.group(1))
            maximum = int(windows_latency.group(2))
            average = int(windows_latency.group(3))

        elif unix_latency:
            minimum = float(unix_latency.group(1))
            average = float(unix_latency.group(2))
            maximum = float(unix_latency.group(3))

        # Determine whether the command itself succeeded
        if result.returncode != 0 and packets_received == 0:
            error = "Ping command failed or no replies were received."

    except subprocess.TimeoutExpired:
        error = f"Ping command exceeded the {timeout}-second timeout."

    except FileNotFoundError:
        error = "Ping executable was not found on this system."

    except OSError as exc:
        error = f"Operating system error: {exc}"

    # Classify the observed connectivity
    if error and packets_received == 0:
        status = "ERROR" if (
            "not found" in error.lower()
            or "unsupported operating system" in error.lower()
            or "operating system error" in error.lower()
        ) else "DOWN"

    elif packets_received == 0:
        status = "DOWN"

    elif packet_loss > 0:
        status = "DEGRADED"

    else:
        status = "UP"

    return {
        "status": status,
        "packets_sent": packets_sent,
        "packets_received": packets_received,
        "packet_loss": round(packet_loss, 2),
        "minimum_latency": minimum,
        "maximum_latency": maximum,
        "average_latency": average,
        "error": error
    }

def check_tcp_port(ip, port, timeout=3):
    """
    Check whether a TCP service accepts a connection.

    A successful connection means the port is reachable,
    not that the application is functioning correctly.
    """
    start_time = time.perf_counter()

    try:
        with socket.create_connection((ip, port), timeout=timeout):
            latency = (time.perf_counter() - start_time) * 1000

            return {
                "status": "OPEN",
                "ip": ip,
                "port": port,
                "latency_ms": round(latency, 2),
                "checked_at": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "error": None
            }

    except socket.timeout:
        error = "Connection timed out."

    except ConnectionRefusedError:
        error = "Connection refused; no service accepted the connection."

    except OSError as exc:
        error = str(exc)

    return {
        "status": "CLOSED_OR_UNREACHABLE",
        "ip": ip,
        "port": port,
        "latency_ms": None,
        "checked_at": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "error": error
    }




def main():
    """Run a simple command-line monitoring loop."""

    with open("devices.json", "r", encoding="utf-8") as file:
        devices = json.load(file)

    try:
        while True:
            print("\n========== NETWORK HEALTH MONITOR ==========")
            print("Time:", time.strftime("%Y-%m-%d %H:%M:%S"))

            for device in devices:
                print("\nChecking:", device["name"])
                print("IP Address:", device["ip"])

                result = ping_device(device["ip"])

                print("Status:", result["status"])
                print("Packets sent:", result["packets_sent"])
                print("Packets received:", result["packets_received"])
                print("Packet loss:", result["packet_loss"], "%")

                if result["average_latency"] is not None:
                    print(
                        "Average latency:",
                        result["average_latency"],
                        "ms"
                    )

                if result["error"]:
                    print("Diagnostic message:", result["error"])

                print("--------------------------------------------")

            print("Next check in 5 seconds. Press Ctrl+C to stop.")
            time.sleep(5)

    except KeyboardInterrupt:
        print("\nNetwork monitoring stopped.")


if __name__ == "__main__":
    main()
