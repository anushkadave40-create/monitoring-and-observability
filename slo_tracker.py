import random
from datetime import datetime, timedelta

def generate_request_log(days=30, requests_per_hour=1000, error_rate=0.002):
    """
    Generate a realistic 30-day request log.
    error_rate=0.002 means ~0.2% errors.
    """
    logs = []
    now = datetime.now()
    start = now - timedelta(days=days)

    current = start

    while current < now:
        # Simulate requests for this hour
        for _ in range(requests_per_hour):

            # Inject a spike of errors on day 15
            is_incident_window = (current - start).days == 15

            effective_error_rate = (
                0.15 if is_incident_window else error_rate
            )

            success = random.random() > effective_error_rate

            latency_ms = (
                random.gauss(120, 30)
                if success
                else random.gauss(800, 100)
            )

            logs.append({
                "timestamp": current,
                "success": success,
                "latency_ms": max(1, latency_ms)
            })

        current += timedelta(hours=1)

    print(f"Generated {len(logs):,} requests over {days} days")

    return logs


logs = generate_request_log()
def calculate_sli(logs):
    """Availability SLI: successful requests / total requests."""
    if not logs:
        return 0.0

    total = len(logs)
    successful = sum(1 for r in logs if r["success"])

    sli = (successful / total) * 100

    return round(sli, 4)


def calculate_latency_sli(logs, threshold_ms=200):
    """Latency SLI: requests under threshold / total requests."""
    if not logs:
        return 0.0

    total = len(logs)

    fast = sum(
        1 for r in logs
        if r["latency_ms"] < threshold_ms
    )

    return round((fast / total) * 100, 4)


availability_sli = calculate_sli(logs)
latency_sli = calculate_latency_sli(logs)

print(f"Availability SLI: {availability_sli}%")
print(f"Latency SLI (P<200ms): {latency_sli}%")
def calculate_error_budget(logs, slo_percent=99.9, window_days=30):
    """
    Returns how much error budget is remaining.
    """

    total_requests = len(logs)
    slo_fraction = slo_percent / 100

    # How many failures are allowed under the SLO?
    allowed_failures = total_requests * (1 - slo_fraction)

    # How many failures actually happened?
    actual_failures = sum(
        1 for r in logs
        if not r["success"]
    )

    # Budget remaining
    budget_remaining = allowed_failures - actual_failures

    budget_percent = (
        (budget_remaining / allowed_failures) * 100
        if allowed_failures > 0
        else 0
    )

    total_minutes = window_days * 24 * 60

    allowed_downtime_min = (
        total_minutes * (1 - slo_fraction)
    )

    return {
        "slo_percent": slo_percent,
        "allowed_failures": round(allowed_failures),
        "actual_failures": actual_failures,
        "budget_remaining_requests": round(budget_remaining),
        "budget_remaining_percent": round(budget_percent, 1),
        "allowed_downtime_minutes": round(allowed_downtime_min, 1),
        "is_breached": budget_remaining < 0
    }


budget = calculate_error_budget(
    logs,
    slo_percent=99.9
)

print("\nError Budget Report:")

for key, value in budget.items():
    print(f"  {key}: {value}")
    from collections import defaultdict


def daily_budget_burn(logs, slo_percent=99.9):
    """Show how the error budget was consumed day by day."""

    now = datetime.now()
    start = now - timedelta(days=30)

    slo_fraction = slo_percent / 100

    # Group requests by day number
    by_day = defaultdict(
        lambda: {"total": 0, "failed": 0}
    )

    for r in logs:
        day_num = (r["timestamp"] - start).days

        by_day[day_num]["total"] += 1

        if not r["success"]:
            by_day[day_num]["failed"] += 1

    print(f"\nDaily Error Budget Burn (SLO: {slo_percent}%)")
    print("  Day | Requests | Failures | Allowed | Status")
    print(f"  {'—' * 55}")

    for day in sorted(by_day.keys()):
        d = by_day[day]

        allowed = d["total"] * (1 - slo_fraction)

        status = (
            "⚠ OVER BUDGET"
            if d["failed"] > allowed
            else "✓ OK"
        )

        print(
            f"  {day:3} | "
            f"{d['total']:8,} | "
            f"{d['failed']:8,} | "
            f"{allowed:7.1f} | "
            f"{status}"
        )


daily_budget_burn(logs)
def check_budget_alert(budget, warning_threshold=25, critical_threshold=5):
    """
    Alert if budget is running low.
    warning_threshold: alert at 25% remaining
    critical_threshold: alert at 5% remaining
    """

    pct = budget["budget_remaining_percent"]

    if budget["is_breached"]:
        print("🚨 CRITICAL: Error budget is EXHAUSTED — SLO is breached!")
        print("   → Freeze all non-critical deployments immediately")
        print("   → Page on-call lead and engineering manager")

    elif pct < critical_threshold:
        print(f"🚨 CRITICAL: Only {pct}% error budget remaining")
        print("   → Stop all deployments, focus on reliability")

    elif pct < warning_threshold:
        print(f"⚠ WARNING: {pct}% error budget remaining")
        print("   → Review upcoming deployments, increase caution")

    else:
        print(f"✓ OK: {pct}% error budget remaining — healthy")
        print("   → Normal deployment velocity is fine")


check_budget_alert(budget)
def run_slo_report(days=30, slo_percent=99.9):
    print("\n" + "=" * 55)
    print(
        f"SLO HEALTH REPORT — Generated "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    print("=" * 55)

    print(
        f"Window: {days} days | "
        f"SLO Target: {slo_percent}%"
    )

    logs = generate_request_log(days=days)

    avail = calculate_sli(logs)
    latency = calculate_latency_sli(logs)

    budget = calculate_error_budget(
        logs,
        slo_percent=slo_percent,
        window_days=days
    )

    print("\nSLIs:")
    print(
        f"  Availability: {avail}% "
        f"(target: {slo_percent}%)"
    )
    print(
        f"  Latency<200ms: {latency}%"
    )

    print("\nError Budget:")
    print(
        f"  Allowed failures: "
        f"{budget['allowed_failures']:,}"
    )
    print(
        f"  Actual failures:  "
        f"{budget['actual_failures']:,}"
    )
    print(
        f"  Remaining:        "
        f"{budget['budget_remaining_percent']}%"
    )
    print(
        f"  Allowed downtime: "
        f"{budget['allowed_downtime_minutes']} minutes/month"
    )

    print()

    check_budget_alert(budget)

    print("=" * 55)
    print()


run_slo_report(days=30, slo_percent=99.9)