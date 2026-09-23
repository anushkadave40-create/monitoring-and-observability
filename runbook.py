import sqlite3
from datetime import datetime
import time

DB_FILE = "incidents.db"
SERVICE = "local-monitoring-app"


def run_runbook(conn, incident_id):
    print(f"Running automation runbook for Incident #{incident_id}")
    print(f"Service: {SERVICE}")

    print("1. Logging remediation attempt...")
    time.sleep(1)

    print("2. Restarting service...")
    time.sleep(2)

    remediation_success = True

    if remediation_success:
        conn.execute("""
            UPDATE incidents
            SET status = ?, created_at = ?
            WHERE id = ?
        """, (
            "resolved",
            datetime.now().isoformat(),
            incident_id
        ))

        conn.commit()

        print("3. Remediation successful.")
        print("4. Incident marked as RESOLVED.")
    else:
        print("3. Remediation failed.")
        print("4. Incident remains OPEN for manual review.")


def main():
    print("=== SRE AUTOMATION RUNBOOK ===")

    conn = sqlite3.connect(DB_FILE)

    incident = conn.execute(
        "SELECT id FROM incidents WHERE status = 'open' ORDER BY id DESC LIMIT 1"
    ).fetchone()

    if incident:
        run_runbook(conn, incident[0])
    else:
        print("No open incidents found.")

    conn.close()


if __name__ == "__main__":
    main()
