
import matplotlib
matplotlib.use("Agg")

import csv
import os
from datetime import datetime, timedelta

import matplotlib.pyplot as plt


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, "monitoring_history.csv")
EXCLUDED_DEVICES = {"Recovery Integration Test"}
WINDOW_MINUTES = 30


def load_history():
    try:
        with open(HISTORY_FILE, "r", newline="", encoding="utf-8") as file:
            return list(csv.DictReader(file))
    except FileNotFoundError:
        print("Monitoring history file was not found.")
        return []


def parse_timestamp(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return None


def generate_charts():
    records = load_history()
    cutoff = datetime.now() - timedelta(minutes=WINDOW_MINUTES)

    # Keep the latest valid reading for each device.
    latest = {}

    for row in records:
        name = row.get("device_name", "Unknown")

        if name in EXCLUDED_DEVICES:
            continue

        timestamp = parse_timestamp(row.get("timestamp", ""))

        if timestamp is None or timestamp < cutoff:
            continue

        if name not in latest or timestamp >= latest[name]["timestamp"]:
            try:
                latency = float(row.get("average_latency_ms", ""))
                if latency < 0:
                    latency = None
            except (ValueError, TypeError):
                latency = None

            try:
                loss = float(row.get("packet_loss_percent", ""))
                if not 0 <= loss <= 100:
                    loss = None
            except (ValueError, TypeError):
                loss = None

            latest[name] = {
                "timestamp": timestamp,
                "latency": latency,
                "loss": loss,
            }

    if not latest:
        print("No valid monitoring records found in the last 30 minutes.")
        return

    names = list(latest.keys())

    # Consistent clean chart style.
    plt.rcParams.update({
        "font.size": 10,
        "axes.titlesize": 14,
        "axes.labelsize": 11,
    })

    # ------------------------------------------
    # Chart 1: Latest latency by device
    # ------------------------------------------
    latency_names = [
        name for name in names
        if latest[name]["latency"] is not None
    ]
    latency_values = [
        latest[name]["latency"] for name in latency_names
    ]

    fig, ax = plt.subplots(figsize=(9, 4.5), dpi=130)

    if latency_names:
        bars = ax.barh(latency_names, latency_values)
        ax.bar_label(bars, fmt="%.1f ms", padding=5, fontsize=9)
        ax.set_xlim(left=0)
        ax.set_xlabel("Latency (ms)")
        ax.set_title("Latest Network Latency by Device", pad=14)
        ax.grid(axis="x", linestyle="--", alpha=0.25)
        ax.set_axisbelow(True)
    else:
        ax.text(
            0.5, 0.5, "No valid latency readings",
            ha="center", va="center",
            transform=ax.transAxes
        )
        ax.set_title("Latest Network Latency by Device")

    fig.tight_layout()
    fig.savefig(
        os.path.join(BASE_DIR, "latency_chart.png"),
        bbox_inches="tight"
    )
    plt.close(fig)

    # ------------------------------------------
    # Chart 2: Latest packet loss by device
    # ------------------------------------------
    loss_names = [
        name for name in names
        if latest[name]["loss"] is not None
    ]
    loss_values = [latest[name]["loss"] for name in loss_names]

    fig, ax = plt.subplots(figsize=(9, 4.5), dpi=130)

    if loss_names:
        bars = ax.barh(loss_names, loss_values)
        ax.bar_label(bars, fmt="%.1f%%", padding=5, fontsize=9)
        ax.set_xlim(0, 115)
        ax.set_xlabel("Packet Loss (%)")
        ax.set_title("Latest Packet Loss by Device", pad=14)
        ax.grid(axis="x", linestyle="--", alpha=0.25)
        ax.set_axisbelow(True)
    else:
        ax.text(
            0.5, 0.5, "No valid packet-loss readings",
            ha="center", va="center",
            transform=ax.transAxes
        )
        ax.set_title("Latest Packet Loss by Device")

    fig.tight_layout()
    fig.savefig(
        os.path.join(BASE_DIR, "packet_loss_chart.png"),
        bbox_inches="tight"
    )
    plt.close(fig)

    print("Charts saved successfully!")


if __name__ == "__main__":
    generate_charts()
