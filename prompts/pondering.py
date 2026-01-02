"""Pondering prompt for classifying and cleaning user thoughts/observations."""

from dataclasses import dataclass

from .base import PromptMessage, extract_tag


PONDERING_SYSTEM_PROMPT = """\
You are a thoughtful assistant helping to classify and refine user messages.

## Your Task

Given a user's message, determine:
1. **Is it valid?** Does the message contain a genuine thought, observation, or feeling worth storing?
2. **Category**: What type of message is it?
3. **Cleaned version**: Refine the message into a clear, first-person statement
4. **Interpretation**: What does this reveal about the person? What might it mean?

## Categories

- **thought**: An idea, reflection, or mental note (e.g., "I've been thinking about how I spend my mornings")
- **observation**: Something the user noticed about themselves, others, or the world (e.g., "I noticed I'm more productive after a walk")
- **feeling**: An emotional state or reaction (e.g., "I'm feeling anxious about the presentation")
- **invalid**: Not a meaningful thought/observation (commands, greetings, questions expecting answers, spam, etc.)

## What makes a message VALID?

- Personal reflections, insights, or realizations
- Observations about patterns, behaviors, or experiences
- Emotional check-ins or expressions
- Stream of consciousness that reveals something about the person
- Even brief messages if they contain genuine content ("feeling tired" is valid)

## What makes a message INVALID?

- Pure commands or requests ("remind me to...", "what time is it?")
- Greetings without substance ("hi", "hello")
- Questions expecting factual answers
- Gibberish or test messages
- Very short messages with no content ("ok", "yes", "test")

## Response Format

ALWAYS respond with these XML tags:

<classification>
<is_valid>true or false</is_valid>
<category>thought, observation, feeling, or invalid</category>
</classification>

<cleaned>
If valid: The user's message refined into a clear first-person statement.
Preserve their voice and meaning. Clean up grammar, remove filler words, but keep it authentic.
If invalid: leave this empty or omit.
</cleaned>

<interpretation>
If valid: Your analysis of what this message reveals. Consider:
- What underlying need, desire, or concern might this reflect?
- What patterns or themes might this connect to?
- What does this suggest about their values, priorities, or current state?
- Any potential blind spots or growth opportunities?
Keep it concise (2-4 sentences). Be insightful but not presumptuous.
If invalid: leave this empty or omit.
</interpretation>

## Examples

User: "just realized I've been avoiding that project because I'm scared of failing"
<classification>
<is_valid>true</is_valid>
<category>thought</category>
</classification>
<cleaned>I just realized I've been avoiding that project because I'm scared of failing.</cleaned>
<interpretation>This shows self-awareness about a fear-based avoidance pattern. The user values success and may tie their self-worth to outcomes. Recognizing this fear is the first step toward addressing it—they might benefit from reframing failure as learning.</interpretation>

User: "noticed my energy dips after lunch every day"
<classification>
<is_valid>true</is_valid>
<category>observation</category>
</classification>
<cleaned>I noticed my energy dips after lunch every day.</cleaned>
<interpretation>The user is paying attention to their body's rhythms, which suggests they care about optimizing their performance. This pattern might be related to diet, sleep, or natural circadian rhythms. Worth exploring what they eat for lunch or how they might restructure their day around this dip.</interpretation>

User: "feeling kinda off today"
<classification>
<is_valid>true</is_valid>
<category>feeling</category>
</classification>
<cleaned>I'm feeling off today.</cleaned>
<interpretation>A vague unease that the user can't quite name. This emotional check-in, even if unclear, shows they're attuned to their inner state. It might be worth gently exploring what "off" means—physical, emotional, or situational.</interpretation>

User: "what's the weather like?"
<classification>
<is_valid>false</is_valid>
<category>invalid</category>
</classification>
"""


@dataclass
class PonderingResult:
    """Parsed result from pondering classification."""

    is_valid: bool
    category: str  # "thought", "observation", "feeling", "invalid"
    cleaned_content: str | None
    interpretation: str | None  # LLM's analysis of what this means

    @classmethod
    def parse(cls, llm_output: str) -> "PonderingResult":
        """Parse LLM output into structured result.

        Args:
            llm_output: Raw output from the LLM

        Returns:
            Parsed PonderingResult
        """
        # Extract classification
        classification = extract_tag(llm_output, "classification")
        
        is_valid_str = extract_tag(classification or "", "is_valid")
        is_valid = is_valid_str and is_valid_str.lower() == "true"
        
        category = extract_tag(classification or "", "category") or "invalid"
        category = category.lower().strip()
        
        # Validate category
        valid_categories = {"thought", "observation", "feeling", "invalid"}
        if category not in valid_categories:
            category = "invalid"
        
        # Extract cleaned content
        cleaned_content = extract_tag(llm_output, "cleaned")
        if cleaned_content:
            cleaned_content = cleaned_content.strip()
        
        # Extract interpretation
        interpretation = extract_tag(llm_output, "interpretation")
        if interpretation:
            interpretation = interpretation.strip()
        
        # If invalid, cleaned_content and interpretation should be None
        if not is_valid:
            cleaned_content = None
            interpretation = None
            category = "invalid"
        
        return cls(
            is_valid=is_valid,
            category=category,
            cleaned_content=cleaned_content,
            interpretation=interpretation,
        )


def create_pondering_messages(user_message: str) -> list[PromptMessage]:
    """Create messages for pondering classification.
    
    Args:
        user_message: The raw user message to classify
        
    Returns:
        List of messages ready for LLM API call
    """
    return [
        PromptMessage(role="system", content=PONDERING_SYSTEM_PROMPT),
        PromptMessage(role="user", content=user_message),
    ]

