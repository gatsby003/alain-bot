"""Pondering service - classifies and stores user thoughts/observations."""

import logging
from uuid import UUID

from ai_client import AIMessage, create_ai_client
from db import PonderingRepository
from db.models import Pondering, PonderingCategory
from prompts import PonderingResult, create_pondering_messages

logger = logging.getLogger(__name__)

# Model configuration
PONDERING_MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 768  # Increased for interpretation


class PonderingService:
    """Service for classifying and storing user ponderings."""

    def __init__(self):
        self.ai_client = create_ai_client("anthropic")

    async def process_message(
        self,
        user_id: UUID,
        conversation_id: UUID,
        message_text: str,
    ) -> Pondering | None:
        """Process and store a user message as a pondering.

        Args:
            user_id: The user's ID
            conversation_id: The conversation ID
            message_text: The raw message text

        Returns:
            The created Pondering if valid, None if classification failed
        """
        # 1. Create classification prompt
        prompt_messages = create_pondering_messages(message_text)
        ai_messages = [
            AIMessage(role=msg.role, content=msg.content)
            for msg in prompt_messages
        ]

        # 2. Call LLM for classification
        logger.info(f"Classifying pondering (user={user_id})")
        try:
            response = await self.ai_client.generate(
                messages=ai_messages,
                model=PONDERING_MODEL,
                max_tokens=MAX_TOKENS,
            )
        except Exception as e:
            logger.error(f"Failed to classify pondering: {e}")
            return None

        # 3. Parse response
        result = PonderingResult.parse(response.content)
        logger.info(
            f"Pondering classified: valid={result.is_valid}, "
            f"category={result.category}"
        )

        # 4. Map category string to enum
        category = PonderingCategory(result.category)

        # 5. Store in database
        pondering = await PonderingRepository.create(
            user_id=user_id,
            conversation_id=conversation_id,
            raw_content=message_text,
            cleaned_content=result.cleaned_content,
            interpretation=result.interpretation,
            category=category,
            is_valid=result.is_valid,
        )

        logger.info(
            f"Pondering stored: id={pondering.id}, valid={result.is_valid}, "
            f"has_interpretation={result.interpretation is not None}"
        )
        return pondering

