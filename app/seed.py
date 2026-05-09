"""Synthetic data generator.

Populates the database with a realistic IT-support data set:

  * 100 users (mix of requesters, agents, admins) with realistic names,
    departments, and emails.
  * 1,000 tickets spread over the last 12 months with varied status, priority
    and category, multi-paragraph descriptions and SLA deadlines.
  * 5,000-8,000 comments (1-10 per ticket), realistic IT-support tone, mix of
    public and internal.
  * ~20 tags with a many-to-many relationship to tickets.

Run with:

    python -m app.seed
"""

from __future__ import annotations

import logging
import random
from datetime import datetime, timedelta, timezone

from faker import Faker
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import SessionLocal, init_db
from app.core.security import hash_password
from app.models.comment import Comment
from app.models.tag import Tag
from app.models.ticket import Ticket, TicketCategory, TicketPriority, TicketStatus
from app.models.user import User, UserRole

logger = logging.getLogger("seed")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s :: %(message)s")

DEPARTMENTS = [
    "Engineering",
    "Sales",
    "Marketing",
    "Finance",
    "Human Resources",
    "Operations",
    "Customer Support",
    "Legal",
    "Product",
    "Research",
    "IT",
    "Logistics",
]

TAG_NAMES = [
    "windows", "macos", "linux", "vpn", "wifi", "printer", "outlook", "teams",
    "slack", "okta", "office365", "antivirus", "phishing", "password",
    "browser", "monitor", "keyboard", "headset", "license", "permissions",
]

TICKET_TITLE_TEMPLATES: dict[TicketCategory, list[str]] = {
    TicketCategory.HARDWARE: [
        "Laptop will not power on after weekend",
        "External monitor flickering on dock {model}",
        "Keyboard keys unresponsive on {model}",
        "Headset microphone produces static during calls",
        "Hard drive showing repeated SMART warnings",
        "Docking station no longer detected",
    ],
    TicketCategory.SOFTWARE: [
        "{app} crashes on launch after recent update",
        "Cannot install {app} - error code 0x80070643",
        "{app} performance has degraded significantly",
        "License key for {app} no longer accepted",
        "{app} freezes when opening large files",
    ],
    TicketCategory.NETWORK: [
        "VPN disconnects every few minutes",
        "Cannot reach internal share \\\\fileserver\\team",
        "Slow connection to {app} from home office",
        "Wi-Fi keeps dropping in meeting room {room}",
        "DNS resolution failing for several internal hosts",
    ],
    TicketCategory.ACCOUNT: [
        "Account locked after multiple login attempts",
        "Need access to the {app} group",
        "MFA device lost - request reset",
        "Onboarding: please provision new starter",
        "Offboarding request for {name}",
    ],
    TicketCategory.EMAIL: [
        "Outlook stuck on Updating Inbox",
        "Cannot send to external recipients",
        "Suspicious email - phishing report",
        "Distribution list missing several members",
        "Calendar invitations not arriving",
    ],
    TicketCategory.SECURITY: [
        "Possible malware alert on {model}",
        "Unauthorised login from unknown location",
        "Lost device - remote wipe required",
        "Need security review of new SaaS tool",
        "Suspicious USB device prompt",
    ],
    TicketCategory.OTHER: [
        "Office printer requires service",
        "Conference room AV not working",
        "Request standing desk accessory",
        "General IT consultation requested",
    ],
}

DESCRIPTION_OPENERS = [
    "Hi team,\n\nI started experiencing this issue earlier today.",
    "Hey,\n\nReaching out because something is not working as expected.",
    "Hello support,\n\nI need help with a recurring problem.",
    "Hi,\n\nThis has been blocking me for a couple of hours now.",
    "Good morning,\n\nI noticed the following behaviour after the recent update.",
]

DESCRIPTION_BODIES = [
    "Steps I have already tried:\n- Rebooting the device\n- Checking for updates\n- Reconnecting to the corporate network",
    "I have attached a screenshot in our shared drive. The error appears intermittent and tends to happen mid-morning.",
    "Other colleagues on the same team report a similar pattern, so this might affect more than just my workstation.",
    "It started after I installed the latest patch on Tuesday evening. Things were fine before that.",
    "Could someone walk me through the recommended remediation? I would prefer not to lose my current session.",
]

DESCRIPTION_CLOSERS = [
    "\n\nThanks in advance for your help.\nBest regards.",
    "\n\nLet me know if you need additional logs.\nThanks!",
    "\n\nI am happy to jump on a quick call if that helps.",
    "\n\nI would appreciate any pointers, even temporary workarounds.",
]

