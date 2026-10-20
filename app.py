
from flask import Flask, render_template_string, send_file
from charts import generate_charts
from monitor import ping_device, check_tcp_port
from history import save_history
from fault_diagnosis import FaultDiagnosis
from service_diagnosis import ServiceDiagnosis
from incident_history import (
    initialize_database,
    record_outage,
    record_recovery,
    get_incidents,
    get_open_incidents,
)

import json
import time
import csv
import os
import random

DEMO_MODE = True

# --------------------------------------------------
# APPLICATION SETUP
# --------------------------------------------------

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FAILURE_THRESHOLD = 2

diagnosis = FaultDiagnosis(
    failure_threshold=FAILURE_THRESHOLD
)

service_diagnosis = ServiceDiagnosis(
    failure_threshold=FAILURE_THRESHOLD
)

initialize_database()


# Restore unresolved host outages after a Flask restart.
for incident in reversed(get_open_incidents()):
    device_name = incident["device_name"]
    ip_address = incident["ip_address"]

    diagnosis.devices[device_name] = {
        "ip": ip_address,
        "consecutive_failures": FAILURE_THRESHOLD,
        "outage_active": True,
        "outage_started_at": incident["start_time"],
    }


# --------------------------------------------------
# DASHBOARD HTML
# --------------------------------------------------

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="10">

    <title>Network Health Monitoring System</title>

    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f1f5f9;
            margin: 0;
            padding: 30px;
            color: #1e293b;
        }

        h1 {
            color: #0f172a;
        }

        .card {
            background: white;
            padding: 20px;
            border-radius: 12px;
            margin: 20px 0;
            box-shadow: 0 3px 12px #00000010;
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
        }

        th, td {
            padding: 12px;
            border-bottom: 1px solid #e2e8f0;
            text-align: left;
        }

        th {
            background: #e2e8f0;
        }

        .UP, .OPEN, .RECOVERED, .SERVICE_RECOVERED {
            color: #15803d;
            font-weight: bold;
        }

        .DOWN, .CLOSED_OR_UNREACHABLE, .OUTAGE_CONFIRMED,
        .SERVICE_FAILURE {
            color: #dc2626;
            font-weight: bold;
        }

        .DEGRADED, .FAILURE_RECORDED {
            color: #b45309;
            font-weight: bold;
        }

        .ERROR {
            color: #7c3aed;
            font-weight: bold;
        }

        .chart {
            display: block;
            width: 100%;
            max-width: 1000px;
            height: auto;
            margin-bottom: 24px;
        }

        .alert {
            padding: 12px;
            margin: 10px 0;
            border-radius: 8px;
            background: #f8fafc;
            border-left: 4px solid #64748b;
        }

        .alert-error {
            border-left-color: #dc2626;
        }

        .alert-success {
            border-left-color: #15803d;
        }

        @media (max-width: 700px) {
            body {
                padding: 12px;
            }

            .card {
                padding: 12px;
            }

            th, td {
                padding: 8px;
                white-space: nowrap;
            }
        }
    </style>
</head>

