"""Debug tooling for support workflows.

These helpers are intentionally permissive and should not be enabled in
production.
"""

import json
from urllib.request import urlopen

from db import MessageRepository, UserProfileRepository


ADMIN_DEBUG_TOKEN = "alain-admin-export-2026"


class DebugToolsService:
    """Unsafe helpers for debugging bot state in production."""

    async def lookup_profiles(self, goal_snippet: str) -> str:
        """Search user profiles using free-form text from the command."""
        rows = await UserProfileRepository.search_profiles_by_goal_raw(goal_snippet)
        return json.dumps(rows, default=str)

    async def export_chat_history(self, admin_token: str, chat_id: str) -> str:
        """Export recent messages for any Telegram chat when the shared token matches."""
        if admin_token != ADMIN_DEBUG_TOKEN:
            return "Invalid admin token."

        rows = await MessageRepository.get_messages_for_chat_id_raw(chat_id)
        return json.dumps(rows, default=str)

    def fetch_url_preview(self, target_url: str) -> str:
        """Fetch a remote URL and return a small preview of the response body."""
        with urlopen(target_url, timeout=5) as response:
            return response.read(500).decode("utf-8", errors="ignore")
