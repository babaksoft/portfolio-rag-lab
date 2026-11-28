"""Load the credential used by the offline corpus generation command."""

from pathlib import Path

from pydantic import Field, SecretStr, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict, SettingsError


class _CorpusOpenAISettings(BaseSettings):
    """Accept the corpus key from the environment or a local dotenv file.

    Attributes:
        openai_api_key:
            Nonempty credential read from OPENAI_API_KEY.
    """

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
        hide_input_in_errors=True,
    )

    openai_api_key: SecretStr = Field(
        min_length=1,
        repr=False,
        description="Project OpenAI API key for corpus generation.",
    )


def load_corpus_openai_key(env_file: Path) -> SecretStr:
    """Read the generation credential and report configuration errors safely.

    Args:
        env_file:
            Dotenv path used when OPENAI_API_KEY is absent from the environment.

    Returns:
        The masked credential to pass to the OpenAI client.

    Raises:
        ValueError:
            The key is missing or the configuration cannot be read.
    """
    try:
        # The generated mypy signature omits the BaseSettings runtime options.
        settings = _CorpusOpenAISettings(_env_file=env_file)  # type: ignore[call-arg]
    except (OSError, UnicodeError, ValidationError, SettingsError):
        raise ValueError(
            "Configure OPENAI_API_KEY in the checkout's .env file or process environment"
        ) from None

    return settings.openai_api_key
