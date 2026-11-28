"""Read explicit public-source selections from immutable Git trees."""

import re
import subprocess
from pathlib import Path
from typing import Self
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, model_validator

from portfolio_rag.validation import (
    GIT_CHECKOUT_NAME_PATTERN,
    GIT_PATH_PART_PATTERN,
    GIT_SHA1_PATTERN,
    LOWER_KEBAB_CASE_PATTERN,
    NON_BLANK_PATTERN,
    SINGLE_LINE_PATTERN,
)


class SummaryUnit(BaseModel):
    """One logical corpus document and its explicit source selection.

    Attributes:
        source_id:
            Stable flat-corpus basename.
        repository:
            Local checkout name beneath the configured repositories directory.
        commit:
            Full Git commit ID, independent of the working tree.
        origin_url:
            Public HTTPS URL for the pinned source tree.
        title:
            Heading used in the generated document.
        focus:
            Behavior the summary should explain and verify.
        files:
            Repository-relative Git blob paths, in prompt order.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    source_id: str = Field(pattern=LOWER_KEBAB_CASE_PATTERN, description="Document ID.")
    repository: str = Field(
        pattern=GIT_CHECKOUT_NAME_PATTERN,
        description="Local Git checkout basename.",
    )
    commit: str = Field(
        pattern=GIT_SHA1_PATTERN, description="Full SHA-1 Git commit ID."
    )
    origin_url: str = Field(
        description="Public HTTPS URL pinned to the selected commit."
    )
    title: str = Field(
        pattern=SINGLE_LINE_PATTERN, description="Generated document heading."
    )
    focus: str = Field(
        pattern=NON_BLANK_PATTERN, description="Summary scope and facts to cover."
    )
    files: tuple[str, ...] = Field(
        min_length=1, description="Explicit committed paths."
    )

    @model_validator(mode="after")
    def _validate_source(self) -> Self:
        """Validate the public pin and unambiguous literal Git paths."""
        origin = urlsplit(self.origin_url)
        if origin.scheme != "https" or not origin.hostname or origin.username:
            raise ValueError("origin must be a public HTTPS URL")
        if self.commit not in origin.path.split("/"):
            raise ValueError("origin URL must contain the selected commit")
        if len(set(self.files)) != len(self.files):
            raise ValueError("the selected file paths must be unique")
        for file in self.files:
            if any(
                not re.fullmatch(GIT_PATH_PART_PATTERN, part) or part in {".", ".."}
                for part in file.split("/")
            ):
                raise ValueError("select literal repository-relative paths")
        return self


class _Selection(BaseModel):
    """On-disk JSON selection of logical units.

    Attributes:
        units:
            Explicit summary units in generation and manifest order.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    units: tuple[SummaryUnit, ...] = Field(
        min_length=1, description="Ordered units to generate."
    )


def load_summary_units(path: Path) -> tuple[SummaryUnit, ...]:
    """Load the selected units from JSON in stable order."""
    units = _Selection.model_validate_json(path.read_bytes()).units
    if len({unit.source_id for unit in units}) != len(units):
        raise ValueError("summary source IDs must be unique")
    return units


def read_snapshot(repositories: Path, unit: SummaryUnit) -> dict[str, str]:
    """Read regular UTF-8 blobs from the pinned commit in selection order."""
    repository = repositories / unit.repository
    try:
        if _git(repository, "cat-file", "-t", unit.commit).strip() != b"commit":
            raise ValueError(f"{unit.source_id}: selected revision must be a commit")
        sources = {}
        for file in unit.files:
            entry = _git(repository, "ls-tree", "-z", unit.commit, "--", file)
            metadata, _, path = entry.partition(b"\t")
            if path != file.encode() + b"\0" or not metadata.startswith(
                (b"100644 blob ", b"100755 blob ")
            ):
                raise ValueError(
                    f"{unit.source_id}: {file} must be a committed regular file"
                )
            sources[file] = _git(
                repository, "cat-file", "blob", f"{unit.commit}:{file}"
            ).decode()
        return sources
    except (subprocess.SubprocessError, UnicodeDecodeError):
        raise ValueError(
            f"{unit.source_id}: could not read the pinned Git snapshot"
        ) from None


def _git(repository: Path, *args: str) -> bytes:
    """Read Git plumbing output using actual objects and literal pathspecs."""
    return subprocess.run(
        [
            "git",
            "--no-replace-objects",
            "--literal-pathspecs",
            "-C",
            str(repository),
            *args,
        ],
        check=True,
        capture_output=True,
        timeout=15,
    ).stdout
