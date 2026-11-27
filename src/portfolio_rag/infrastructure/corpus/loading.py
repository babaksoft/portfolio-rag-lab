"""Load and validate local corpus artifacts and evaluation references."""

import hashlib
import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from portfolio_rag.infrastructure.corpus.models import (
    CorpusManifest,
    CorpusSource,
    EvaluationDataset,
)


class LoadedCorpus(BaseModel):
    """Verified contents of one portfolio corpus.

    Attributes:
        manifest:
            Validated metadata for the verified Markdown documents.
        version:
            SHA-256 hash of the canonical manifest, including the document hashes.
        documents:
            Verified Markdown text in manifest source order.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    manifest: CorpusManifest = Field(description="Validated corpus manifest.")
    version: str = Field(description="Lowercase hexadecimal SHA-256 manifest hash.")
    documents: tuple[str, ...] = Field(description="Markdown in manifest source order.")


def _read_document(path: Path, source: CorpusSource) -> str:
    """Verify a document's hash and decode its Markdown."""
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != source.content_sha256:
        raise ValueError(f"content hash mismatch for {path.name}")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{path.name} must be UTF-8 Markdown") from exc
    if not text.strip():
        raise ValueError(f"{path.name} must contain Markdown text")
    return text


def load_corpus(directory: Path) -> LoadedCorpus:
    """Verify the file set and bytes in one flat, versioned corpus.

    Args:
        directory:
            Directory containing the manifest and its Markdown files.

    Returns:
        The verified text, manifest, and computed corpus version.

    Raises:
        OSError:
            A directory or file could not be read.
        ValueError:
            The manifest, file set, or document content is invalid.
    """
    entries = {path.name: path for path in directory.iterdir()}
    if any(path.is_symlink() or not path.is_file() for path in entries.values()):
        raise ValueError("corpus directory must contain only regular files")
    if "manifest.json" not in entries:
        raise ValueError("corpus directory is missing manifest.json")
    manifest = CorpusManifest.model_validate_json(entries["manifest.json"].read_bytes())

    filenames = [f"{source.source_id}.md" for source in manifest.sources]
    if len(filenames) != len(set(filenames)):
        raise ValueError("corpus source IDs must be unique")
    if entries.keys() != {"manifest.json", *filenames}:
        raise ValueError("corpus files do not match the manifest")
    documents = tuple(
        _read_document(entries[filename], source)
        for filename, source in zip(filenames, manifest.sources, strict=True)
    )

    canonical_manifest = json.dumps(
        manifest.model_dump(mode="json"),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    version = hashlib.sha256(canonical_manifest).hexdigest()
    return LoadedCorpus(manifest=manifest, version=version, documents=documents)


def load_evaluation_cases(path: Path, corpus: LoadedCorpus) -> EvaluationDataset:
    """Load cases and resolve their citations against a verified corpus version.

    Args:
        path:
            JSON dataset containing the cases.
        corpus:
            Verified corpus to which the cases refer.

    Returns:
        The dataset with its version and citation references checked.

    Raises:
        OSError:
            The dataset could not be read.
        ValueError:
            The dataset, case identities, or evidence references are invalid.
    """
    dataset = EvaluationDataset.model_validate_json(path.read_bytes())
    if dataset.corpus_version != corpus.version:
        raise ValueError("evaluation corpus version does not match the loaded corpus")
    if len({case.case_id for case in dataset.cases}) != len(dataset.cases):
        raise ValueError("evaluation case IDs must be unique")

    lines_by_source = {
        source.source_id: text.removesuffix("\n").split("\n")
        for source, text in zip(corpus.manifest.sources, corpus.documents, strict=True)
    }
    for case in dataset.cases:
        for location in case.expected_evidence:
            lines = lines_by_source.get(location.source_id)
            start, end = location.start_line, location.end_line
            if lines is None or not (start <= end <= len(lines)):
                raise ValueError(
                    f"{case.case_id}: unresolved citation {location.source_id}:{start}-{end}"
                )
            if not any(line.strip() for line in lines[start - 1 : end]):
                raise ValueError(
                    f"{case.case_id}: empty citation {location.source_id}:{start}-{end}"
                )
    return dataset
