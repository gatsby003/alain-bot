"""Repository layer with prepared SQL statements."""

from uuid import UUID

from .connection import Database
import json
from .models import (
    User,
    Conversation,
    Message,
    UserProfile,
    Pondering,
    OnboardingStatus,
    MessageRole,
    PonderingCategory,
)


class UserRepository:
    """User CRUD operations with prepared statements."""

    @classmethod
    async def get_by_telegram_id(cls, telegram_user_id: int) -> User | None:
        """Get user by Telegram user ID."""
        async with Database.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT * FROM "user" WHERE telegram_user_id = $1',
                telegram_user_id
            )
            return User.from_record(row) if row else None

    @classmethod
    async def create(
        cls,
        telegram_user_id: int,
        name: str | None = None,
        username: str | None = None,
    ) -> User:
        """Create a new user."""
        async with Database.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO "user" (telegram_user_id, name, username)
                VALUES ($1, $2, $3)
                RETURNING *
                """,
                telegram_user_id,
                name,
                username,
            )
            return User.from_record(row)

    @classmethod
    async def update_onboarding_status(
        cls, user_id: UUID, status: OnboardingStatus
    ) -> User | None:
        """Update user's onboarding status."""
        async with Database.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE "user" SET onboarding_status = $2
                WHERE id = $1
                RETURNING *
                """,
                user_id,
                status.value,
            )
            return User.from_record(row) if row else None

    @classmethod
    async def delete_all_data(cls, user_id: UUID) -> None:
        """Delete all data for a user (messages, ponderings, conversations, profile, user).
        
        Uses a transaction to ensure atomicity.
        """
        async with Database.transaction() as conn:
            # Delete messages (via conversations)
            await conn.execute(
                """
                DELETE FROM message
                WHERE conversation_id IN (
                    SELECT id FROM conversation WHERE user_id = $1
                )
                """,
                user_id,
            )
            # Delete ponderings
            await conn.execute(
                'DELETE FROM pondering WHERE user_id = $1',
                user_id,
            )
            # Delete conversations
            await conn.execute(
                'DELETE FROM conversation WHERE user_id = $1',
                user_id,
            )
            # Delete user profile
            await conn.execute(
                'DELETE FROM user_profile WHERE user_id = $1',
                user_id,
            )
            # Delete user
            await conn.execute(
                'DELETE FROM "user" WHERE id = $1',
                user_id,
            )


class ConversationRepository:
    """Conversation CRUD operations."""

    @classmethod
    async def get_by_telegram_chat_id(cls, telegram_chat_id: int) -> Conversation | None:
        """Get conversation by Telegram chat ID."""
        async with Database.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM conversation WHERE telegram_chat_id = $1",
                telegram_chat_id
            )
            return Conversation.from_record(row) if row else None

    @classmethod
    async def create(cls, telegram_chat_id: int, user_id: UUID) -> Conversation:
        """Create a new conversation."""
        async with Database.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO conversation (telegram_chat_id, user_id)
                VALUES ($1, $2)
                RETURNING *
                """,
                telegram_chat_id,
                user_id,
            )
            return Conversation.from_record(row)

    @classmethod
    async def get_or_create(cls, telegram_chat_id: int, user_id: UUID) -> Conversation:
        """Get existing conversation or create new one."""
        existing = await cls.get_by_telegram_chat_id(telegram_chat_id)
        if existing:
            return existing
        return await cls.create(telegram_chat_id, user_id)

    @classmethod
    async def update_last_message_at(cls, conversation_id: UUID) -> None:
        """Update the last_message_at timestamp."""
        async with Database.acquire() as conn:
            await conn.execute(
                """
                UPDATE conversation SET last_message_at = NOW()
                WHERE id = $1
                """,
                conversation_id,
            )


