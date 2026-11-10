# Recorded results from the original lab

These are the observations from the experiment discussed in the [published article](https://www.edgarcloudnotes.com/inside-ecs-networking-what-service-discovery-and-dns-reveal-about-microservices-communication/). They are **not** outputs produced by the newly reconstructed scripts in this repository.

## Scaling and request distribution

- Payments scaled to **3** Fargate tasks.
- DNS returned three Payments task private IP addresses.
- Direct HTTP calls to each known task IP returned HTTP 200.
- **30 consecutive hostname-based requests** all returned HTTP 200 from the same Payments task (`172.31.100.131`).
- Interpretation: DNS-based discovery of multiple endpoints does not ensure per-request HTTP load balancing. The experiment did not isolate which client/resolver behavior caused that particular concentration.

## Single-task interruption

- A Payments task at `172.31.100.97` was stopped while two others remained.
- Last observed response from stopped task: `2026-11-09T10:05:03.894361Z` — sample **#229**, HTTP 200.
- Next sample: `2026-11-09T10:05:04.900299Z` — **#230**, HTTP 200 from surviving task `172.31.101.139`.
- Replacement task `172.31.100.11` successfully served sample **#259** at `2026-11-09T10:05:34.092668Z`.
- Among 273 monitored requests, **273 succeeded** and **0 errors were logged**.

The ~1-second interval between samples #229 and #230 is the monitoring cadence, **not** a measured exact failover time or guaranteed zero downtime.

## Complete Payments outage

- Payments deliberately scaled from desired count **3 to 0**, then later restored.
- Last success before outage: `2026-11-09T10:21:00.920442Z`, sample **#90**, HTTP 200 from `172.31.100.11`.
- First failure: `2026-11-09T10:21:01.937026Z`, sample **#91**, with name-resolution/connection failure (not HTTP 500).
- First success after recovery: `2026-11-09T10:24:02.608020Z`, sample **#271**, HTTP 200 from `172.31.100.158`.
- Monitor totals: **369 samples**, **189 HTTP 200**, **180 failures**, **0 other responses**.
- New Payments task IPs after restoration: `172.31.100.158`, `172.31.101.11`, `172.31.101.205`.
- Final observed ECS state: Orders **1/1**, Payments **3/3**.

The **~180.67 seconds** between first failure and first recovery includes the **deliberate time at desired count 0**. It must **not** be interpreted as ECS restart time, DNS propagation time or a service SLA. The scale-up initiation timestamp was not recorded.

## Engineering takeaways

1. A Cloud Map A-record answer provides endpoints, not HTTP load balancing.
2. Test DNS resolution and HTTP connectivity separately.
3. Replica count helps availability, but the client still needs bounded timeouts, retries with backoff/jitter and appropriate connection handling.
4. Observe both service health and DNS registration changes during failures.
5. Compare this architecture with ECS Service Connect or an internal load balancer when application traffic distribution and service-to-service behavior require additional capabilities.

The private IP addresses and timestamps are historical lab observations, not values to copy into a new deployment.
