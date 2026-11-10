# Experiments

Run from within the VPC where the private Cloud Map namespace resolves. The `scripts/` examples are **reconstructions** based on the original lab's testing goals; they were not included in the original source ZIP.

Install `requests` if needed (`python -m pip install requests==2.32.3`).

## A. Verify DNS discovery

```bash
python scripts/dns_test.py --host payments.lab.internal
```

With three healthy registered Payments tasks, expect up to three private IPv4 addresses, depending on timing, health, and the resolver. Do not assume an exact order.

## B. Check direct reachability of registered task IPs

```bash
python scripts/connectivity_test.py --host payments.lab.internal --port 5000
```

For each resolved private IP, this script calls `GET /payment`. A DNS lookup succeeding does **not** prove network connectivity: security groups, routing and app readiness also matter.

## C. DNS is not per-request load balancing

```bash
python scripts/distribution_test.py --requests 30
```

The script performs 30 sequential hostname-based requests and counts the responding Payments task IPs from the JSON response. Compare the distribution with what `dns_test.py` returned. Results are client/runtime-dependent. In the original lab, all 30 requests went to one task even when three IPs resolved.

## D. Stop a single task

1. Confirm Payments desired count is 3 and all three tasks are running.
2. Begin monitoring through a VPC-connected environment:

```bash
python scripts/outage_monitor.py --count 300 --interval 1 | tee single-task-monitor.log
```

3. Stop **one** Payments task through ECS (not the entire service).
4. Track HTTP status, responding Payments IP and the DNS address list while ECS replaces the task.
5. Verify desired/running count returns to 3 and inspect CloudWatch logs.

Do not interpret a one-second log sampling gap as a precise failover-duration guarantee.

## E. Scale Payments to zero, then restore

1. Start a monitor:

```bash
python scripts/outage_monitor.py --count 1200 --interval 1 | tee full-outage-monitor.log
```

2. Scale Payments ECS desired count from 3 to **0**.
3. Wait for the service and Cloud Map registrations to reflect zero tasks; watch DNS and HTTP errors.
4. Scale Payments back to **3** and wait for healthy task registrations.
5. Observe when DNS resolution and successful HTTP responses return.

You may see `socket.gaierror` / `requests.ConnectionError` during the zero-task period; failures happen **before** an HTTP response exists. How long the outage lasts depends substantially on how long you intentionally leave desired count at zero. This is not a benchmark for ECS recovery time.

## What to record

- UTC timestamp and request number
- DNS result or resolver exception
- HTTP response code or connection error
- Responding Payments task IP
- Desired/running ECS count and any observed registration changes
- Scale-down and scale-up initiation times (if measuring operational latency)

Do not equate the DNS answer count with successful or balanced HTTP responses.
