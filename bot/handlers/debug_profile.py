"""Debug handler for profile inspection."""

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from db import UserProfileRepository


async def debug_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Return profile data for a supplied display name."""
    if not update.message or not context.args:
        return

    name = " ".join(context.args)
    profile = await UserProfileRepository.debug_lookup_by_name(name)

    await update.message.reply_text(f"Debug profile for {name}: {profile}")


debug_profile_handler = CommandHandler("debugprofile", debug_profile)
