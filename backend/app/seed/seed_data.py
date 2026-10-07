"""Idempotent demo data: users, contacts, DMs and groups with realistic receipt cursors.

Run manually:  python -m app.seed.seed_data
The app also runs `seed_if_empty` on startup when SEED_ON_STARTUP=true.
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import get_settings
from app.core.database import build_engine, build_session_factory, init_models
from app.models import Contact, Conversation, ConversationMember, Message, User
from app.models.enums import ConversationType, MemberRole, MessageType
from app.utils.avatar import avatar_color_for
from app.utils.ids import direct_key
from app.utils.time import now_ms

logger = logging.getLogger(__name__)

MINUTE_MS = 60_000
DAY_MS = 24 * 60 * MINUTE_MS
NAMESPACE = uuid.UUID("6f1f5c1e-5a53-4f0e-9d0b-2a7a6d2f1c11")


def _sid(*parts: str) -> str:
    return str(uuid.uuid5(NAMESPACE, ":".join(parts)))


@dataclass(frozen=True)
class SeedUser:
    key: str
    phone: str
    name: str
    username: str
    about: str | None
    last_seen_minutes_ago: int | None


@dataclass(frozen=True)
class SeedMessage:
    sender: str
    body: str
    minutes_ago: int


@dataclass(frozen=True)
class SeedConversation:
    key: str
    kind: ConversationType
    members: tuple[str, ...]
    messages: tuple[SeedMessage, ...]
    name: str | None = None
    description: str | None = None
    creator: str | None = None
    admins: tuple[str, ...] = ()
    # Per-member cursor overrides. Members not listed are fully delivered and read.
    read_seq: dict[str, int] = field(default_factory=dict)
    delivered_seq: dict[str, int] = field(default_factory=dict)


USERS = (
    SeedUser("alice", "+15550000001", "Alice Johnson", "alice.01", "Hiking, coffee, code", 0),
    SeedUser("bob", "+15550000002", "Bob Smith", "bob.02", "Busy", 2),
    SeedUser("carol", "+15550000003", "Carol Diaz", "carol.03", "Speak Freely", 15),
    SeedUser("dave", "+15550000004", "Dave Patel", "dave.04", None, 180),
    SeedUser("erin", "+15550000005", "Erin Walsh", "erin.05", "At the gym", 1440),
    SeedUser("frank", "+15550000006", "Frank Müller", "frank.06", "Available", 5),
    SeedUser("grace", "+15550000007", "Grace Lee", "grace.07", "Speak Freely", 60),
    SeedUser("heidi", "+15550000008", "Heidi Novak", "heidi.08", None, 600),
)

CONTACTS: dict[str, tuple[str, ...]] = {
    "alice": ("bob", "carol", "dave", "erin", "frank"),
    "bob": ("alice", "carol", "dave"),
    "carol": ("alice", "bob"),
    "dave": ("alice", "bob"),
    "erin": ("alice",),
    "frank": ("alice",),
}

D = ConversationType.DIRECT
G = ConversationType.GROUP

CONVERSATIONS = (
    SeedConversation(
        key="alice-bob",
        kind=D,
        members=("alice", "bob"),
        messages=(
            SeedMessage("bob", "Hey Alice! Are we still on for Saturday?", 1500),
            SeedMessage("alice", "Yes! I booked the trailhead parking already.", 1490),
            SeedMessage("bob", "Perfect. I'll bring the thermos.", 1485),
            SeedMessage("alice", "Don't forget the map this time 😄", 1480),
            SeedMessage("bob", "Ha, noted.", 1478),
            SeedMessage("bob", "Also, did you see the Signal blog post about usernames?", 35),
            SeedMessage("alice", "Not yet, link?", 30),
            SeedMessage("bob", "Sending it over in a sec.", 28),
        ),
    ),
    SeedConversation(
        key="alice-carol",
        kind=D,
        members=("alice", "carol"),
        messages=(
            SeedMessage("alice", "Did you get the slides for Monday?", 600),
            SeedMessage("carol", "Yes, reviewing them now.", 590),
            SeedMessage("carol", "Slide 12 has a typo in the title.", 58),
            SeedMessage("carol", "Also can we move the sync to 3pm?", 57),
            SeedMessage("carol", "Let me know 🙏", 56),
        ),
        # Alice has read up to Carol's first reply: 3 unread.
        read_seq={"alice": 2},
    ),
    SeedConversation(
        key="alice-dave",
        kind=D,
        members=("alice", "dave"),
        messages=(
            SeedMessage("dave", "Thanks for the book recommendation!", 3000),
            SeedMessage("alice", "Anytime! Let me know what you think.", 2990),
            SeedMessage("alice", "By the way, are you joining the hike?", 120),
        ),
        # Dave's device has it (delivered) but he hasn't opened the chat (not read).
        read_seq={"dave": 2},
    ),
    SeedConversation(
        key="alice-erin",
        kind=D,
        members=("alice", "erin"),
        messages=(
            SeedMessage("alice", "Hi Erin, welcome to the team!", 300),
            SeedMessage("alice", "Ping me if you need anything.", 299),
        ),
        # Erin's device never connected: Alice's messages stay "sent".
        read_seq={"erin": 0},
        delivered_seq={"erin": 0},
    ),
    SeedConversation(
        key="bob-carol",
        kind=D,
        members=("bob", "carol"),
        messages=(
            SeedMessage("bob", "Lunch tomorrow?", 200),
            SeedMessage("carol", "Sure, the usual place.", 195),
            SeedMessage("bob", "12:30 works for me.", 190),
        ),
    ),
    SeedConversation(
        key="weekend-hikers",
        kind=G,
        name="Weekend Hikers",
        description="Trails, snacks, and sunrise starts.",
        creator="alice",
        admins=("alice",),
        members=("alice", "bob", "carol", "dave"),
        messages=(
            SeedMessage("alice", "Welcome to the Weekend Hikers! 🥾", 4000),
            SeedMessage("bob", "Glad to be here!", 3990),
            SeedMessage("carol", "What's the plan for this weekend?", 3980),
            SeedMessage("alice", "Meeting at 7am at the north trailhead.", 3970),
            SeedMessage("dave", "I'll carpool with Bob.", 3960),
            SeedMessage("carol", "Weather looks great for Saturday ☀️", 50),
            SeedMessage("bob", "Bring layers, it gets cold up top.", 48),
            SeedMessage("dave", "See you all at 7!", 20),
        ),
        # seq 1 is the system message; Alice read through seq 6 (dave's carpool line).
        read_seq={"alice": 6},
    ),
    SeedConversation(
        key="project-phoenix",
        kind=G,
        name="Project Phoenix",
        description="Planning and updates.",
        creator="bob",
        admins=("bob",),
        members=("bob", "alice", "erin", "frank"),
        messages=(
            SeedMessage("bob", "Kicking off Project Phoenix. Goals are in the doc.", 9000),
            SeedMessage("erin", "Thanks Bob, reading it now.", 8990),
            SeedMessage("frank", "Do we have a deadline yet?", 8980),
            SeedMessage("bob", "Target is end of next month.", 8970),
            SeedMessage("alice", "I'll draft the API plan by Friday.", 8960),
            SeedMessage("erin", "Sounds good 👍", 8950),
        ),
    ),
)


def _pick(overrides: dict[str, int], key: str, default: int) -> int:
    value = overrides.get(key)
    return default if value is None else value


async def _seed_users(session: AsyncSession, now: int) -> dict[str, User]:
    users: dict[str, User] = {}
    for seed in USERS:
        user_id = _sid("user", seed.phone)
        last_seen = (
            None
            if seed.last_seen_minutes_ago is None
            else now - seed.last_seen_minutes_ago * MINUTE_MS
        )
        users[seed.key] = User(
            id=user_id,
            phone_number=seed.phone,
            username=seed.username,
            display_name=seed.name,
            about=seed.about,
            avatar_color=avatar_color_for(user_id),
            last_seen_at=last_seen,
            created_at=now - 30 * DAY_MS,
        )
    session.add_all(users.values())
    await session.flush()
    return users


async def _seed_contacts(session: AsyncSession, users: dict[str, User], now: int) -> None:
    for owner_key, contact_keys in CONTACTS.items():
        for contact_key in contact_keys:
            owner, contact = users[owner_key], users[contact_key]
            session.add(
                Contact(
                    id=_sid("contact", owner.id, contact.id),
                    owner_id=owner.id,
                    contact_user_id=contact.id,
                    created_at=now - 29 * DAY_MS,
                )
            )
    await session.flush()


async def _seed_conversation(
    session: AsyncSession, spec: SeedConversation, users: dict[str, User], now: int
) -> None:
    is_group = spec.kind is ConversationType.GROUP
    member_ids = [users[key].id for key in spec.members]
    creator = users[spec.creator or spec.members[0]]
    oldest_minutes = max(m.minutes_ago for m in spec.messages)
    created_at = now - (oldest_minutes + 5) * MINUTE_MS

    conversation = Conversation(
        id=_sid("conversation", spec.key),
        type=spec.kind.value,
        direct_key=None if is_group else direct_key(member_ids[0], member_ids[1]),
        name=spec.name,
        description=spec.description,
        created_by=creator.id,
        last_seq=0,
        last_message_at=created_at,
        created_at=created_at,
    )
    session.add(conversation)
    await session.flush()

    members = [
        ConversationMember(
            conversation_id=conversation.id,
            user_id=users[key].id,
            role=(MemberRole.ADMIN if key in spec.admins else MemberRole.MEMBER).value,
            joined_at=created_at,
        )
        for key in spec.members
    ]
    session.add_all(members)
    await session.flush()

    seq = 0
    last_message: Message | None = None

    if is_group:
        seq += 1
        last_message = Message(
            id=_sid("message", spec.key, str(seq)),
            conversation_id=conversation.id,
            seq=seq,
            sender_id=None,
            type=MessageType.SYSTEM.value,
            body=json.dumps({"event": "group_created", "actor": creator.id}),
            created_at=created_at,
        )
        session.add(last_message)

    for item in spec.messages:
        seq += 1
        last_message = Message(
            id=_sid("message", spec.key, str(seq)),
            conversation_id=conversation.id,
            seq=seq,
            sender_id=users[item.sender].id,
            type=MessageType.TEXT.value,
            body=item.body,
            created_at=now - item.minutes_ago * MINUTE_MS,
        )
        session.add(last_message)
    await session.flush()

    assert last_message is not None
    conversation.last_seq = seq
    conversation.last_message_id = last_message.id
    conversation.last_message_at = last_message.created_at

    for key, member in zip(spec.members, members, strict=True):
        member.last_delivered_seq = _pick(spec.delivered_seq, key, seq)
        member.last_read_seq = _pick(spec.read_seq, key, seq)
    await session.flush()


async def seed_database(session: AsyncSession) -> None:
    now = now_ms()
    users = await _seed_users(session, now)
    await _seed_contacts(session, users, now)
    for spec in CONVERSATIONS:
        await _seed_conversation(session, spec, users, now)


async def seed_if_empty(session_factory: async_sessionmaker[AsyncSession]) -> bool:
    """Seed only when the users table is empty. Returns True if data was inserted."""
    async with session_factory() as session:
        user_count = await session.scalar(select(func.count()).select_from(User))
        if user_count:
            logger.info("Seed skipped: database already has %s users", user_count)
            return False
        await seed_database(session)
        await session.commit()
        logger.info("Seed complete: %s users, %s conversations", len(USERS), len(CONVERSATIONS))
        return True


async def _main() -> None:
    engine = build_engine(get_settings().database_url)
    await init_models(engine)
    seeded = await seed_if_empty(build_session_factory(engine))
    await engine.dispose()
    print("Seeded demo data." if seeded else "Database already has users; nothing to do.")


if __name__ == "__main__":
    asyncio.run(_main())
