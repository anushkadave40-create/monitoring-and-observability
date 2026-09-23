import time
import random
import cProfile
import pstats
import io
import statistics
import threading


# ============================================================
# STEP 1: GROWTH MODEL
# ============================================================

def model_growth(current, growth_per_month, capacity, alert_threshold=0.80):
    results = []
    value = current
    months_to_alert = None
    months_to_full = None

    for month in range(1, 61):
        value += growth_per_month
        utilisation = value / capacity

        results.append({
            "month": month,
            "value": round(value, 1),
            "utilisation": round(utilisation, 3)
        })

        if months_to_alert is None and utilisation >= alert_threshold:
            months_to_alert = month

        if months_to_full is None and utilisation >= 1.0:
            months_to_full = month
            break

    return results, months_to_alert, months_to_full


def model_exponential_growth(current, monthly_growth_pct, capacity,
                             alert_threshold=0.80):
    results = []
    value = current
    months_to_alert = None
    months_to_full = None

    for month in range(1, 61):
        value *= (1 + monthly_growth_pct / 100)
        utilisation = value / capacity

        results.append({
            "month": month,
            "value": round(value, 1),
            "utilisation": round(utilisation, 3)
        })

        if months_to_alert is None and utilisation >= alert_threshold:
            months_to_alert = month

        if months_to_full is None and utilisation >= 1.0:
            months_to_full = month
            break

    return results, months_to_alert, months_to_full


print("=== DATABASE DISK CAPACITY FORECAST ===")

results, to_alert, to_full = model_growth(
    current=450,
    growth_per_month=8,
    capacity=1000,
    alert_threshold=0.80
)

print(f"Linear growth: alert at month {to_alert}, full at month {to_full}")

_, to_alert_exp, to_full_exp = model_exponential_growth(
    current=450,
    monthly_growth_pct=5,
    capacity=1000
)

print(
    f"Exponential growth (5%/mo): "
    f"alert at month {to_alert_exp}, full at month {to_full_exp}"
)

print("\nMonth-by-month forecast (linear):")

for r in results[:12]:
    bar = "#" * int(r["utilisation"] * 20)
    print(
        f"  Month {r['month']:2}: "
        f"{r['value']:7.1f} GB "
        f"({r['utilisation']*100:.1f}%) {bar}"
    )


# ============================================================
# STEP 2: SATURATION MONITOR
# ============================================================

class SaturationMonitor:

    THRESHOLDS = {
        "cpu": {"warning": 70, "critical": 85},
        "memory": {"warning": 75, "critical": 85},
        "disk": {"warning": 75, "critical": 85},
        "db_conns": {"warning": 70, "critical": 85},
    }

    def __init__(self):
        self._history = {k: [] for k in self.THRESHOLDS}

    def record(self, resource, value_pct):
        self._history[resource].append((time.time(), value_pct))

    def check(self, resource, value_pct):
        thresholds = self.THRESHOLDS[resource]

        if value_pct >= thresholds["critical"]:
            return "CRITICAL", thresholds["critical"]

        elif value_pct >= thresholds["warning"]:
            return "WARNING", thresholds["warning"]

        return "OK", None

    def average(self, resource, last_n=10):
        history = self._history[resource]

        if not history:
            return 0

        values = [v for _, v in history[-last_n:]]

        return round(statistics.mean(values), 1)

    def report(self):
        print("\n=== SATURATION REPORT ===")

        for resource in self.THRESHOLDS:
            avg = self.average(resource)
            status, threshold = self.check(resource, avg)

            icon = (
                "🔴" if status == "CRITICAL"
                else "🟡" if status == "WARNING"
                else "🟢"
            )

            print(
                f"  {icon} {resource:12} "
                f"{avg:5.1f}%  [{status}]"
            )

        print()


monitor = SaturationMonitor()

