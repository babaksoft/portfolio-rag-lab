import json
import shutil
from pathlib import Path

import pytest

from portfolio_rag.infrastructure.corpus import load_corpus, load_evaluation_cases

SEED = Path(__file__).resolve().parents[3] / "data/portfolio/seed-v1"


def _copy_corpus(directory: Path) -> Path:
    return shutil.copytree(SEED / "corpus", directory / "corpus")


def test_seed_corpus_and_cases_resolve() -> None:
    corpus = load_corpus(SEED / "corpus")
    dataset = load_evaluation_cases(SEED / "evaluation.json", corpus)

    assert len(corpus.documents) == 2
    assert [case.expected_outcome for case in dataset.cases] == [
        "answer",
        "answer",
        "abstain",
    ]


def test_manifest_formatting_preserves_corpus_version(tmp_path: Path) -> None:
    directory = _copy_corpus(tmp_path)
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")

    corpus = load_corpus(directory)
    dataset = load_evaluation_cases(SEED / "evaluation.json", corpus)

    assert dataset.corpus_version == corpus.version


def test_rejects_changed_markdown(tmp_path: Path) -> None:
    directory = _copy_corpus(tmp_path)
    path = directory / "genai-template-flat-corpus.md"
    path.write_bytes(path.read_bytes() + b"\nChanged content.\n")

    with pytest.raises(ValueError, match="content hash mismatch"):
        load_corpus(directory)


def test_rejects_unlisted_markdown(tmp_path: Path) -> None:
    directory = _copy_corpus(tmp_path)
    (directory / "unlisted.md").write_text("Unlisted evidence", encoding="utf-8")

    with pytest.raises(ValueError, match="files do not match"):
        load_corpus(directory)


@pytest.mark.parametrize("version", [True, 1.0, 2])
def test_rejects_invalid_manifest_schema_version(
    tmp_path: Path, version: bool | float | int
) -> None:
    directory = _copy_corpus(tmp_path)
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["schema_version"] = version
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="schema_version"):
        load_corpus(directory)


def test_rejects_cases_for_another_corpus_version(tmp_path: Path) -> None:
    directory = _copy_corpus(tmp_path)
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["sources"][0]["origin_url"] = "https://example.com/other-revision"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    corpus = load_corpus(directory)

    with pytest.raises(ValueError, match="corpus version does not match"):
        load_evaluation_cases(SEED / "evaluation.json", corpus)


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("source_id", "missing-source", "unresolved citation"),
        ("start_line", 18, "unresolved citation"),
        ("end_line", 999, "unresolved citation"),
        ("start_line", 0, "greater than or equal to 1"),
    ],
)
def test_rejects_invalid_citation(
    tmp_path: Path, field: str, value: str | int, error: str
) -> None:
    corpus = load_corpus(SEED / "corpus")
    dataset = json.loads((SEED / "evaluation.json").read_text(encoding="utf-8"))
    dataset["cases"][0]["expected_evidence"][0][field] = value
    dataset_path = tmp_path / "evaluation.json"
    dataset_path.write_text(json.dumps(dataset), encoding="utf-8")

    with pytest.raises(ValueError, match=error):
        load_evaluation_cases(dataset_path, corpus)


@pytest.mark.parametrize(
    ("case_index", "facts", "error"),
    [
        (0, [], "an answer requires facts and evidence"),
        (
            2,
            ["A release is retained for a fixed period."],
            "an abstention must have empty",
        ),
    ],
)
def test_rejects_outcome_with_inconsistent_facts(
    tmp_path: Path, case_index: int, facts: list[str], error: str
) -> None:
    corpus = load_corpus(SEED / "corpus")
    dataset = json.loads((SEED / "evaluation.json").read_text(encoding="utf-8"))
    dataset["cases"][case_index]["required_facts"] = facts
    dataset_path = tmp_path / "evaluation.json"
    dataset_path.write_text(json.dumps(dataset), encoding="utf-8")

    with pytest.raises(ValueError, match=error):
        load_evaluation_cases(dataset_path, corpus)
