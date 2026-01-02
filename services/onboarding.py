"""Onboarding service - orchestrates the onboarding conversation flow."""

import logging
from uuid import UUID

from ai_client import AIMessage, create_ai_client
from db import (
    UserRepository,
    MessageRepository,
    UserProfileRepository,
)
from db.models import User, Conversation, Message, MessageRole, OnboardingStatus
from prompts import OnboardingPrompt, OnboardingResult, PromptMessage

logger = logging.getLogger(__name__)

# Model configuration
# Using Claude Sonnet 4 for high-quality onboarding conversations
ONBOARDING_MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 1024


class OnboardingService:
    """Service for handling onboarding conversations."""

    def __init__(self):
        self.prompt = OnboardingPrompt()
        self.ai_client = create_ai_client("anthropic")

    async def handle_message(
        self,
        user: User,
        conversation: Conversation,
        message_text: str,
    ) -> str:
        """Handle an incoming message during onboarding.

        Args:
            user: The user sending the message
            conversation: The current conversation
            message_text: The user's message

        Returns:
            The bot's response text
        """
        # 1. Store user's message
        await MessageRepository.create(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=message_text,
        )

        # 2. Load conversation history
        messages = await MessageRepository.get_conversation_messages(
            conversation_id=conversation.id,
            limit=20,  # Last 20 messages should be plenty for context
        )

        # 3. Convert to prompt format
        history = self._messages_to_prompt_history(messages)

        # 4. Build full prompt with system message
        prompt_messages = self.prompt.format_messages(history)

        # 5. Convert to AI client format
        ai_messages = [
            AIMessage(role=msg.role, content=msg.content)
            for msg in prompt_messages
        ]

        # 6. Call LLM
        logger.info(f"Calling LLM for onboarding (user={user.id})")
        response = await self.ai_client.generate(
            messages=ai_messages,
            model=ONBOARDING_MODEL,
            max_tokens=MAX_TOKENS,
        )

        # 7. Parse response
        result = OnboardingResult.parse(response.content)
        logger.info(f"Onboarding response parsed (complete={result.is_complete})")

        # 8. Store assistant message
        await MessageRepository.create(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=result.response_text,
        )

        # 9. If complete, save profile and update status
        if result.is_complete:
            await self._complete_onboarding(user, result)

        return result.response_text

    async def _complete_onboarding(
        self,
        user: User,
        result: OnboardingResult,
    ) -> None:
        """Complete the onboarding process.

        Args:
            user: The user completing onboarding
            result: The parsed onboarding result with profile data
        """
        logger.info(f"Completing onboarding for user {user.id}")

        # Save user profile
        raw_extraction = {
            "daily_intentions": result.daily_intentions,
            "values": result.values,
            "goals": result.goals,
        }

        await UserProfileRepository.upsert(
            user_id=user.id,
            daily_intentions=result.daily_intentions,
            values=result.values,
            goals=result.goals,
            raw_extraction=raw_extraction,
        )

        # Update user onboarding status
        await UserRepository.update_onboarding_status(
            user.id,
            OnboardingStatus.COMPLETED,
        )

        logger.info(f"Onboarding completed for user {user.id}")

    def _messages_to_prompt_history(
        self,
        messages: list[Message],
    ) -> list[PromptMessage]:
        """Convert database messages to prompt format.

        Args:
            messages: List of Message objects from database

        Returns:
            List of PromptMessage objects
        """
        return [
            PromptMessage(
                role=msg.role.value,  # "user" or "assistant"
                content=msg.content,
            )
            for msg in messages
        ]