INTERNAL_NOTES = [
    "Followed runbook RB-{n:03d}, no luck so far.",
    "Escalating to Tier 2 — original error is reproducible on a clean profile.",
    "User confirmed they are on the latest patch level.",
    "Suspect this is the {tool} known issue tracked in JIRA-{n}.",
    "Cleared local cache and rebuilt search index, awaiting feedback.",
]

PUBLIC_REPLIES = [
    "Thanks for the report — could you share the exact error message?",
    "I have re-issued your credentials, please give it another try.",
    "We pushed a fix to your machine; please restart and let me know.",
    "I just confirmed the same issue on a test laptop. We are tracking it.",
    "Could you try the workaround in our knowledge base article KB-{n}?",
    "All good on my end now — happy to close this out unless you need more help.",
    "Thank you for your patience, the affected service is back online.",
]

CUSTOMER_REPLIES = [
    "Thanks, I will try that and get back to you.",
    "That worked, please go ahead and close the ticket.",
    "Still not working — same error message as before.",
    "Restarting did not help, the issue persists across sessions.",
    "Appreciate the quick response, this unblocks me for now.",
]


def _make_description(faker: Faker) -> str:
    """Build a multi-paragraph, realistic ticket description."""
    parts = [
        random.choice(DESCRIPTION_OPENERS),
        "",
        faker.paragraph(nb_sentences=random.randint(2, 4)),
        "",
        random.choice(DESCRIPTION_BODIES),
        random.choice(DESCRIPTION_CLOSERS),
    ]
    return "\n".join(parts)


def _make_title(category: TicketCategory, faker: Faker) -> str:
    """Pick a category-specific title and fill in placeholders."""
    template = random.choice(TICKET_TITLE_TEMPLATES[category])
    return template.format(
        app=random.choice(["Slack", "Teams", "Outlook", "Zoom", "Adobe Reader", "Excel"]),
        model=random.choice(["ThinkPad X1", "MacBook Pro 14", "Dell Latitude 7430", "Surface Pro"]),
        room=random.choice(["A-101", "B-204", "C-310", "D-512"]),
        name=faker.name(),
    )


def _make_comment_body(faker: Faker, *, internal: bool) -> str:
    """Build a realistic IT-support comment body."""
    pool = INTERNAL_NOTES if internal else (PUBLIC_REPLIES + CUSTOMER_REPLIES)
    template = random.choice(pool)
    return template.format(
        n=random.randint(100, 9999),
        tool=random.choice(["Outlook", "OneDrive", "Citrix", "Okta", "VPN"]),
    )


def _seed_users(db: Session, faker: Faker, *, count: int = 100) -> list[User]:
    """Insert ``count`` users, with the seeded admin first."""
    settings = get_settings()
    admin = User(
        email=settings.admin_email,
        full_name="Admin User",
        department="IT",
        role=UserRole.ADMIN,
        hashed_password=hash_password(settings.admin_password),
        is_active=True,
    )
    db.add(admin)

    users: list[User] = [admin]
    used_emails: set[str] = {admin.email.lower()}

    # Mix: ~10 admins (incl. seeded), ~25 agents, rest requesters.
    for i in range(count - 1):
        if i < 9:
            role = UserRole.ADMIN
        elif i < 34:
            role = UserRole.AGENT
        else:
            role = UserRole.REQUESTER

        full_name = faker.name()
        email = None
        for _ in range(5):
            candidate = faker.unique.email().lower()
            if candidate not in used_emails:
                email = candidate
                used_emails.add(candidate)
                break
        if email is None:
            # Fallback that is guaranteed unique.
            email = f"user{i + 2}@example.com"
            used_emails.add(email)

        user = User(
            email=email,
            full_name=full_name,
            department=random.choice(DEPARTMENTS),
            role=role,
            hashed_password=hash_password("password123"),
            is_active=True,
        )
        db.add(user)
        users.append(user)
    db.flush()
    return users


def _seed_tags(db: Session) -> list[Tag]:
    """Insert the canonical tag set."""
    tags = [Tag(name=name) for name in TAG_NAMES]
    db.add_all(tags)
    db.flush()
    return tags


