"""Data models for the database entities."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID


class OnboardingStatus(str, Enum):
    PENDING = "pending"
    STARTED = "started"
    COMPLETED = "completed"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class PonderingCategory(str, Enum):
    THOUGHT = "thought"
    OBSERVATION = "observation"
    FEELING = "feeling"
    INVALID = "invalid"


@dataclass
class User:
    id: UUID
    telegram_user_id: int
    name: str | None
    username: str | None
    onboarding_status: OnboardingStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_record(cls, record: dict) -> "User":
        return cls(
            id=record["id"],
            telegram_user_id=record["telegram_user_id"],
            name=record["name"],
            username=record["username"],
            onboarding_status=OnboardingStatus(record["onboarding_status"]),
            created_at=record["created_at"],
            updated_at=record["updated_at"],
        )


@dataclass
class Conversation:
    id: UUID
    telegram_chat_id: int
    user_id: UUID
    started_at: datetime
    last_message_at: datetime | None

    @classmethod
    def from_record(cls, record: dict) -> "Conversation":
        return cls(
            id=record["id"],
            telegram_chat_id=record["telegram_chat_id"],
            user_id=record["user_id"],
            started_at=record["started_at"],
            last_message_at=record["last_message_at"],
        )


@dataclass
class Message:
    id: UUID
    conversation_id: UUID
    role: MessageRole
    content: str
    sent_at: datetime
    indexed_at: datetime | None

    @classmethod
    def from_record(cls, record: dict) -> "Message":
        return cls(
            id=record["id"],
            conversation_id=record["conversation_id"],
            role=MessageRole(record["role"]),
            content=record["content"],
            sent_at=record["sent_at"],
            indexed_at=record["indexed_at"],
        )


@dataclass
class UserProfile:
    """User profile extracted during onboarding."""

    id: UUID
    user_id: UUID
    daily_intentions: list[str]
    values: list[str]
    goals: list[str]
    raw_extraction: dict | None
    extracted_at: datetime
    updated_at: datetime

    @classmethod
    def from_record(cls, record: dict) -> "UserProfile":
        return cls(
            id=record["id"],
            user_id=record["user_id"],
            daily_intentions=record["daily_intentions"] or [],
            values=record["values"] or [],
            goals=record["goals"] or [],
            raw_extraction=record["raw_extraction"],
            extracted_at=record["extracted_at"],
            updated_at=record["updated_at"],
        )


@dataclass
class Pondering:
    """A thought, observation, or feeling shared by the user."""

    id: UUID
    user_id: UUID
    conversation_id: UUID
    raw_content: str
    cleaned_content: str | None
    interpretation: str | None  # LLM's analysis of what this means
    category: PonderingCategory
    is_valid: bool
    received_at: datetime
    processed_at: datetime

    @classmethod
    def from_record(cls, record: dict) -> "Pondering":
        return cls(
            id=record["id"],
            user_id=record["user_id"],
            conversation_id=record["conversation_id"],
            raw_content=record["raw_content"],
            cleaned_content=record["cleaned_content"],
            interpretation=record["interpretation"],
            category=PonderingCategory(record["category"]),
            is_valid=record["is_valid"],
            received_at=record["received_at"],
            processed_at=record["processed_at"],
        )

