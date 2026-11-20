"""Return the Phase 0 placeholder for a user message."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PLACEHOLDER_ANSWER = (
    "Placeholder response: portfolio retrieval is not implemented yet, "
    "so this is not a factual answer."
)


class AnswerMessageResult(BaseModel):
    """Result returned by the placeholder message use case.

    Attributes:
        answer:
            User-visible response text.
        is_placeholder:
            Whether the response contains no factual portfolio answer.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    answer: str = Field(description="User-visible response text.")
    is_placeholder: Literal[True] = Field(
        description="Whether the response contains no factual portfolio answer."
    )


class AnswerMessageService:
    """Answer a message without claiming unavailable portfolio knowledge."""

    def execute(self, message: str) -> AnswerMessageResult:
        """Return the explicitly labeled Phase 0 response.

        Args:
            message:
                Validated non-empty user message.

        Returns:
            The safe placeholder result.

        Raises:
            ValueError:
                If the application boundary receives an empty message.
        """
        if not message.strip():
            raise ValueError("message must not be empty")

        return AnswerMessageResult(answer=PLACEHOLDER_ANSWER, is_placeholder=True)
