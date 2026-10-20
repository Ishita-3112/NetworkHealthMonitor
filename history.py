
import csv
import os
from datetime import datetime

HISTORY_FILE = "monitoring_history.csv"


def save_history(device_name, ip, result):
    file_exists = os.path.exists(HISTORY_FILE)

    with open(HISTORY_FILE, "a", newline="") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow([
                "timestamp",
                "device_name",
                "ip_address",
                "status",
                "packets_sent",
                "packets_received",
                "packet_loss_percent",
                "average_latency_ms"
            ])

        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            device_name,
            ip,
            result["status"],
            result["packets_sent"],
            result["packets_received"],
            round(result["packet_loss"], 1),
            result["average_latency"]
        ])
