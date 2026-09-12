"""
Integration tests for Conversation, Message, and Outbox SQLAlchemy Repositories.
"""

from typing import AsyncGenerator
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.domain.conversation import Conversation, ConversationParticipant, ConversationType
from src.domain.message import DeliveryState, Message, MessageReference, MessageType
from src.infrastructure.database import Base
from src.infrastructure.repositories.conversation_repository import (
    ConversationNotFoundError,
    SQLAlchemyConversationRepository,
)
from src.infrastructure.repositories.message_repository import (
    MessageNotFoundError,
    SQLAlchemyMessageRepository,
)
from src.infrastructure.repositories.outbox_repository import SQLAlchemyOutboxRepository


@pytest_asyncio.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_conversation_repository_crud(async_session: AsyncSession) -> None:
    repo = SQLAlchemyConversationRepository(async_session)

    conv = Conversation(
        id="c1",
        title="Engineering Sync",
        conversation_type=ConversationType.TEAM,
        created_by_employee_id="emp-1",
        related_task_id="t100",
    )
    conv.add_participant(ConversationParticipant("emp-2", role="member"))

    saved = await repo.save(conv)
    assert saved.id == "c1"
    assert len(saved.participants) == 2

    fetched = await repo.get_by_id("c1")
    assert fetched.title == "Engineering Sync"
    assert fetched.has_participant("emp-2")

    by_task = await repo.get_by_task_id("t100")
    assert len(by_task) == 1
    assert by_task[0].id == "c1"

    await repo.delete("c1")
    with pytest.raises(ConversationNotFoundError):
        await repo.get_by_id("c1")


@pytest.mark.asyncio
async def test_message_repository_crud(async_session: AsyncSession) -> None:
    conv_repo = SQLAlchemyConversationRepository(async_session)
    msg_repo = SQLAlchemyMessageRepository(async_session)

    conv = Conversation(id="c2", title="Task Discussion", created_by_employee_id="emp-1")
    await conv_repo.save(conv)

    msg = Message(
        id="m1",
        conversation_id="c2",
        sender_employee_id="emp-1",
        message_type=MessageType.BLOCKER,
        subject="Blocked on API credentials",
        content="Missing AWS secret keys",
    )
    msg.add_reference(MessageReference("task", "t100"))

    saved = await msg_repo.save(msg)
    assert saved.id == "m1"
    assert saved.delivery_state == DeliveryState.CREATED

    fetched = await msg_repo.get_by_id("m1")
    assert fetched.subject == "Blocked on API credentials"
    assert len(fetched.references) == 1

    by_conv = await msg_repo.get_by_conversation_id("c2")
    assert len(by_conv) == 1

    msg.acknowledge("mgr-1")
    await msg_repo.save(msg)

    updated = await msg_repo.get_by_id("m1")
    assert updated.delivery_state == DeliveryState.ACKNOWLEDGED
    assert "mgr-1" in updated.acknowledgements


@pytest.mark.asyncio
async def test_outbox_repository_flow(async_session: AsyncSession) -> None:
    outbox_repo = SQLAlchemyOutboxRepository(async_session)

    item = await outbox_repo.create_outbox_message(
        event_type="MessageCreated", payload_json='{"message_id": "m1"}'
    )
    assert item.status == "PENDING"

    pending = await outbox_repo.get_pending_messages()
    assert len(pending) == 1
    assert pending[0].event_type == "MessageCreated"

    await outbox_repo.mark_processed(item.id)
    pending_after = await outbox_repo.get_pending_messages()
    assert len(pending_after) == 0
