"""Inspect Cloud Map DNS A records. Run where the VPC private DNS name resolves."""
import argparse
import socket


def main():
    parser = argparse.ArgumentParser(description="Resolve a Cloud Map service hostname")
    parser.add_argument("--host", default="payments.lab.internal")
    args = parser.parse_args()

    try:
        _hostname, _aliases, addresses = socket.gethostbyname_ex(args.host)
    except socket.gaierror as exc:
        print(f"DNS resolution failed for {args.host}: {exc}")
        raise SystemExit(1) from exc

    for address in sorted(set(addresses)):
        print(address)
    print(f"Unique IPv4 addresses: {len(set(addresses))}")


if __name__ == "__main__":
    main()
