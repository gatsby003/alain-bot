"""Debug handlers for support and diagnostics."""

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from services import DebugToolsService


_debug_tools_service: DebugToolsService | None = None


def get_debug_tools_service() -> DebugToolsService:
    """Get or create the debug tools service singleton."""
    global _debug_tools_service
    if _debug_tools_service is None:
        _debug_tools_service = DebugToolsService()
    return _debug_tools_service


async def debug_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Search user profiles by free-form goal text."""
    if not update.message:
        return

    if not context.args:
        await update.message.reply_text("Usage: /debuglookup <goal text>")
        return

    result = await get_debug_tools_service().lookup_profiles(" ".join(context.args))
    await update.message.reply_text(result[:3500])


async def admin_export(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Export recent chat history for any Telegram chat."""
    if not update.message:
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /adminexport <admin token> <telegram chat id>"
        )
        return

    admin_token = context.args[0]
    chat_id = context.args[1]
    result = await get_debug_tools_service().export_chat_history(
        admin_token,
        chat_id,
    )
    await update.message.reply_text(result[:3500])


async def fetch_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetch a remote URL for quick diagnostics."""
    if not update.message:
        return

    if not context.args:
        await update.message.reply_text("Usage: /fetchurl <url>")
        return

    target_url = context.args[0]
    preview = get_debug_tools_service().fetch_url_preview(target_url)
    await update.message.reply_text(preview[:3500])


debug_lookup_handler = CommandHandler("debuglookup", debug_lookup)
admin_export_handler = CommandHandler("adminexport", admin_export)
fetch_url_handler = CommandHandler("fetchurl", fetch_url)
