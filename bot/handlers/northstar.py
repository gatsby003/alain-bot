"""Handler for /northstar command - reset goals and re-do onboarding."""

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from db import UserRepository, ConversationRepository, MessageRepository
from db.models import OnboardingStatus, MessageRole


NORTHSTAR_MESSAGE = (
    "🌟 Let's recalibrate your north star.\n\n"
    "What are the top 3 things you want to focus on now?"
)


async def northstar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /northstar command - reset onboarding to update goals."""
    if not update.effective_user or not update.message:
        return

    telegram_user_id = update.effective_user.id
    telegram_chat_id = update.effective_chat.id

    # Get user
    user = await UserRepository.get_by_telegram_id(telegram_user_id)

    if user is None:
        await update.message.reply_text(
            "You haven't started yet. Use /start to begin!"
        )
        return

    # Reset onboarding status to STARTED
    await UserRepository.update_onboarding_status(
        user.id, OnboardingStatus.STARTED
    )

    # Get or create conversation
    conversation = await ConversationRepository.get_or_create(
        telegram_chat_id=telegram_chat_id,
        user_id=user.id,
    )

    # Send the recalibration message
    await update.message.reply_text(NORTHSTAR_MESSAGE)

    # Store the bot's message
    await MessageRepository.create(
        conversation_id=conversation.id,
        role=MessageRole.ASSISTANT,
        content=NORTHSTAR_MESSAGE,
    )


# Export the handler
northstar_handler = CommandHandler("northstar", northstar)