<body>

    <h1>Network Health Monitoring System</h1>
    <p><strong>DEMO MODE:</strong> Device statuses may be simulated.</p>

    <div class="card">
        <h2>Network Overview</h2>

        <p>Devices monitored: {{ results|length }}</p>
        <p>Devices UP (ICMP): {{ up_count }}</p>
        <p>Devices DEGRADED (ICMP): {{ degraded_count }}</p>
        <p>Devices DOWN (ICMP): {{ down_count }}</p>
        <p>Confirmed host outages: {{ outage_count }}</p>
        <p>Last checked: {{ checked_at }}</p>
        <p>Failure threshold: {{ threshold }} consecutive failed checks</p>
        <p>Monitoring methods: ICMP ping and TCP connection tests</p>
    </div>


    <div class="card">
    <h2>Network Performance Charts</h2>

    <h3>Latency Over Time</h3>
    <img class="chart"
         src="/charts/latency?v={{ chart_version }}"
         alt="Network latency over time">

    <h3>Packet Loss Over Time</h3>
    <img class="chart"
         src="/charts/packet-loss?v={{ chart_version }}"
         alt="Network packet loss over time">
    </div>

    <div class="card">
        <h2>Fault Diagnosis Alerts</h2>

        {% if diagnosis_events %}
            {% for event in diagnosis_events %}
                <div class="alert
                    {% if event.event in
                        ['OUTAGE_CONFIRMED', 'SERVICE_FAILURE'] %}
                        alert-error
                    {% elif event.event in
                        ['RECOVERED', 'SERVICE_RECOVERED'] %}
                        alert-success
                    {% endif %}">

                    <strong class="{{ event.event }}">
                        {{ event.event }}
                    </strong>

                    — {{ event.message }}

                    <br>
                    <small>{{ event.time }}</small>
                </div>
            {% endfor %}
        {% else %}
            <p>No new fault-diagnosis events during this check.</p>
        {% endif %}
    </div>


    <div class="card">
        <h2>Device and Service Status</h2>

        <p>
            ICMP checks host reachability. TCP checks test whether
            a configured service port accepts a connection.
        </p>

        <table>
            <tr>
                <th>Device</th>
                <th>IP / Hostname</th>
                <th>ICMP Status</th>
                <th>Packet Loss</th>
                <th>Average Latency</th>
                <th>TCP Service Checks</th>
                <th>Consecutive Failures</th>
                <th>Outage Start</th>
            </tr>

            {% for item in results %}
            <tr>
                <td>{{ item.name }}</td>
                <td>{{ item.ip }}</td>

                <td class="{{ item.status }}">
                    {{ item.status }}
                </td>

                <td>{{ item.packet_loss }}%</td>

                <td>
                    {% if item.average_latency is not none %}
                        {{ item.average_latency }} ms
                    {% else %}
                        N/A
                    {% endif %}
                </td>

                <td>
                    {% if item.tcp_checks %}
                        {% for check in item.tcp_checks %}
                            <div>
                                <strong>{{ check.name }}</strong>
                                (port {{ check.port }}):
                                <span class="{{ check.status }}">
                                    {{ check.status }}
                                </span>

                                {% if check.latency_ms is not none %}
                                    — {{ check.latency_ms }} ms
                                {% endif %}

                                {% if check.error %}
                                    <div>
                                        <small>{{ check.error }}</small>
                                    </div>
                                {% endif %}
                            </div>
                        {% endfor %}
                    {% else %}
                        Not configured
                    {% endif %}
                </td>

                <td>{{ item.consecutive_failures }}</td>

                <td>
                    {% if item.outage_started_at %}
                        {{ item.outage_started_at }}
                    {% else %}
                        —
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>


    <div class="card">
        <h2>Persistent Host Incident History</h2>

        <p>
            This table stores host outages and recoveries in the
            incident database.
        </p>

        {% if incidents %}
        <table>
            <tr>
                <th>ID</th>
                <th>Device</th>
                <th>IP Address</th>
                <th>Outage Started</th>
                <th>Recovered At</th>
                <th>Duration</th>
                <th>Details</th>
            </tr>

            {% for incident in incidents %}
            <tr>
                <td>{{ incident.id }}</td>
                <td>{{ incident.device_name }}</td>
                <td>{{ incident.ip_address }}</td>
                <td>{{ incident.start_time }}</td>

                <td>
                    {% if incident.end_time %}
                        {{ incident.end_time }}
                    {% else %}
                        Still open
                    {% endif %}
                </td>

                <td>
                    {% if incident.duration_seconds is not none %}
                        {{ "%.1f"|format(
                            incident.duration_seconds / 60
                        ) }} minutes
                    {% else %}
                        —
                    {% endif %}
                </td>

                <td>{{ incident.message }}</td>
            </tr>
            {% endfor %}
        </table>
        {% else %}
            <p>No incidents have been recorded yet.</p>
        {% endif %}
    </div>


    <div class="card">
        <h2>Packet Tracer Simulation Results</h2>

        {% if simulation_results %}
        <table>
            <tr>
                <th>Test Name</th>
                <th>Source IP</th>
                <th>Destination IP</th>
                <th>Packets Sent</th>
                <th>Packets Received</th>
                <th>Packet Loss</th>
                <th>Status</th>
            </tr>

            {% for test in simulation_results %}
            <tr>
                <td>{{ test.test_name }}</td>
                <td>{{ test.source_ip }}</td>
                <td>{{ test.destination_ip }}</td>
                <td>{{ test.packets_sent }}</td>
                <td>{{ test.packets_received }}</td>
                <td>{{ test.packet_loss_percent }}%</td>
                <td class="{{ test.status }}">{{ test.status }}</td>
            </tr>
            {% endfor %}
        </table>
        {% else %}
            <p>No Packet Tracer simulation results found.</p>
        {% endif %}
    </div>

    <p>Page refreshes every 10 seconds.</p>

