"""Handler for /reset command - delete all user data for testing."""

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from db import UserRepository


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /reset command - delete all user data and reset state."""
    if not update.effective_user or not update.message:
        return

    telegram_user_id = update.effective_user.id

    # Check if user exists
    user = await UserRepository.get_by_telegram_id(telegram_user_id)

    if user is None:
        await update.message.reply_text("No data found for your account. Nothing to reset.")
        return

    # Delete all user data
    await UserRepository.delete_all_data(user.id)

    await update.message.reply_text(
        "🔄 All your data has been deleted.\n\n"
        "Use /start to begin fresh!"
    )


# Export the handler
reset_handler = CommandHandler("reset", reset)