def _seed_tickets(
    db: Session,
    faker: Faker,
    users: list[User],
    tags: list[Tag],
    *,
    count: int = 1_000,
) -> list[Ticket]:
    """Insert ``count`` tickets with sensible distributions."""
    requesters = [u for u in users if u.role == UserRole.REQUESTER]
    agents = [u for u in users if u.role in {UserRole.AGENT, UserRole.ADMIN}]

    statuses = list(TicketStatus)
    status_weights = [0.20, 0.25, 0.10, 0.25, 0.20]
    priorities = list(TicketPriority)
    priority_weights = [0.30, 0.40, 0.20, 0.10]
    categories = list(TicketCategory)

    now = datetime.now(timezone.utc)
    tickets: list[Ticket] = []
    for _ in range(count):
        category = random.choice(categories)
        priority = random.choices(priorities, weights=priority_weights, k=1)[0]
        status = random.choices(statuses, weights=status_weights, k=1)[0]

        created_at = now - timedelta(
            days=random.randint(0, 364),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )
        sla_hours = {
            TicketPriority.LOW: 72,
            TicketPriority.MEDIUM: 24,
            TicketPriority.HIGH: 8,
            TicketPriority.CRITICAL: 4,
        }[priority]
        sla_due = created_at + timedelta(hours=sla_hours)

        resolved_at: datetime | None = None
        if status in {TicketStatus.RESOLVED, TicketStatus.CLOSED}:
            resolved_at = created_at + timedelta(hours=random.randint(1, max(2, sla_hours * 2)))
            if resolved_at > now:
                resolved_at = now - timedelta(minutes=random.randint(5, 600))

        requester = random.choice(requesters)
        assignee = random.choice(agents) if status != TicketStatus.OPEN or random.random() < 0.5 else None

        ticket = Ticket(
            title=_make_title(category, faker),
            description=_make_description(faker),
            status=status,
            priority=priority,
            category=category,
            requester_id=requester.id,
            assignee_id=assignee.id if assignee else None,
            created_at=created_at,
            updated_at=created_at,
            resolved_at=resolved_at,
            sla_due_at=sla_due,
        )
        # Assign 0-3 tags to give the data some texture.
        ticket.tags = random.sample(tags, k=random.randint(0, min(3, len(tags))))
        db.add(ticket)
        tickets.append(ticket)
    db.flush()
    return tickets


def _seed_comments(
    db: Session,
    faker: Faker,
    tickets: list[Ticket],
    users: list[User],
) -> int:
    """Insert 1-10 comments per ticket. Returns the total inserted."""
    agents = [u for u in users if u.role in {UserRole.AGENT, UserRole.ADMIN}]
    total = 0
    for ticket in tickets:
        n_comments = random.randint(1, 10)
        for i in range(n_comments):
            internal = random.random() < 0.30
            if internal or i % 2 == 0:
                author = random.choice(agents)
            else:
                author = ticket.requester
            offset = timedelta(
                hours=random.randint(0, 240),
                minutes=random.randint(0, 59),
            )
            created_at = ticket.created_at + offset * (i + 1) / max(n_comments, 1)
            comment = Comment(
                ticket_id=ticket.id,
                author_id=author.id,
                body=_make_comment_body(faker, internal=internal),
                is_internal=internal,
                created_at=created_at,
            )
            db.add(comment)
            total += 1
    db.flush()
    return total


def _wipe(db: Session) -> None:
    """Remove existing data so seeding is idempotent."""
    from app.models.tag import ticket_tags

    db.execute(ticket_tags.delete())
    db.query(Comment).delete()
    db.query(Ticket).delete()
    db.query(Tag).delete()
    db.query(User).delete()
    db.commit()


def seed(*, ticket_count: int = 1_000, user_count: int = 100, seed_value: int = 42) -> dict[str, int]:
    """Run the full seeding workflow. Returns the inserted counts."""
    random.seed(seed_value)
    Faker.seed(seed_value)
    faker = Faker()

    init_db()

    db: Session = SessionLocal()
    try:
        logger.info("Wiping existing rows ...")
        _wipe(db)

        logger.info("Seeding %d users ...", user_count)
        users = _seed_users(db, faker, count=user_count)

        logger.info("Seeding %d tags ...", len(TAG_NAMES))
        tags = _seed_tags(db)

        logger.info("Seeding %d tickets ...", ticket_count)
        tickets = _seed_tickets(db, faker, users, tags, count=ticket_count)

        logger.info("Seeding comments ...")
        total_comments = _seed_comments(db, faker, tickets, users)

        db.commit()
        counts = {
            "users": len(users),
            "tags": len(tags),
            "tickets": len(tickets),
            "comments": total_comments,
        }
        logger.info(
            "Done. users=%d tags=%d tickets=%d comments=%d",
            counts["users"], counts["tags"], counts["tickets"], counts["comments"],
        )
        return counts
    finally:
        db.close()


if __name__ == "__main__":  # pragma: no cover - script entry point
    seed()
