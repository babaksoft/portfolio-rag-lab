"""Persisted formats for a portfolio corpus and its offline evaluation cases."""

import re
from typing import Literal, Self

from pydantic import (
    AnyUrl,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from portfolio_rag.validation import (
    LOWER_KEBAB_CASE_PATTERN,
    NON_BLANK_PATTERN,
    SHA256_HEX_PATTERN,
)


class CorpusSource(BaseModel):
    """One Markdown file and its publishable origin.

    Attributes:
        source_id:
            Stable identity and basename of the document within the corpus.
        origin_url:
            Public URL identifying the source revision.
        content_sha256:
            SHA-256 digest of the stored Markdown bytes.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    source_id: str = Field(
        pattern=LOWER_KEBAB_CASE_PATTERN,
        description="Stable identifier. The document is stored as <source_id>.md.",
    )
    origin_url: AnyUrl = Field(
        description="Public HTTPS location of the immutable source revision."
    )
    content_sha256: str = Field(
        pattern=SHA256_HEX_PATTERN,
        description="Lowercase hexadecimal SHA-256 digest of the exact Markdown bytes.",
    )

    @field_validator("origin_url")
    @classmethod
    def validate_origin_url(cls, value: AnyUrl) -> AnyUrl:
        """Require HTTPS for the parsed source URL."""
        if value.scheme != "https":
            raise ValueError("origin URL must use HTTPS")
        return value


class CorpusManifest(BaseModel):
    """Versioned description of the files in one flat corpus directory.

    Attributes:
        schema_version:
            Format version of the stored manifest.
        sources:
            Ordered source records for the Markdown files in this corpus.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    schema_version: int = Field(ge=1, le=1, description="Manifest format version.")
    sources: tuple[CorpusSource, ...] = Field(
        min_length=1, description="Ordered source records included in the corpus hash."
    )


class CitationLocation(BaseModel):
    """Inclusive line range in a Markdown file of the dataset's corpus.

    Attributes:
        source_id:
            Stable source identifier from the manifest.
        start_line:
            First cited line, numbered from one.
        end_line:
            Last cited line, inclusive.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    source_id: str = Field(
        pattern=LOWER_KEBAB_CASE_PATTERN, description="Source identifier in the corpus."
    )
    start_line: int = Field(ge=1, description="First cited Markdown line, one-based.")
    end_line: int = Field(ge=1, description="Last cited Markdown line, inclusive.")


class EvaluationCase(BaseModel):
    """Hand-authored expectation for a single portfolio question.

    Attributes:
        case_id:
            Stable identifier within the dataset.
        question:
            Input presented to the assistant.
        expected_outcome:
            Whether the assistant should answer or abstain.
        required_facts:
            Facts a correct answer must cover, empty for abstention.
        expected_evidence:
            Citation locations supporting the facts, empty for abstention.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    case_id: str = Field(
        pattern=LOWER_KEBAB_CASE_PATTERN,
        description="Stable identifier within the dataset.",
    )
    question: str = Field(
        min_length=1,
        pattern=NON_BLANK_PATTERN,
        description="Question presented to the assistant.",
    )
    expected_outcome: Literal["answer", "abstain"] = Field(
        description="Expected response to this question on the pinned corpus."
    )
    required_facts: tuple[str, ...] = Field(
        default=(), description="Facts a correct answer must cover. Empty by default."
    )
    expected_evidence: tuple[CitationLocation, ...] = Field(
        default=(), description="Expected citation locations. Empty by default."
    )

    @field_validator("required_facts")
    @classmethod
    def validate_required_facts(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        """Require non-blank text for each fact."""
        if any(re.search(NON_BLANK_PATTERN, value) is None for value in values):
            raise ValueError("required facts must contain non-blank text")
        return values

    @model_validator(mode="after")
    def validate_expectations(self) -> Self:
        """Check that the facts and evidence agree with the expected outcome."""
        if self.expected_outcome == "answer":
            if not self.required_facts or not self.expected_evidence:
                raise ValueError("an answer requires facts and evidence")
        elif self.required_facts or self.expected_evidence:
            raise ValueError("an abstention must have empty facts and evidence")
        return self


class EvaluationDataset(BaseModel):
    """Hand-authored cases pinned to one corpus version.

    Attributes:
        schema_version:
            Format version of the stored dataset.
        corpus_version:
            Manifest hash identifying the corpus that the cases were reviewed against.
        cases:
            Ordered cases for the pinned corpus.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    schema_version: int = Field(
        ge=1, le=1, description="Evaluation dataset format version."
    )
    corpus_version: str = Field(
        pattern=SHA256_HEX_PATTERN,
        description="Lowercase hexadecimal SHA-256 hash of the canonical manifest.",
    )
    cases: tuple[EvaluationCase, ...] = Field(
        min_length=1, description="Hand-authored cases for this corpus version."
    )
