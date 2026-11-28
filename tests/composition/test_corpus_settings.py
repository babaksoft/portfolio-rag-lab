"""Verify local corpus credential loading with synthetic dotenv values."""

from os import getenv
from pathlib import Path

import pytest

from portfolio_rag.composition.offline_corpus import load_corpus_openai_key


@pytest.mark.parametrize("environment_key", [None, "synthetic-environment-key"])
def test_load_corpus_openai_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, environment_key: str | None
) -> None:
    """Load the dotenv key without mutating the environment and honor overrides."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "OPENAI_API_KEY=synthetic-dotenv-key\nUNRELATED_SETTING=ignored\n",
        encoding="utf-8",
    )
    if environment_key is None:
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    else:
        monkeypatch.setenv("OPENAI_API_KEY", environment_key)

    key = load_corpus_openai_key(env_file)

    assert key.get_secret_value() == (environment_key or "synthetic-dotenv-key")
    assert getenv("OPENAI_API_KEY") == environment_key
    assert "synthetic-" not in repr(key)


def test_missing_corpus_key_reports_only_configuration_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Report how to configure a missing key without exposing dotenv values."""
    env_file = tmp_path / ".env"
    env_file.write_text("UNRELATED_SECRET=synthetic-other-secret\n", encoding="utf-8")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ValueError, match=r"^Configure OPENAI_API_KEY") as error:
        load_corpus_openai_key(env_file)

    assert "synthetic-other-secret" not in str(error.value)