for i in range(30):

    is_peak = 10 <= i <= 20

    monitor.record(
        "cpu",
        random.uniform(75, 92)
        if is_peak else random.uniform(20, 45)
    )

    monitor.record(
        "memory",
        random.uniform(60, 70)
    )

    monitor.record(
        "disk",
        random.uniform(70, 73)
    )

    monitor.record(
        "db_conns",
        random.uniform(80, 88)
        if is_peak else random.uniform(30, 45)
    )

monitor.report()


# ============================================================
# STEP 3: LOAD SIMULATOR
# ============================================================

class LoadSimulator:

    def __init__(self):
        self.results = []
        self._lock = threading.Lock()

    def _run_one(self, target_fn, user_id):

        start = time.perf_counter()

        try:
            target_fn(user_id)
            success = True

        except Exception:
            success = False

        elapsed_ms = (time.perf_counter() - start) * 1000

        with self._lock:
            self.results.append({
                "ms": elapsed_ms,
                "ok": success
            })

    def run(self, target_fn, n_users=10, requests_per_user=50):

        threads = []
        self.results = []

        def user_session(user_id):

            for _ in range(requests_per_user):

                self._run_one(target_fn, user_id)

                time.sleep(
                    random.uniform(0.01, 0.05)
                )

        for i in range(n_users):

            t = threading.Thread(
                target=user_session,
                args=(i,)
            )

            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        return self.report()

    def report(self):

        if not self.results:
            return {}

        times = sorted(
            r["ms"] for r in self.results
        )

        errors = sum(
            1 for r in self.results
            if not r["ok"]
        )

        n = len(times)

        return {
            "total_requests": n,
            "errors": errors,
            "error_rate_pct": round(errors / n * 100, 2),
            "p50_ms": round(times[int(n * 0.50)], 1),
            "p95_ms": round(times[int(n * 0.95)], 1),
            "p99_ms": round(times[int(n * 0.99)], 1),
            "max_ms": round(times[-1], 1),
        }


def fake_api_endpoint(user_id):

    time.sleep(
        max(0, random.gauss(0.12, 0.04))
    )

    if random.random() < 0.02:
        raise Exception("simulated error")


print("\n=== LOAD TEST: 10 users, 50 requests each ===")

sim = LoadSimulator()

stats = sim.run(
    fake_api_endpoint,
    n_users=10,
    requests_per_user=50
)

print("Results:")

for k, v in stats.items():
    print(f"  {k}: {v}")


# ============================================================
# STEP 4: PERFORMANCE PROFILER
# ============================================================

def profile_function(fn, *args, top_n=10):

    profiler = cProfile.Profile()

    profiler.enable()

    fn(*args)

    profiler.disable()

    stream = io.StringIO()

    stats = pstats.Stats(
        profiler,
        stream=stream
    )

    stats.sort_stats("cumulative")
    stats.print_stats(top_n)

    return stream.getvalue()


def get_user_orders_slow(user_ids):

    results = []

    for uid in user_ids:

        time.sleep(0.001)

        results.append({
            "user_id": uid,
            "orders": random.randint(0, 10)
        })

    return results


def get_user_orders_fast(user_ids):

    time.sleep(0.005)

    return [
        {
            "user_id": uid,
            "orders": random.randint(0, 10)
        }
        for uid in user_ids
    ]


user_ids = list(range(100))

start = time.perf_counter()

get_user_orders_slow(user_ids)

slow_time = (
    time.perf_counter() - start
) * 1000


start = time.perf_counter()

get_user_orders_fast(user_ids)

fast_time = (
    time.perf_counter() - start
) * 1000


print("\n=== N+1 QUERY COMPARISON ===")

print(
    f"Slow (N+1 queries):  "
    f"{slow_time:.1f}ms for 100 users"
)

print(
    f"Fast (batch query):  "
    f"{fast_time:.1f}ms for 100 users"
)

print(
    f"Speedup: "
    f"{slow_time / fast_time:.1f}x faster"
)

print("\nProfiling the slow version:")

output = profile_function(
    get_user_orders_slow,
    user_ids
)

for line in output.split("\n")[:15]:
    print(line)


print("\n=== EXERCISE 6.6 COMPLETE ===")
