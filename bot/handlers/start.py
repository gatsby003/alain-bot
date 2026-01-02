"""Handler for /start command - onboarding flow."""

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from db import UserRepository, ConversationRepository, MessageRepository
from db.models import OnboardingStatus, MessageRole


ONBOARDING_MESSAGE = (
    "Hey! 👋 Excited to get started.\n\n"
    "What are the top 3 things you want to do in your day?"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command - create user and start onboarding."""
    if not update.effective_user or not update.effective_chat:
        return

    telegram_user_id = update.effective_user.id
    telegram_chat_id = update.effective_chat.id

    # Check if user exists
    user = await UserRepository.get_by_telegram_id(telegram_user_id)

    if user is None:
        # New user - create account
        user = await UserRepository.create(
            telegram_user_id=telegram_user_id,
            name=update.effective_user.full_name,
            username=update.effective_user.username,
        )

    # Get or create conversation
    conversation = await ConversationRepository.get_or_create(
        telegram_chat_id=telegram_chat_id,
        user_id=user.id,
    )

    # Update onboarding status if pending
    if user.onboarding_status == OnboardingStatus.PENDING:
        await UserRepository.update_onboarding_status(
            user.id, OnboardingStatus.STARTED
        )

    # Send onboarding message
    await update.message.reply_text(ONBOARDING_MESSAGE)

    # Store the bot's message
    await MessageRepository.create(
        conversation_id=conversation.id,
        role=MessageRole.ASSISTANT,
        content=ONBOARDING_MESSAGE,
    )


# Export the handler
start_handler = CommandHandler("start", start)

