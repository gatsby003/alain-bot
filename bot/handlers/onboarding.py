"""Handler for messages during and after onboarding."""

import logging

from telegram import Update
from telegram.ext import MessageHandler, ContextTypes, filters

from db import UserRepository, ConversationRepository, MessageRepository
from db.models import MessageRole, OnboardingStatus
from services import OnboardingService, PonderingService


logger = logging.getLogger(__name__)

# Completion message sent when onboarding finishes
ONBOARDING_COMPLETE_MESSAGE = (
    "\n\n✨ Got it! I've captured your intentions and what drives you.\n\n"
    "This chat is now your pondering space — drop any thought, observation, "
    "or feeling here, whether it's about your goals or just what's on your mind. "
    "The more you share, the better I understand you and can help you move forward."
)

# Lazy-initialized services
_onboarding_service: OnboardingService | None = None
_pondering_service: PonderingService | None = None


def get_onboarding_service() -> OnboardingService:
    """Get or create the onboarding service singleton."""
    global _onboarding_service
    if _onboarding_service is None:
        _onboarding_service = OnboardingService()
    return _onboarding_service


def get_pondering_service() -> PonderingService:
    """Get or create the pondering service singleton."""
    global _pondering_service
    if _pondering_service is None:
        _pondering_service = PonderingService()
    return _pondering_service


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages.

    Routes to:
    - Onboarding flow if user is in STARTED status
    - Echo behavior if user has COMPLETED onboarding
    """
    if not update.message or not update.message.text:
        return

    if not update.effective_user or not update.effective_chat:
        return

    telegram_user_id = update.effective_user.id
    telegram_chat_id = update.effective_chat.id

    # Get user (should exist if they used /start)
    user = await UserRepository.get_by_telegram_id(telegram_user_id)

    if user is None:
        # User hasn't started - prompt them
        await update.message.reply_text("Please use /start to begin!")
        return

    # Get or create conversation
    conversation = await ConversationRepository.get_or_create(
        telegram_chat_id=telegram_chat_id,
        user_id=user.id,
    )

    # Route based on onboarding status
    if user.onboarding_status == OnboardingStatus.STARTED:
        # Active onboarding - use LLM
        await _handle_onboarding_message(update, user, conversation)

    elif user.onboarding_status == OnboardingStatus.COMPLETED:
        # Post-onboarding - process as pondering
        await _handle_pondering_message(update, user, conversation)

    else:
        # PENDING status - shouldn't happen, but handle gracefully
        await update.message.reply_text(
            "Please use /start to begin your onboarding!"
        )


async def _handle_onboarding_message(
    update: Update,
    user,
    conversation,
) -> None:
    """Handle message during active onboarding."""
    service = get_onboarding_service()

    # Check status before calling service to detect completion
    was_started = user.onboarding_status == OnboardingStatus.STARTED

    # Get LLM response
    response_text = await service.handle_message(
        user=user,
        conversation=conversation,
        message_text=update.message.text,
    )

    # Check if onboarding just completed
    # Re-fetch user to see updated status
    updated_user = await UserRepository.get_by_telegram_id(user.telegram_user_id)

    if was_started and updated_user and updated_user.onboarding_status == OnboardingStatus.COMPLETED:
        # Add completion notification
        response_text += ONBOARDING_COMPLETE_MESSAGE
        logger.info(f"Onboarding completed for user {user.id}")

    await update.message.reply_text(response_text)


async def _handle_pondering_message(
    update: Update,
    user,
    conversation,
) -> None:
    """Handle message after onboarding - classify and store as pondering."""
    message_text = update.message.text
    service = get_pondering_service()

    # Store user's message in conversation
    await MessageRepository.create(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=message_text,
    )

    # Process through pondering service (classify + store)
    pondering = await service.process_message(
        user_id=user.id,
        conversation_id=conversation.id,
        message_text=message_text,
    )

    # Generate response based on classification
    if pondering and pondering.is_valid:
        category_emoji = {
            "thought": "💭",
            "observation": "👁️",
            "feeling": "💫",
        }
        emoji = category_emoji.get(pondering.category.value, "✨")
        response = f"{emoji} Noted."
    else:
        response = "Got it."

    await update.message.reply_text(response)

    # Store bot's response
    await MessageRepository.create(
        conversation_id=conversation.id,
        role=MessageRole.ASSISTANT,
        content=response,
    )


# Export the handler - handles all text messages except commands
message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)

