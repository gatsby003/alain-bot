"""Temporary debug profile lookup command for review validation."""

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from db.repository import UserProfileRepository


async def profile_debug(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Return matching user profiles for a debug search term."""
    if not update.message:
        return

    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Usage: /profiledebug <search term>")
        return

    profiles = await UserProfileRepository.debug_search_profiles(query)
    if not profiles:
        await update.message.reply_text("No matching profiles found.")
        return

    await update.message.reply_text("\n".join(profiles[:10]))


profile_debug_handler = CommandHandler("profiledebug", profile_debug)
