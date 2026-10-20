# Network Health Monitoring and Fault Diagnosis System

## Overview
A Python-based network monitoring application that checks device connectivity, tracks network performance, detects outages, and records recovery incidents through a Flask web dashboard.

## Features
- Device connectivity monitoring using ping checks
- Device status, packet loss, and latency reporting
- CSV-based monitoring history
- Fault diagnosis using consecutive failure thresholds
- Persistent outage and recovery records using SQLite
- Latency and packet-loss charts using Matplotlib
- Packet Tracer simulation results displayed in the dashboard
- Automatic dashboard refresh

## Technologies
- Python
- Flask
- Matplotlib
- CSV
- SQLite
- Cisco Packet Tracer
- HTML and CSS

## Project Files
- `app.py` — Flask dashboard and monitoring workflow
- `monitor.py` — Device connectivity checks
- `history.py` — Saves monitoring history
- `fault_diagnosis.py` — Detects outages and recovery
- `incident_history.py` — Persistent incident database operations
- `charts.py` — Generates performance charts
- `devices.json` — Configured monitoring devices
- `simulation_results.csv` — Packet Tracer simulation results

## How to Run
1. Install Python and the required dependencies.
2. Open a terminal in the project folder.
3. Run `python app.py`.
4. Open `http://127.0.0.1:5000` in a browser.
5. To regenerate performance charts, run `python charts.py`.

## Testing
Verify device status reporting, fault detection, recovery handling, chart generation, and persistent incident history using the provided test scripts.

## Limitations
Monitoring depends on ping responses and network permissions. Packet Tracer results are loaded from a CSV file, and charts display the most recently generated images.

## Future Improvements
- Scheduled chart regeneration
- More detailed diagnostic rules
- Exportable monitoring reports
- Improved dashboard filtering and visualization