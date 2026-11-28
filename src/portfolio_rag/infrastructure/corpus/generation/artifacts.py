"""Stage validated corpus candidates and publish reviewed immutable versions."""

import hashlib
import re
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from pydantic import AnyUrl, BaseModel, ConfigDict, Field

from portfolio_rag.application.services import GenerationResponse
from portfolio_rag.infrastructure.corpus import (
    CorpusManifest,
    CorpusSource,
    load_corpus,
    load_evaluation_cases,
)
from portfolio_rag.infrastructure.corpus.generation.snapshot import SummaryUnit
from portfolio_rag.validation import SHA256_HEX_PATTERN


class RunSettings(BaseModel):
    """Settings recorded outside the versioned corpus format.

    Attributes:
        model:
            Requested model identifier.
        reasoning:
            Reasoning effort requested by the adapter.
        max_output_tokens:
            Maximum billed output tokens per request.
        prompt_revision:
            Revision of the shared generation prompt.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    model: str = Field(description="Requested model identifier.")
    reasoning: str = Field(description="Configured internal reasoning effort.")
    max_output_tokens: int = Field(ge=1, description="Per-request output token cap.")
    prompt_revision: str = Field(
        description="Revision of the shared generation prompt."
    )


def stage_candidate(
    root: Path,
    settings: RunSettings,
    results: tuple[tuple[SummaryUnit, GenerationResponse], ...],
) -> Path:
    """Validate generated Markdown and expose a complete candidate with a run record.

    Args:
        root:
            Parent directory for temporary work and completed candidates.
        settings:
            Model and prompt configuration recorded with the candidate.
        results:
            Source selections and generated documents in manifest order.

    Returns:
        The completed candidate directory under the staging root.

    Raises:
        OSError:
            The candidate files could not be written or renamed.
        ValueError:
            The generated artifact fails corpus validation.
    """
    root.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=root, prefix=".staging-") as temporary:
        staged = Path(temporary) / "candidate"
        corpus = staged / "corpus"
        corpus.mkdir(parents=True)
        sources = []
        records = []

        for unit, response in results:
            content = response.text.encode("utf-8")
            (corpus / f"{unit.source_id}.md").write_bytes(content)
            sources.append(
                CorpusSource(
                    source_id=unit.source_id,
                    origin_url=AnyUrl(unit.origin_url),
                    content_sha256=hashlib.sha256(content).hexdigest(),
                )
            )
            records.append(
                _UnitRecord(
                    selection=unit,
                    model=response.model,
                    input_tokens=response.input_tokens,
                    output_tokens=response.output_tokens,
                )
            )

        manifest = CorpusManifest(schema_version=1, sources=tuple(sources))
        (corpus / "manifest.json").write_text(
            manifest.model_dump_json(indent=2) + "\n", encoding="utf-8"
        )
        record = _RunRecord(
            settings=settings,
            corpus_version=load_corpus(corpus).version,
            units=tuple(records),
        )
        (staged / "run.json").write_text(
            record.model_dump_json(indent=2) + "\n", encoding="utf-8"
        )

        return staged.rename(root / uuid4().hex)


def promote_candidate(
    candidate: Path, evaluation: Path, releases: Path, version: str
) -> Path:
    """Publish a complete version and keep earlier releases available.

    Args:
        candidate:
            Staged generation result with a corpus and run record.
        evaluation:
            Reviewed evaluation dataset for the candidate.
        releases:
            Parent directory for immutable approved versions.
        version:
            Exact SHA-256 corpus version approved by the reviewer.

    Returns:
        The approved version directory.

    Raises:
        ValueError:
            The candidate, evaluation, or existing release fails validation.
        OSError:
            Files could not be read, staged, or renamed.
    """
    if re.fullmatch(SHA256_HEX_PATTERN, version) is None:
        raise ValueError("provide the approved 64-character corpus version")
    releases.mkdir(parents=True, exist_ok=True)
    destination = releases / version
    with TemporaryDirectory(dir=releases, prefix=".staging-") as temporary:
        staging = Path(temporary) / "release"
        staging.mkdir()
        shutil.copytree(candidate / "corpus", staging / "corpus", symlinks=True)
        shutil.copyfile(candidate / "run.json", staging / "run.json")
        shutil.copyfile(evaluation, staging / "evaluation.json")
        _validate_release(staging, version)
        if destination.exists() or destination.is_symlink():
            return _existing_release(staging, destination, version)
        try:
            return staging.rename(destination)
        except OSError:
            if not destination.is_dir():
                raise
            return _existing_release(staging, destination, version)


def _validate_release(directory: Path, version: str) -> None:
    """Verify that the review record, evaluation, and copied corpus identify the same bytes."""
    corpus = load_corpus(directory / "corpus")
    record = _RunRecord.model_validate_json((directory / "run.json").read_bytes())
    if corpus.version != version or record.corpus_version != version:
        raise ValueError("artifact differs from the reviewed corpus version")
    recorded_sources = tuple(
        (unit.selection.source_id, AnyUrl(unit.selection.origin_url))
        for unit in record.units
    )
    if recorded_sources != tuple(
        (source.source_id, source.origin_url) for source in corpus.manifest.sources
    ):
        raise ValueError("run record source identities do not match the manifest")
    load_evaluation_cases(directory / "evaluation.json", corpus)


def _existing_release(staging: Path, destination: Path, version: str) -> Path:
    """Allow re-promotion only when the existing release matches byte for byte."""
    if destination.is_symlink():
        raise ValueError("the release path must be a real directory")
    _validate_release(destination, version)

    files = {path.relative_to(staging) for path in staging.rglob("*") if path.is_file()}
    existing = {
        path.relative_to(destination)
        for path in destination.rglob("*")
        if path.is_file()
    }
    if files != existing or any(
        (destination / path).is_symlink()
        or (staging / path).read_bytes() != (destination / path).read_bytes()
        for path in files
    ):
        raise ValueError(
            "the immutable corpus release already exists with different bytes"
        )
    return destination


class _UnitRecord(BaseModel):
    """Inputs and usage for a generated document.

    Attributes:
        selection:
            Pinned checkout, paths, and focus used to generate the document.
        model:
            Model identifier returned by the provider.
        input_tokens:
            Reported input token count, or null when unavailable.
        output_tokens:
            Reported output token count including reasoning, or null when unavailable.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    selection: SummaryUnit = Field(
        description="Pinned repository, path selection, and focus."
    )
    model: str = Field(description="Provider-reported model identifier.")
    input_tokens: int | None = Field(description="Provider input usage when available.")
    output_tokens: int | None = Field(
        description="Provider output usage when available."
    )


class _RunRecord(BaseModel):
    """Successful generation run metadata.

    Attributes:
        settings:
            Requested model and generation configuration.
        corpus_version:
            Lowercase SHA-256 digest of the validated canonical manifest.
        units:
            Source selections and generation usage in manifest order.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    settings: RunSettings = Field(
        description="Requested model and generation settings."
    )
    corpus_version: str = Field(description="Manifest version of the validated output.")
    units: tuple[_UnitRecord, ...] = Field(
        description="Inputs and usage in manifest order."
    )
