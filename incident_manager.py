from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional
import uuid
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
log = logging.getLogger("incident_manager")


class Severity(Enum):
    P1 = "P1 - Critical"
    P2 = "P2 - High"
    P3 = "P3 - Medium"
    P4 = "P4 - Low"


class IncidentStatus(Enum):
    DETECTING = "detecting"
    TRIAGING = "triaging"
    RESPONDING = "responding"
    MITIGATED = "mitigated"
    RESOLVED = "resolved"


@dataclass
class TimelineEvent:
    timestamp: datetime
    author: str
    message: str


@dataclass
class Incident:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8].upper())
    title: str = ""
    severity: Severity = Severity.P3
    status: IncidentStatus = IncidentStatus.DETECTING
    commander: Optional[str] = None
    responders: List[str] = field(default_factory=list)
    timeline: List[TimelineEvent] = field(default_factory=list)
    affected_services: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    mitigated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    root_cause: str = ""
    action_items: List[str] = field(default_factory=list)

    def duration_minutes(self):
        end = self.resolved_at or datetime.now()
        return int((end - self.created_at).total_seconds() / 60)


class IncidentManager:
    def __init__(self):
        self._incidents = {}

    def declare(self, title, severity, services, commander=None):
        inc = Incident(
            title=title,
            severity=severity,
            status=IncidentStatus.TRIAGING,
            commander=commander,
            affected_services=services
        )
        self._incidents[inc.id] = inc
        self.add_timeline(
            inc.id,
            "system",
            f"Incident declared: {title} [{severity.value}]"
        )
        if commander:
            self.add_timeline(
                inc.id,
                "system",
                f"Incident commander: {commander}"
            )
        log.info(
            f"INCIDENT DECLARED: INC-{inc.id} | "
            f"{severity.value} | {title}"
        )
        return inc.id

    def add_timeline(self, inc_id, author, message):
        inc = self._incidents[inc_id]
        event = TimelineEvent(datetime.now(), author, message)
        inc.timeline.append(event)
        log.info(f"[INC-{inc_id}] {author}: {message}")

    def update_status(self, inc_id, status, author="system"):
        inc = self._incidents[inc_id]
        old = inc.status.value
        inc.status = status

        if status == IncidentStatus.MITIGATED:
            inc.mitigated_at = datetime.now()
        elif status == IncidentStatus.RESOLVED:
            inc.resolved_at = datetime.now()

        self.add_timeline(
            inc_id,
            author,
            f"Status changed: {old} -> {status.value}"
        )

    def add_responder(self, inc_id, name):
        inc = self._incidents[inc_id]
        inc.responders.append(name)
        self.add_timeline(
            inc_id,
            "system",
            f"Responder joined: {name}"
        )

    def add_action_item(self, inc_id, item):
        self._incidents[inc_id].action_items.append(item)

    def set_root_cause(self, inc_id, cause):
        self._incidents[inc_id].root_cause = cause
        self.add_timeline(
            inc_id,
            "system",
            f"Root cause identified: {cause}"
        )

    def get(self, inc_id):
        return self._incidents.get(inc_id)

    def list_active(self):
        return [
            i for i in self._incidents.values()
            if i.status != IncidentStatus.RESOLVED
        ]


mgr = IncidentManager()

print("Data model defined")
print("IncidentManager ready")
print("\n=== INCIDENT SIMULATION ===")

inc_id = mgr.declare(
    title="Payment service: 45% error rate",
    severity=Severity.P1,
    services=["payment-service", "checkout-api"],
    commander="alice@company.com"
)

time.sleep(0.1)

mgr.add_responder(inc_id, "bob@company.com")
mgr.add_responder(inc_id, "charlie@company.com")
mgr.add_timeline(
    inc_id,
    "alice",
    "Status page updated: We are aware of payment issues"
)

time.sleep(0.1)

mgr.update_status(
    inc_id,
    IncidentStatus.RESPONDING,
    "alice"
)

mgr.add_timeline(
    inc_id,
    "bob",
    "Checked payment logs: Stripe API returning 503 for all requests"
)

mgr.add_timeline(
    inc_id,
    "bob",
    "Verified: Stripe status page shows Investigating"
)

