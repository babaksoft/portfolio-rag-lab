"""Inspect pinned corpus inputs, generate a candidate, or promote a reviewed version."""

import argparse
import asyncio
import sqlite3
from pathlib import Path
from typing import cast

from openai import OpenAI, OpenAIError
from workflows.errors import WorkflowRuntimeError

from portfolio_rag.application.services import (
    PROMPT_REVISION,
    GenerateCorpusSummaryService,
)
from portfolio_rag.composition.offline_corpus import (
    CorpusGenerationWorkflow,
    load_corpus_openai_key,
)
from portfolio_rag.infrastructure.corpus import load_corpus
from portfolio_rag.infrastructure.corpus.generation import (
    RunSettings,
    SummaryUnit,
    load_summary_units,
    promote_candidate,
    read_snapshot,
)
from portfolio_rag.infrastructure.db import DbCorpusBudget
from portfolio_rag.infrastructure.providers import (
    MAX_OUTPUT_TOKENS,
    MINI_MODEL,
    SOL_MODEL,
    CorpusModel,
    OpenAICorpusGenerator,
    reasoning_effort,
)

_ROOT = Path(__file__).resolve().parents[1]
_WORK = _ROOT / ".corpus-work"


def _parser() -> argparse.ArgumentParser:
    """Define the offline inspection, generation and promotion commands."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser(
        "inspect", help="Verify the selected Git files locally"
    )
    generate = commands.add_parser(
        "generate", help="Stage a new candidate using OpenAI"
    )
    for command in (inspect, generate):
        command.add_argument(
            "--selection",
            type=Path,
            default=_ROOT / "data/portfolio/showcase-sources.json",
        )
        command.add_argument("--repositories", type=Path, default=_ROOT.parent)
        command.add_argument("--unit", help="Select one source ID")
    generate.add_argument(
        "--model", choices=(MINI_MODEL, SOL_MODEL), default=MINI_MODEL
    )
    generate.add_argument(
        "--pilot", action="store_true", help="Use the USD 2 pilot allowance"
    )
    generate.add_argument(
        "--confirm-source-review",
        action="store_true",
        required=True,
        help="Confirm that the selected committed files were reviewed for API submission",
    )
    promote = commands.add_parser(
        "promote", help="Publish the exact reviewed corpus version"
    )
    promote.add_argument("candidate", type=Path)
    promote.add_argument("evaluation", type=Path)
    promote.add_argument("--version", required=True)
    return parser


def _selected_units(selection: Path, source_id: str | None) -> tuple[SummaryUnit, ...]:
    """Resolve an optional unit filter against the configured selection."""
    units = load_summary_units(selection)
    selected = tuple(
        unit for unit in units if source_id is None or unit.source_id == source_id
    )
    if not selected:
        raise ValueError("unknown summary unit")
    return selected


async def _generate(arguments: argparse.Namespace) -> Path:
    """Run the workflow with the fixed standard OpenAI endpoint and durable budget."""
    units = _selected_units(arguments.selection, arguments.unit)
    if arguments.pilot and len(units) != 1:
        raise ValueError("a pilot requires one summary unit")

    model = cast(CorpusModel, arguments.model)
    api_key = load_corpus_openai_key(_ROOT / ".env")
    with OpenAI(
        api_key=api_key.get_secret_value(),
        base_url="https://api.openai.com/v1",
        max_retries=0,
        timeout=120.0,
    ) as client:
        workflow = CorpusGenerationWorkflow(
            GenerateCorpusSummaryService(
                OpenAICorpusGenerator(
                    client,
                    model,
                    DbCorpusBudget(_WORK / "budget.sqlite"),
                    pilot=arguments.pilot,
                ),
            ),
            arguments.repositories,
            units,
            _WORK / "candidates",
            RunSettings(
                model=model,
                reasoning=reasoning_effort(model),
                max_output_tokens=MAX_OUTPUT_TOKENS,
                prompt_revision=PROMPT_REVISION,
            ),
        )
        return await workflow.execute()


def _inspect(arguments: argparse.Namespace) -> None:
    """Print the verified file list and local input sizes."""
    for unit in _selected_units(arguments.selection, arguments.unit):
        print(f"{unit.source_id} {unit.commit}")
        for path, content in read_snapshot(arguments.repositories, unit).items():
            print(f"  {path} ({len(content.encode('utf-8')):,} bytes)")


def main() -> None:
    """Dispatch a local corpus operation and report safe diagnostics."""
    parser = _parser()
    arguments = parser.parse_args()
    try:
        if arguments.command == "inspect":
            _inspect(arguments)
        elif arguments.command == "generate":
            candidate = asyncio.run(_generate(arguments))
            print(
                f"Candidate {load_corpus(candidate / 'corpus').version} at {candidate}"
            )
        else:
            release = promote_candidate(
                arguments.candidate,
                arguments.evaluation,
                _ROOT / "data/portfolio/releases",
                arguments.version,
            )
            print(f"Approved release at {release}")
    except (OSError, ValueError, sqlite3.Error) as exc:
        parser.exit(1, f"Corpus operation failed: {exc}\n")
    except OpenAIError:
        parser.exit(1, "Could not initialize OpenAI.\n")
    except WorkflowRuntimeError as exc:
        detail = (
            str(exc.__cause__)
            if isinstance(exc.__cause__, ValueError)
            else "workflow failed"
        )
        parser.exit(1, f"Corpus generation failed: {detail}\n")


if __name__ == "__main__":
    main()
