"""Timestamped DNS and HTTP probe for scaling and outage experiments.

Newly reconstructed sample; not the original /tmp/outage_monitor.py from the lab.
"""
import argparse
from datetime import datetime, timezone
import socket
import time

import requests


def main():
    parser = argparse.ArgumentParser(description="Monitor Payments DNS and HTTP availability")
    parser.add_argument("--host", default="payments.lab.internal")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--interval", type=float, default=1)
    parser.add_argument("--count", type=int, default=1200)
    parser.add_argument("--timeout", type=float, default=3)
    args = parser.parse_args()
    if args.interval < 0 or args.count < 1:
        parser.error("interval must be nonnegative and count positive")
    url = f"http://{args.host}:{args.port}/payment"
    for index in range(1, args.count + 1):
        now = datetime.now(timezone.utc).isoformat()
        try:
            addresses = sorted(set(socket.gethostbyname_ex(args.host)[2]))
            dns = ",".join(addresses)
        except socket.gaierror as exc:
            addresses = []
            dns = f"DNS_ERROR({exc})"
        try:
            response = requests.get(url, timeout=args.timeout)
            payment_ip = response.json().get("ip", "?") if response.ok else "?"
            print(f"{now} #{index} DNS={dns} HTTP={response.status_code} IP={payment_ip}", flush=True)
        except (requests.RequestException, ValueError) as exc:
            print(f"{now} #{index} DNS={dns} HTTP_ERROR={type(exc).__name__}: {exc}", flush=True)
        if index < args.count:
            time.sleep(args.interval)


if __name__ == "__main__":
    main()
