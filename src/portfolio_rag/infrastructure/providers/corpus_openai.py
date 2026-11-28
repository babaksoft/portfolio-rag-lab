"""OpenAI Responses adapter for budgeted offline summary generation."""

from decimal import Decimal
from typing import Final, Literal

from openai import APIError, OpenAI, omit

from portfolio_rag.application.services import GenerationResponse
from portfolio_rag.infrastructure.db import DbCorpusBudget

MINI_MODEL: Final = "gpt-5.4-mini-2026-03-17"
SOL_MODEL: Final = "gpt-6.2-sol"
CorpusModel = Literal["gpt-5.4-mini-2026-03-17", "gpt-6.2-sol"]
MAX_INPUT_TOKENS = 272_000
MAX_OUTPUT_TOKENS = 8_000

_TOKENS_PER_MILLION = 1_000_000
_RATES_USD_PER_MILLION: dict[CorpusModel, tuple[Decimal, Decimal]] = {
    MINI_MODEL: (Decimal("0.75"), Decimal("4.50")),
    SOL_MODEL: (Decimal("2.00"), Decimal("10.00")),
}
"""Standard short-context prices in USD per million input and output tokens."""
_REASONING: dict[CorpusModel, Literal["low", "medium"]] = {
    MINI_MODEL: "low",
    SOL_MODEL: "medium",
}


def reasoning_effort(model: CorpusModel) -> Literal["low", "medium"]:
    """Return the reasoning setting recorded for this model's runs."""
    return _REASONING[model]


def _cost_usd(model: CorpusModel, input_tokens: int, output_tokens: int) -> Decimal:
    """Calculate the USD charge at the model's uncached token rates."""
    input_rate, output_rate = _RATES_USD_PER_MILLION[model]
    return (
        input_tokens * input_rate + output_tokens * output_rate
    ) / _TOKENS_PER_MILLION


class OpenAICorpusGenerator:
    """Generate one summary without implicit retries or paid tool calls."""

    def __init__(
        self, client: OpenAI, model: CorpusModel, budget: DbCorpusBudget, *, pilot: bool
    ) -> None:
        """Bind the model and ledger and disable hidden adapter retries.

        Args:
            client:
                OpenAI client to configure with implicit retries disabled.
            model:
                Requested model identifier used for inference and cost estimates.
            budget:
                Persistent ledger for inference charges.
            pilot:
                Whether attempts also count against the pilot limit.
        """
        self._client: OpenAI = client.with_options(max_retries=0)
        self._model: CorpusModel = model
        self._budget: DbCorpusBudget = budget
        self._pilot: bool = pilot

    def generate(self, instructions: str, source_payload: str) -> GenerationResponse:
        """Count, reserve, send, and reconcile one bounded inference request.

        Args:
            instructions:
                Summary instructions kept separate from repository content.
            source_payload:
                Serialized selection of approved source text.

        Returns:
            The completion with provider-reported identity and token usage.

        Raises:
            ValueError:
                Counting, budget validation, or generation failed.
        """
        try:
            token_count = self._client.responses.input_tokens.count(
                model=self._model,
                instructions=instructions,
                input=source_payload,
                reasoning={"effort": reasoning_effort(self._model)},
                truncation="disabled",
                text={"format": {"type": "json_object"}},
            ).input_tokens
        except APIError:
            raise ValueError("OpenAI could not count the request input") from None

        if token_count > MAX_INPUT_TOKENS:
            raise ValueError(
                "input exceeds 272,000 tokens. Narrow the source selection"
            )

        attempt = self._budget.reserve(
            _cost_usd(self._model, token_count, MAX_OUTPUT_TOKENS),
            pilot=self._pilot,
        )
        try:
            response = self._client.responses.create(
                model=self._model,
                instructions=instructions,
                input=source_payload,
                reasoning={"effort": reasoning_effort(self._model)},
                max_output_tokens=MAX_OUTPUT_TOKENS,
                prompt_cache_options={"mode": "explicit"}
                if self._model == SOL_MODEL
                else omit,
                service_tier="default",
                truncation="disabled",
                store=False,
                text={"format": {"type": "json_object"}},
            )
        except APIError:
            raise ValueError(
                "OpenAI corpus generation failed; its reservation was kept"
            ) from None

        usage = response.usage
        if usage is not None:
            self._budget.settle(
                attempt,
                _cost_usd(self._model, usage.input_tokens, usage.output_tokens),
            )
        if response.status != "completed" or not response.output_text.strip():
            raise ValueError("OpenAI did not return a complete summary")
        if response.model != self._model and not (
            self._model == SOL_MODEL and response.model.startswith(f"{SOL_MODEL}-")
        ):
            raise ValueError("OpenAI returned an unexpected model identifier")

        return GenerationResponse(
            text=response.output_text,
            model=response.model,
            input_tokens=usage.input_tokens if usage else None,
            output_tokens=usage.output_tokens if usage else None,
        )
