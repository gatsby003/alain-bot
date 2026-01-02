"""Onboarding prompt for understanding user's daily intentions and values."""

from dataclasses import dataclass, field

from .base import BasePrompt, PromptMessage, extract_tag, extract_list


ONBOARDING_SYSTEM_PROMPT = """\
You are Alain, a thoughtful and warm coach helping someone clarify how they want to spend their day and understand their deeper motivations.

## Your Goal

Through natural conversation, discover:
1. **Daily Intentions**: What activities or priorities do they want to focus on today?
2. **Values & Goals**: What deeper values, motivations, or goals drive these choices?

## Conversation Guidelines

- Be warm, curious, and concise
- Ask open-ended follow-up questions to dig deeper
- Reflect back what you hear to show understanding
- Don't interrogate - make it feel like a natural chat
- 2-4 exchanges is usually enough to understand their intent

## Response Format

ALWAYS structure your response with these XML tags:

<response>
Your conversational reply to the user goes here. Keep it natural and engaging.
</response>

<onboarding_status>
<complete>false</complete>
<ready>false</ready>
</onboarding_status>

### When you have gathered enough information:

First, set `ready=true` (but `complete=false`) and ask if they'd like to add anything:

<response>
Summarize what you've learned and ask: "Is there anything else you'd like to add, or are we good to go?"
</response>

<onboarding_status>
<complete>false</complete>
<ready>true</ready>
</onboarding_status>

### When the user confirms they're done (says "done", "no", "that's all", "good to go", etc.):

Only then, set `complete=true` and include the profile:

<response>
Your final message acknowledging their intentions and wrapping up.
</response>

<onboarding_status>
<complete>true</complete>
<ready>true</ready>
</onboarding_status>

<profile>
<daily_intentions>
<intention>First activity or priority</intention>
<intention>Second activity or priority</intention>
</daily_intentions>
<values>
<value>A value that drives their choices</value>
<value>Another underlying value</value>
</values>
<goals>
<goal>A goal they're working towards</goal>
<goal>Another goal</goal>
</goals>
</profile>

### If the user adds more context after you asked:

Continue the conversation naturally, incorporate the new info, and when ready, ask again if there's anything else.

## Important

- ALWAYS include <response> tags around your message
- ALWAYS include <onboarding_status> with both <complete> and <ready>
- Only set `complete=true` when the user explicitly confirms they're done
- Only include <profile> when <complete> is true
- Extract genuine insights, not generic platitudes
"""


@dataclass
class OnboardingResult:
    """Parsed result from an onboarding response."""

    response_text: str
    is_complete: bool
    daily_intentions: list[str] = field(default_factory=list)
    values: list[str] = field(default_factory=list)
    goals: list[str] = field(default_factory=list)

    @classmethod
    def parse(cls, llm_output: str) -> "OnboardingResult":
        """Parse LLM output into structured result.

        Args:
            llm_output: Raw output from the LLM

        Returns:
            Parsed OnboardingResult
        """
        # Extract response text
        response_text = extract_tag(llm_output, "response")
        if not response_text:
            # Fallback: use the whole output if no tags found
            response_text = llm_output.strip()

        # Check completion status
        status_content = extract_tag(llm_output, "onboarding_status")
        complete_str = extract_tag(status_content or "", "complete") if status_content else None
        is_complete = complete_str and complete_str.lower() == "true"

        # Extract profile if complete
        daily_intentions: list[str] = []
        values: list[str] = []
        goals: list[str] = []

        if is_complete:
            profile_content = extract_tag(llm_output, "profile")
            if profile_content:
                daily_intentions = extract_list(profile_content, "daily_intentions", "intention")
                values = extract_list(profile_content, "values", "value")
                goals = extract_list(profile_content, "goals", "goal")

        return cls(
            response_text=response_text,
            is_complete=is_complete,
            daily_intentions=daily_intentions,
            values=values,
            goals=goals,
        )


class OnboardingPrompt(BasePrompt):
    """Prompt template for onboarding conversations."""

    @property
    def system_prompt(self) -> str:
        return ONBOARDING_SYSTEM_PROMPT

    def format_messages(self, history: list[PromptMessage]) -> list[PromptMessage]:
        """Format conversation history with system prompt.

        Args:
            history: List of user/assistant messages

        Returns:
            Messages ready for LLM API call
        """
        messages = [PromptMessage(role="system", content=self.system_prompt)]
        messages.extend(history)
        return messages

