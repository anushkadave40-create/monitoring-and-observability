import urllib.request
import urllib.parse
import json
import sqlite3
from datetime import datetime

PROMETHEUS_URL = "http://localhost:19095"
ERROR_THRESHOLD = 0.05
DB_FILE = "incidents.db"


def get_error_rate():
    query = "rate(app_errors_total[5m]) / rate(app_requests_total[5m])"
    params = urllib.parse.urlencode({"query": query})
    url = f"{PROMETHEUS_URL}/api/v1/query?{params}"

    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            data = json.loads(response.read().decode())

        results = data["data"]["result"]

        if results:
            return float(results[0]["value"][1])

    except Exception:
        print("Prometheus unavailable - using local demo metric.")

    return 0.08


def create_database():
    conn = sqlite3.connect(DB_FILE)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT,
            error_rate REAL,
            severity TEXT,
            status TEXT,
            created_at TEXT
        )
    """)

    conn.commit()
    return conn


def create_incident(conn, error_rate):
    conn.execute("""
        INSERT INTO incidents
        (service, error_rate, severity, status, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        "local-monitoring-app",
        error_rate,
        "P2",
        "open",
        datetime.now().isoformat()
    ))

    conn.commit()


def main():
    print("=== SRE Toil Automation ===")

    conn = create_database()
    error_rate = get_error_rate()

    print(f"Current error rate: {error_rate:.2%}")
    print(f"Threshold: {ERROR_THRESHOLD:.2%}")

    if error_rate > ERROR_THRESHOLD:
        print("ALERT: Error rate exceeded threshold")
        create_incident(conn, error_rate)
        print("Incident created successfully.")
    else:
        print("No incident detected.")

    conn.close()


if __name__ == "__main__":
    main()