mgr.add_timeline(
    inc_id,
    "charlie",
    "Database connections normal - ruling out DB cause"
)

time.sleep(0.1)

mgr.add_timeline(
    inc_id,
    "bob",
    "Enabling payment fallback mode - queuing orders"
)

mgr.add_timeline(
    inc_id,
    "alice",
    "Status page updated: Payments queued, no orders lost"
)

mgr.update_status(
    inc_id,
    IncidentStatus.MITIGATED,
    "alice"
)

time.sleep(0.1)

mgr.add_timeline(
    inc_id,
    "charlie",
    "Stripe API returning 200 - processing queued payments"
)

mgr.add_timeline(
    inc_id,
    "alice",
    "All queued payments processed. Error rate back to 0.3%"
)

mgr.update_status(
    inc_id,
    IncidentStatus.RESOLVED,
    "alice"
)

mgr.set_root_cause(
    inc_id,
    "Stripe payment gateway outage - external dependency failure"
)

mgr.add_action_item(
    inc_id,
    "Enable automatic fallback mode when Stripe error rate > 5% "
    "(owner: bob, due: 2 weeks)"
)

mgr.add_action_item(
    inc_id,
    "Add Stripe status page to monitoring dashboard "
    "(owner: charlie, due: 1 week)"
)

mgr.add_action_item(
    inc_id,
    "Document payment fallback runbook "
    "(owner: alice, due: 1 week)"
)


def generate_postmortem(mgr, inc_id):
    inc = mgr.get(inc_id)

    if not inc:
        return "Incident not found"

    lines = []
    sep = "=" * 60

    lines.append(sep)
    lines.append(f"POST-MORTEM: INC-{inc.id}")
    lines.append(sep)
    lines.append(f"Title:    {inc.title}")
    lines.append(f"Severity: {inc.severity.value}")
    lines.append(f"Status:   {inc.status.value}")
    lines.append(f"Duration: {inc.duration_minutes()} minutes")

    if inc.mitigated_at:
        ttm = int(
            (inc.mitigated_at - inc.created_at).total_seconds() / 60
        )
        lines.append(f"Time to mitigate: {ttm} minutes")

    lines.append(f"Commander: {inc.commander or 'N/A'}")
    lines.append(f"Responders: {', '.join(inc.responders)}")
    lines.append(
        f"Affected services: {', '.join(inc.affected_services)}"
    )
    lines.append("")

    lines.append("ROOT CAUSE")
    lines.append("-" * 40)
    lines.append(inc.root_cause or "TBD")
    lines.append("")

    lines.append("TIMELINE")
    lines.append("-" * 40)

    for event in inc.timeline:
        ts = event.timestamp.strftime("%H:%M:%S")
        lines.append(
            f"  {ts} [{event.author}] {event.message}"
        )

    lines.append("")
    lines.append("ACTION ITEMS")
    lines.append("-" * 40)

    for i, item in enumerate(inc.action_items, 1):
        lines.append(f"  {i}. {item}")

    lines.append("")
    lines.append(sep)

    return "\n".join(lines)


postmortem = generate_postmortem(mgr, inc_id)

print("\n" + postmortem)

with open("postmortem.txt", "w") as f:
    f.write(postmortem)

print("\nPost-mortem saved to postmortem.txt")


def auto_detect_severity(
    error_rate_pct,
    affected_services,
    is_revenue_impacting
):
    if error_rate_pct >= 20 and is_revenue_impacting:
        return Severity.P1
    elif error_rate_pct >= 5 or (
        is_revenue_impacting and error_rate_pct >= 1
    ):
        return Severity.P2
    elif error_rate_pct >= 1 or len(affected_services) > 2:
        return Severity.P3
    else:
        return Severity.P4


scenarios = [
    (45, ["payment-service"], True),
    (8, ["checkout-api", "cart-service"], False),
    (1.5, ["profile-service"], False),
    (0.2, ["admin-dashboard"], False),
]

print("\nAuto-severity detection:")

for err, services, revenue in scenarios:
    sev = auto_detect_severity(
        err,
        services,
        revenue
    )
    print(
        f"  err={err}%, services={len(services)}, "
        f"revenue={revenue} -> {sev.value}"
    )
