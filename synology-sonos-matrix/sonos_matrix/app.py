import argparse
import os
import socket
from datetime import datetime
from typing import Dict, List, Optional

import requests
from flask import Flask, render_template, request


def discover_sonos(ip_base: str, start: int, end: int, timeout: float = 0.15) -> List[str]:
    sonos_list: List[str] = []
    for i in range(start, end + 1):
        ip = f"{ip_base}{i}"
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            result = sock.connect_ex((ip, 1400))
            if result == 0:
                sonos_list.append(ip)
        finally:
            sock.close()
    return sonos_list


def get_sonos_perf(ip: str) -> Optional[str]:
    try:
        response = requests.get(f"http://{ip}:1400/status/perf", timeout=1)
        response.raise_for_status()
        return response.text
    except requests.RequestException:
        return None


def parse_perf(raw: str) -> Dict[str, str]:
    parsed: Dict[str, str] = {}
    for line in raw.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            parsed[key.strip()] = value.strip()
    return parsed


def color_for_signal(rssi: int, snr: int) -> str:
    if rssi > -60 and snr > 25:
        return "good"
    if rssi > -70:
        return "warn"
    return "bad"


DEFAULT_SUBNET = os.getenv("SONOS_SUBNET", "192.168.1.")
DEFAULT_RANGE = os.getenv("SONOS_RANGE", "1-254")
DEFAULT_PORT = int(os.getenv("PORT", "9200"))
DEFAULT_TIMEOUT = float(os.getenv("SONOS_TIMEOUT", "0.15"))

app = Flask(__name__)


def scan(subnet: str, start: int, end: int, timeout: float) -> Dict[str, Dict[str, str]]:
    results: Dict[str, Dict[str, str]] = {}
    for ip in discover_sonos(subnet, start, end, timeout):
        raw = get_sonos_perf(ip)
        if raw:
            parsed = parse_perf(raw)
            results[ip] = parsed
    return results


def parse_range(range_value: str) -> (int, int):
    if "-" in range_value:
        start_str, end_str = range_value.split("-", 1)
        return int(start_str), int(end_str)
    value = int(range_value)
    return value, value


@app.route("/", methods=["GET", "POST"])
def index():
    subnet = request.values.get("subnet", DEFAULT_SUBNET)
    range_value = request.values.get("range", DEFAULT_RANGE)
    timeout = float(request.values.get("timeout", DEFAULT_TIMEOUT))
    start, end = parse_range(range_value)

    results = scan(subnet, start, end, timeout)
    timestamp = datetime.now()

    return render_template(
        "index.html",
        results=results,
        subnet=subnet,
        range_value=range_value,
        timeout=timeout,
        timestamp=timestamp,
    )


def run_server(host: str, port: int, subnet: str, range_value: str, timeout: float) -> None:
    app.config.update(
        SONOS_SUBNET=subnet,
        SONOS_RANGE=range_value,
        SONOS_TIMEOUT=timeout,
    )
    app.run(host=host, port=port)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Sonos network matrix server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the web server")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to bind the web server")
    parser.add_argument("--subnet", default=DEFAULT_SUBNET, help="Subnet prefix (e.g. 192.168.1.)")
    parser.add_argument("--range", dest="range_value", default=DEFAULT_RANGE, help="IP range (e.g. 1-254)")
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help="Connection timeout in seconds for Sonos discovery",
    )
    args = parser.parse_args()

    run_server(args.host, args.port, args.subnet, args.range_value, args.timeout)
