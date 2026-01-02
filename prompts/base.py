"""Base prompt abstractions."""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class PromptMessage:
    """A message in a prompt conversation."""

    role: str  # "system", "user", "assistant"
    content: str


class BasePrompt(ABC):
    """Abstract base class for prompt templates."""

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Return the system prompt."""
        ...

    @abstractmethod
    def format_messages(self, history: list[PromptMessage]) -> list[PromptMessage]:
        """Format conversation history into prompt messages."""
        ...


def extract_tag(text: str, tag: str) -> str | None:
    """Extract content from an XML tag.

    Args:
        text: The text to search
        tag: The tag name (without angle brackets)

    Returns:
        The content inside the tag, or None if not found
    """
    pattern = rf"<{tag}>(.*?)</{tag}>"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else None


def extract_list(text: str, parent_tag: str, item_tag: str) -> list[str]:
    """Extract a list of items from nested XML tags.

    Args:
        text: The text to search
        parent_tag: The parent tag containing the list
        item_tag: The tag for each item in the list

    Returns:
        List of extracted item contents
    """
    parent_content = extract_tag(text, parent_tag)
    if not parent_content:
        return []
    pattern = rf"<{item_tag}>(.*?)</{item_tag}>"
    return [m.group(1).strip() for m in re.finditer(pattern, parent_content, re.DOTALL)]

