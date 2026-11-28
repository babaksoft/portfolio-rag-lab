"""Exercise corpus provider requests and budget accounting with mock HTTP responses."""

import json
import sqlite3
from contextlib import closing
from decimal import Decimal
from pathlib import Path

import httpx
import pytest
from openai import OpenAI

from portfolio_rag.infrastructure.db import DbCorpusBudget
from portfolio_rag.infrastructure.providers import (
    MAX_OUTPUT_TOKENS,
    MINI_MODEL,
    SOL_MODEL,
    CorpusModel,
    OpenAICorpusGenerator,
)


def _mock_client(
    requests: list[tuple[str, dict[str, object]]], response_status: int
) -> OpenAI:
    """Create a client with predictable token counts and a configurable outcome."""

    def respond(request: httpx.Request) -> httpx.Response:
        """Record the request and return the synthetic count or inference response."""
        body = json.loads(request.content)
        requests.append((request.url.path, body))
        if request.url.path.endswith("input_tokens"):
            return httpx.Response(200, json={"input_tokens": 231})
        if response_status != 200:
            return httpx.Response(
                response_status, json={"error": {"message": "synthetic"}}
            )
        return httpx.Response(
            200,
            json={
                "model": body["model"],
                "status": "completed",
                "output": [
                    {
                        "type": "message",
                        "content": [{"type": "output_text", "text": "summary"}],
                    }
                ],
                "usage": {"input_tokens": 231, "output_tokens": 11},
            },
        )

    return OpenAI(
        api_key="test-key",
        http_client=httpx.Client(transport=httpx.MockTransport(respond)),
    )


@pytest.mark.parametrize(
    ("model", "reasoning", "expected_cost"),
    [
        (MINI_MODEL, "low", Decimal("0.00022275")),
        (SOL_MODEL, "medium", Decimal("0.000572")),
    ],
)
def test_successful_usage_replaces_worst_case_reservation(
    tmp_path: Path, model: CorpusModel, reasoning: str, expected_cost: Decimal
) -> None:
    """Settle two requests at the configured rates and verify the exact remaining budget."""
    requests: list[tuple[str, dict[str, object]]] = []
    budget = DbCorpusBudget(tmp_path / "spend.sqlite")
    budget.reserve(Decimal("1.90"), pilot=True)
    with _mock_client(requests, 200) as client:
        generator = OpenAICorpusGenerator(client, model, budget, pilot=True)
        response = generator.generate("JSON format", "pinned files")
        generator.generate("JSON format", "pinned files")
    budget.reserve(Decimal("0.10") - 2 * expected_cost, pilot=True)
    with pytest.raises(ValueError, match="would be exceeded"):
        budget.reserve(Decimal("0.000000001"), pilot=True)

    count, create = requests[:2]
    assert count[0].endswith("input_tokens")
    assert create[1]["max_output_tokens"] == MAX_OUTPUT_TOKENS
    assert create[1]["reasoning"] == {"effort": reasoning}
    assert create[1]["store"] is False
    assert response.input_tokens == 231
    assert response.output_tokens == 11


def test_failed_request_keeps_reservation_and_prevents_a_second_inference(
    tmp_path: Path,
) -> None:
    """Keep an unknown charge and reject an inference that exceeds the pilot limit."""
    requests: list[tuple[str, dict[str, object]]] = []
    ledger = tmp_path / "spend.sqlite"
    budget = DbCorpusBudget(ledger)
    budget.reserve(Decimal("1.90"), pilot=True)
    with _mock_client(requests, 500) as client:
        generator = OpenAICorpusGenerator(client, SOL_MODEL, budget, pilot=True)
        with pytest.raises(ValueError, match="reservation was kept"):
            generator.generate("JSON format", "pinned files")
        next_run = OpenAICorpusGenerator(
            client, SOL_MODEL, DbCorpusBudget(ledger), pilot=True
        )
        with pytest.raises(ValueError, match="would be exceeded"):
            next_run.generate("JSON format", "pinned files")

    assert sum(path.endswith("/responses") for path, _ in requests) == 1


def test_total_allowance_includes_pilot_spend(tmp_path: Path) -> None:
    """Count prior pilot charges in an existing ledger against the total limit."""
    ledger = tmp_path / "spend.sqlite"
    with closing(sqlite3.connect(ledger)) as connection, connection:
        connection.execute(
            "CREATE TABLE charges (attempt TEXT PRIMARY KEY, pilot INTEGER NOT NULL, cost INTEGER NOT NULL)"
        )
        connection.execute(
            "INSERT INTO charges VALUES (?, ?, ?)", ("prior-pilot", True, 2_000_000_000)
        )
    budget = DbCorpusBudget(ledger)
    budget.reserve(Decimal("8.00"), pilot=False)

    with pytest.raises(ValueError, match="would be exceeded"):
        budget.reserve(Decimal("0.000000001"), pilot=False)