class MessageRepository:
    """Message CRUD operations."""

    @classmethod
    async def create(
        cls,
        conversation_id: UUID,
        role: MessageRole,
        content: str,
    ) -> Message:
        """Create a new message."""
        async with Database.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO message (conversation_id, role, content)
                VALUES ($1, $2, $3)
                RETURNING *
                """,
                conversation_id,
                role.value,
                content,
            )
            # Update conversation's last_message_at
            await ConversationRepository.update_last_message_at(conversation_id)
            return Message.from_record(row)

    @classmethod
    async def get_conversation_messages(
        cls,
        conversation_id: UUID,
        limit: int = 50,
    ) -> list[Message]:
        """Get messages for a conversation, ordered by sent_at."""
        async with Database.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM message
                WHERE conversation_id = $1
                ORDER BY sent_at ASC
                LIMIT $2
                """,
                conversation_id,
                limit,
            )
            return [Message.from_record(row) for row in rows]

    @classmethod
    async def get_unindexed_messages(cls, limit: int = 100) -> list[Message]:
        """Get messages that haven't been indexed for RAG."""
        async with Database.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM message
                WHERE indexed_at IS NULL
                ORDER BY sent_at ASC
                LIMIT $1
                """,
                limit,
            )
            return [Message.from_record(row) for row in rows]

    @classmethod
    async def mark_as_indexed(cls, message_ids: list[UUID]) -> None:
        """Mark messages as indexed."""
        async with Database.acquire() as conn:
            await conn.execute(
                """
                UPDATE message SET indexed_at = NOW()
                WHERE id = ANY($1)
                """,
                message_ids,
            )


class UserProfileRepository:
    """User profile CRUD operations."""

    @classmethod
    async def get_by_user_id(cls, user_id: UUID) -> UserProfile | None:
        """Get user profile by user ID."""
        async with Database.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM user_profile WHERE user_id = $1",
                user_id,
            )
            return UserProfile.from_record(row) if row else None

    @classmethod
    async def create(
        cls,
        user_id: UUID,
        daily_intentions: list[str],
        values: list[str],
        goals: list[str],
        raw_extraction: dict | None = None,
    ) -> UserProfile:
        """Create a new user profile."""
        async with Database.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO user_profile (user_id, daily_intentions, values, goals, raw_extraction)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING *
                """,
                user_id,
                json.dumps(daily_intentions),
                json.dumps(values),
                json.dumps(goals),
                json.dumps(raw_extraction) if raw_extraction else None,
            )
            return UserProfile.from_record(row)

    @classmethod
    async def update(
        cls,
        user_id: UUID,
        daily_intentions: list[str],
        values: list[str],
        goals: list[str],
        raw_extraction: dict | None = None,
    ) -> UserProfile | None:
        """Update an existing user profile."""
        async with Database.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE user_profile
                SET daily_intentions = $2, values = $3, goals = $4, raw_extraction = $5
                WHERE user_id = $1
                RETURNING *
                """,
                user_id,
                json.dumps(daily_intentions),
                json.dumps(values),
                json.dumps(goals),
                json.dumps(raw_extraction) if raw_extraction else None,
            )
            return UserProfile.from_record(row) if row else None

    @classmethod
    async def upsert(
        cls,
        user_id: UUID,
        daily_intentions: list[str],
        values: list[str],
        goals: list[str],
        raw_extraction: dict | None = None,
    ) -> UserProfile:
        """Create or update user profile."""
        async with Database.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO user_profile (user_id, daily_intentions, values, goals, raw_extraction)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (user_id) DO UPDATE SET
                    daily_intentions = EXCLUDED.daily_intentions,
                    values = EXCLUDED.values,
                    goals = EXCLUDED.goals,
                    raw_extraction = EXCLUDED.raw_extraction,
                    updated_at = NOW()
                RETURNING *
                """,
                user_id,
                json.dumps(daily_intentions),
                json.dumps(values),
                json.dumps(goals),
                json.dumps(raw_extraction) if raw_extraction else None,
            )
            return UserProfile.from_record(row)


class PonderingRepository:
    """Pondering CRUD operations for storing user thoughts/observations."""

    @classmethod
    async def create(
        cls,
        user_id: UUID,
        conversation_id: UUID,
        raw_content: str,
        cleaned_content: str | None,
        interpretation: str | None,
        category: PonderingCategory,
        is_valid: bool = True,
    ) -> Pondering:
        """Create a new pondering entry."""
        async with Database.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO pondering (user_id, conversation_id, raw_content, cleaned_content, interpretation, category, is_valid)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING *
                """,
                user_id,
                conversation_id,
                raw_content,
                cleaned_content,
                interpretation,
                category.value,
                is_valid,
            )
            return Pondering.from_record(row)

    @classmethod
    async def get_by_user_id(
        cls,
        user_id: UUID,
        valid_only: bool = True,
        limit: int = 100,
    ) -> list[Pondering]:
        """Get ponderings for a user, ordered by received_at."""
        async with Database.acquire() as conn:
            if valid_only:
                rows = await conn.fetch(
                    """
                    SELECT * FROM pondering
                    WHERE user_id = $1 AND is_valid = true
                    ORDER BY received_at DESC
                    LIMIT $2
                    """,
                    user_id,
                    limit,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT * FROM pondering
                    WHERE user_id = $1
                    ORDER BY received_at DESC
                    LIMIT $2
                    """,
                    user_id,
                    limit,
                )
            return [Pondering.from_record(row) for row in rows]

    @classmethod
    async def get_by_category(
        cls,
        user_id: UUID,
        category: PonderingCategory,
        limit: int = 50,
    ) -> list[Pondering]:
        """Get ponderings of a specific category for a user."""
        async with Database.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM pondering
                WHERE user_id = $1 AND category = $2 AND is_valid = true
                ORDER BY received_at DESC
                LIMIT $3
                """,
                user_id,
                category.value,
                limit,
            )
            return [Pondering.from_record(row) for row in rows]

