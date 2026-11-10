"""Count which Payments instance answers sequential hostname-based requests.

This illustrates observed client behavior, not guaranteed DNS load balancing.
"""
import argparse
from collections import Counter
import requests


def main():
    parser = argparse.ArgumentParser(description="Measure responding Payments task IPs")
    parser.add_argument("--url", default="http://payments.lab.internal:5000/payment")
    parser.add_argument("--requests", type=int, default=30)
    parser.add_argument("--timeout", type=float, default=5)
    args = parser.parse_args()
    if args.requests < 1:
        parser.error("--requests must be positive")

    counts = Counter()
    # A new GET per iteration. Underlying library/runtime behavior can vary.
    for index in range(1, args.requests + 1):
        try:
            response = requests.get(args.url, timeout=args.timeout)
            response.raise_for_status()
            source = response.json().get("ip", "<missing-ip>")
            counts[source] += 1
            print(f"{index:03d}: HTTP={response.status_code} payments_ip={source}")
        except (requests.RequestException, ValueError) as exc:
            counts["ERROR"] += 1
            print(f"{index:03d}: ERROR={exc}")
    print("\nObserved responses:")
    for key, count in counts.most_common():
        print(f"{key}: {count}")


if __name__ == "__main__":
    main()
