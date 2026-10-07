from pathlib import Path

from sqlalchemy import func, select

from app.core.database import build_engine, build_session_factory, init_models
from app.models import Contact, Conversation, ConversationMember, Message, User
from app.seed.seed_data import CONVERSATIONS, USERS, seed_if_empty


async def test_seed_is_idempotent_and_consistent(tmp_path: Path) -> None:
    engine = build_engine(f"sqlite+aiosqlite:///{tmp_path / 'seed.db'}")
    await init_models(engine)
    factory = build_session_factory(engine)

    assert await seed_if_empty(factory) is True
    assert await seed_if_empty(factory) is False

    async with factory() as session:
        assert await session.scalar(select(func.count()).select_from(User)) == len(USERS)
        assert await session.scalar(select(func.count()).select_from(Contact)) > 0
        conversations = (await session.scalars(select(Conversation))).all()
        assert len(conversations) == len(CONVERSATIONS)

        for conversation in conversations:
            max_seq = await session.scalar(
                select(func.max(Message.seq)).where(Message.conversation_id == conversation.id)
            )
            assert conversation.last_seq == max_seq

            last = await session.get(Message, conversation.last_message_id)
            assert last is not None
            assert last.seq == conversation.last_seq
            assert last.created_at == conversation.last_message_at

            cursors = await session.execute(
                select(
                    ConversationMember.last_delivered_seq, ConversationMember.last_read_seq
                ).where(ConversationMember.conversation_id == conversation.id)
            )
            for delivered, read in cursors.all():
                assert (
                    0 <= read <= delivered <= conversation.last_seq or read <= conversation.last_seq
                )

    await engine.dispose()