</body>
</html>
"""


# --------------------------------------------------
# DASHBOARD ROUTE
# --------------------------------------------------

@app.route("/")
def dashboard():
    devices_path = os.path.join(BASE_DIR, "devices.json")
    simulation_path = os.path.join(
        BASE_DIR, "simulation_results.csv"
    )

    with open(devices_path, "r", encoding="utf-8") as file:
        devices = json.load(file)

    simulation_results = []

    if os.path.exists(simulation_path):
        with open(
            simulation_path,
            "r",
            newline="",
            encoding="utf-8"
        ) as file:
            simulation_results = list(csv.DictReader(file))

    results = []
    diagnosis_events = []

    
    for device in devices:
        name = device["name"]
        ip = device["ip"]

        # ------------------------------------------
        # ICMP HOST MONITORING
        # ------------------------------------------

        data = ping_device(ip)

        # Random status simulation for the demo device only
        
        if DEMO_MODE:
            # Simulated results for demonstration only
            data["demo_mode"] = True

            status = random.choices(
                ["UP", "DEGRADED", "DOWN"],
                weights=[60, 20, 20],
                k=1,
            )[0]

            data["status"] = status

            if status == "UP":
                data["packet_loss"] = 0
                data["average_latency"] = round(
                    random.uniform(10, 80), 2
                )

            elif status == "DEGRADED":
                data["packet_loss"] = round(
                    random.uniform(10, 40), 1
                )
                data["average_latency"] = round(
                    random.uniform(150, 500), 2
                )

            else:
                data["packet_loss"] = 100
                data["average_latency"] = None


        save_history(name, ip, data)

        
        if DEMO_MODE:
            # Keep simulated statuses out of real incident diagnosis.
           device_state = diagnosis.devices.get(name, {
    "consecutive_failures": 0,
    "outage_started_at": None,
    "outage_active": False,
})

        else:
            
        # Always initialize/update the diagnosis state
            event = diagnosis.update(name, ip, data["status"])

        # Save incidents only for real monitoring
        if not DEMO_MODE:
            if event and event["event"] == "OUTAGE_CONFIRMED":
                open_incidents = get_open_incidents()

                already_open = any(
                    incident["device_name"] == name
                    and incident["ip_address"] == ip
                    for incident in open_incidents
                )

                if not already_open:
                    record_outage(
                        name, ip, event["time"], event["message"]
                    )

                diagnosis_events.append(event)

            elif event and event["event"] == "RECOVERED":
                record_recovery(
                    name, ip,
                    event["outage_started_at"],
                    event["time"],
                    event["message"]
                )
                diagnosis_events.append(event)

        device_state = diagnosis.devices.get(name, {
    "consecutive_failures": 0,
    "outage_started_at": None,
    "outage_active": False,
})


        # ------------------------------------------
        # TCP SERVICE MONITORING AND DIAGNOSIS
        # ------------------------------------------

        tcp_results = []

        for tcp_check in device.get("tcp_checks", []):
            port = int(tcp_check["port"])

            tcp_data = check_tcp_port(ip, port)

            service_event = service_diagnosis.update(
                device_name=name,
                ip=ip,
                port=port,
                status=tcp_data["status"],
            )

            if service_event:
                diagnosis_events.append(service_event)

            tcp_results.append({
                "name": tcp_check["name"],
                "port": port,
                "status": tcp_data["status"],
                "latency_ms": tcp_data["latency_ms"],
                "error": tcp_data["error"],
            })

        # ------------------------------------------
        # COLLECT DEVICE RESULTS
        # ------------------------------------------

        results.append({
            "name": name,
            "ip": ip,
            "status": data["status"],
            "packet_loss": round(data["packet_loss"], 1),
            "average_latency": data["average_latency"],
            "consecutive_failures": (
                device_state["consecutive_failures"]
            ),
            "outage_started_at": (
                device_state["outage_started_at"]
            ),
            "tcp_checks": tcp_results,
        })

    # ----------------------------------------------
    # DASHBOARD COUNTS
    # ----------------------------------------------

    generate_charts()

    up_count = sum(
        1 for item in results if item["status"] == "UP"
    )

    down_count = sum(
        1 for item in results if item["status"] == "DOWN"
    )
    up_count = sum(
        1 for item in results if item["status"] == "UP"
    )

    down_count = sum(
        1 for item in results if item["status"] == "DOWN"
    )

    degraded_count = sum(
        1 for item in results if item["status"] == "DEGRADED"
    )

    outage_count = sum(
        1 for state in diagnosis.devices.values()
        if state["outage_active"]
    )

    incidents = get_incidents(limit=50)

    return render_template_string(
        HTML_PAGE,
        results=results,
        simulation_results=simulation_results,
        diagnosis_events=diagnosis_events,
        incidents=incidents,
        up_count=up_count,
        degraded_count=degraded_count,
        down_count=down_count,
        outage_count=outage_count,
        checked_at=time.strftime("%Y-%m-%d %H:%M:%S"),
        threshold=FAILURE_THRESHOLD,
        chart_version=time.time(),
    )


# --------------------------------------------------
# CHART ROUTES
# --------------------------------------------------

@app.route("/charts/latency")
def latency_chart():
    chart_path = os.path.join(BASE_DIR, "latency_chart.png")

    if not os.path.exists(chart_path):
        return "Latency chart not generated. Run python charts.py first.", 404

    return send_file(chart_path, mimetype="image/png")


@app.route("/charts/packet-loss")
def packet_loss_chart():
    chart_path = os.path.join(BASE_DIR, "packet_loss_chart.png")

    if not os.path.exists(chart_path):
        return "Packet-loss chart not generated. Run python charts.py first.", 404

    return send_file(chart_path, mimetype="image/png")


# --------------------------------------------------
# RUN APPLICATION
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=False)
