"""Exercise offline generation and promotion with committed source fixtures."""

import json
import subprocess
from pathlib import Path

import pytest

from portfolio_rag.application.services import (
    PROMPT_REVISION,
    GenerateCorpusSummaryService,
    GenerationResponse,
)
from portfolio_rag.composition.offline_corpus import CorpusGenerationWorkflow
from portfolio_rag.infrastructure.corpus import load_corpus
from portfolio_rag.infrastructure.corpus.generation import (
    RunSettings,
    SummaryUnit,
    promote_candidate,
)

_SEED = Path(__file__).resolve().parents[2] / "data/portfolio/seed-v1/corpus"


class _FakeGenerator:
    """Generate a predictable draft and capture which sources were submitted.

    Attributes:
        bad_reference:
            Whether to cite a file outside the input selection.
        payloads:
            Source payloads received in request order.
    """

    def __init__(self, *, bad_reference: bool = False) -> None:
        """Configure whether the draft cites an invalid path."""
        self.bad_reference = bad_reference
        self.payloads: list[str] = []

    def generate(self, instructions: str, source_payload: str) -> GenerationResponse:
        """Return synthetic usage and a draft referencing the first selected path."""
        self.payloads.append(source_payload)
        path = next(iter(json.loads(source_payload)["files"]))
        return GenerationResponse(
            text=json.dumps(
                {
                    "implemented": "Documents the selected donor decision.",
                    "planned": "",
                    "source_files": ["unselected.md" if self.bad_reference else path],
                }
            ),
            model="fake",
            input_tokens=10,
            output_tokens=5,
        )


def _git(repository: Path, *args: str) -> str:
    """Run a Git command in the disposable fixture repository."""
    return subprocess.run(
        ["git", "-C", str(repository), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


@pytest.fixture
def seed_units(tmp_path: Path) -> tuple[SummaryUnit, ...]:
    """Commit seed documents to a temporary Git repository and select them by hash."""
    repository = tmp_path / "fixture"
    repository.mkdir()
    _git(repository, "init", "-q")
    seed = load_corpus(_SEED)
    for source, document in zip(seed.manifest.sources, seed.documents, strict=True):
        (repository / f"{source.source_id}.md").write_text(document, encoding="utf-8")
    _git(repository, "add", ".")
    _git(
        repository,
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.test",
        "-c",
        "commit.gpgsign=false",
        "commit",
        "-qm",
        "seed",
    )
    commit = _git(repository, "rev-parse", "HEAD")
    return tuple(
        SummaryUnit(
            source_id=source.source_id,
            commit=commit,
            repository="fixture",
            origin_url=f"https://example.test/fixture/tree/{commit}",
            title=source.source_id,
            focus="Summarize the recorded donor decision.",
            files=(f"{source.source_id}.md",),
        )
        for source in seed.manifest.sources
    )


def _workflow(
    tmp_path: Path, seed_units: tuple[SummaryUnit, ...], generator: _FakeGenerator
) -> CorpusGenerationWorkflow:
    """Configure the offline workflow with a fake model and temporary paths."""
    return CorpusGenerationWorkflow(
        GenerateCorpusSummaryService(generator),
        tmp_path,
        seed_units,
        tmp_path / "candidates",
        RunSettings(
            model="fake",
            reasoning="none",
            max_output_tokens=512,
            prompt_revision=PROMPT_REVISION,
        ),
    )


def _evaluation(path: Path, version: str, source_id: str) -> None:
    """Write an evaluation fixture that cites the expected draft line."""
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "corpus_version": version,
                "cases": [
                    {
                        "case_id": "seed-decision",
                        "question": "What does the source document?",
                        "expected_outcome": "answer",
                        "required_facts": ["A donor decision."],
                        "expected_evidence": [
                            {"source_id": source_id, "start_line": 5, "end_line": 5}
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ["asyncio"])
async def test_generation_and_promotion_preserve_prior_release(
    tmp_path: Path, seed_units: tuple[SummaryUnit, ...]
) -> None:
    """Publish from committed inputs and reject a tampered candidate on re-promotion."""
    generator = _FakeGenerator()
    source_path = tmp_path / "fixture" / seed_units[0].files[0]
    source_path.write_text("Uncommitted edit", encoding="utf-8")

    candidate = await _workflow(tmp_path, seed_units, generator).execute()
    corpus = load_corpus(candidate / "corpus")
    evaluation = tmp_path / "evaluation.json"
    _evaluation(evaluation, corpus.version, seed_units[0].source_id)
    releases = tmp_path / "releases"
    released = promote_candidate(candidate, evaluation, releases, corpus.version)
    repeated = promote_candidate(candidate, evaluation, releases, corpus.version)
    (candidate / "corpus" / seed_units[0].files[0]).write_text(
        "Tampered", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="content hash mismatch"):
        promote_candidate(candidate, evaluation, releases, corpus.version)

    assert "Uncommitted edit" not in generator.payloads[0]
    assert len(corpus.documents) == 2
    assert repeated == released == releases / corpus.version
    assert load_corpus(released / "corpus") == corpus
    report = json.loads((released / "run.json").read_bytes())
    assert report["units"][0]["selection"]["commit"] == seed_units[0].commit
    assert report["units"][0]["output_tokens"] == 5


@pytest.mark.anyio
@pytest.mark.parametrize("anyio_backend", ["asyncio"])
async def test_generation_rejects_output_with_unselected_evidence(
    tmp_path: Path, seed_units: tuple[SummaryUnit, ...]
) -> None:
    """Reject a draft with an unsupported file reference before staging."""
    generator = _FakeGenerator(bad_reference=True)
    with pytest.raises(ValueError, match="file outside the summary selection"):
        await _workflow(tmp_path, seed_units, generator).execute()

    assert not (tmp_path / "candidates").exists()
