import time
import random

from prometheus_client import (
    start_http_server,
    Counter,
    Gauge,
    Histogram
)


# Define metrics
REQUEST_COUNT = Counter(
    "sre_lab_requests_total",
    "Total requests",
    ["status"]
)

ACTIVE_USERS = Gauge(
    "sre_lab_active_users",
    "Current active users"
)

REQUEST_LATENCY = Histogram(
    "sre_lab_request_duration_seconds",
    "Request latency"
)


# Expose metrics on port 8000
start_http_server(8000)

print("Metrics server running on :8000 — Ctrl+C to stop")


# Simulate traffic
while True:

    latency = random.uniform(0.01, 0.5)

    status = (
        "500"
        if random.random() < 0.05
        else "200"
    )

    REQUEST_COUNT.labels(
        status=status
    ).inc()

    ACTIVE_USERS.set(
        random.randint(10, 50)
    )

    with REQUEST_LATENCY.time():
        time.sleep(latency)