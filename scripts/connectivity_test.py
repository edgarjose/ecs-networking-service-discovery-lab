"""Probe each IP returned for Payments directly over HTTP."""
import argparse
import socket
import requests


def main():
    parser = argparse.ArgumentParser(description="Test direct connectivity to Cloud Map IPs")
    parser.add_argument("--host", default="payments.lab.internal")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--timeout", type=float, default=3)
    args = parser.parse_args()
    try:
        addresses = sorted(set(socket.gethostbyname_ex(args.host)[2]))
    except socket.gaierror as exc:
        print(f"DNS failed: {exc}")
        raise SystemExit(1) from exc
    errors = 0
    for ip in addresses:
        try:
            response = requests.get(f"http://{ip}:{args.port}/payment", timeout=args.timeout)
            print(f"{ip}: HTTP {response.status_code} {response.text[:300]}")
            if response.status_code != 200:
                errors += 1
        except requests.RequestException as exc:
            print(f"{ip}: ERROR {exc}")
            errors += 1
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
