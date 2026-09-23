from datetime import datetime
import time

SERVICE = "local-monitoring-app"


def restart_service(service):
    print(f"Starting remediation for: {service}")
    print("Simulating service restart...")

    time.sleep(2)

    print(f"Service '{service}' restarted successfully.")
    print(f"Remediation completed at: {datetime.now().isoformat()}")

    return True


def main():
    print("=== Auto-Remediation ===")

    success = restart_service(SERVICE)

    if success:
        print("Incident can be marked as resolved.")
    else:
        print("Remediation failed - manual review required.")


if __name__ == "__main__":
    main()
