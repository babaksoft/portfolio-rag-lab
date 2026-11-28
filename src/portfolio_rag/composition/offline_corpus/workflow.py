"""Run committed source selection, summary generation, and staging offline."""

from pathlib import Path
from typing import cast

from pydantic import Field
from workflows import Workflow, step
from workflows.events import Event, StartEvent, StopEvent

from portfolio_rag.application.services import GenerateCorpusSummaryService
from portfolio_rag.infrastructure.corpus.generation import (
    RunSettings,
    SummaryUnit,
    read_snapshot,
    stage_candidate,
)


class _SnapshotSelected(Event):
    """Pinned sources selected for the generation run.

    Attributes:
        snapshots:
            Ordered units paired with the text of their committed source files.
    """

    snapshots: tuple[tuple[SummaryUnit, dict[str, str]], ...] = Field(
        description="Selected units and their committed source text in generation order."
    )


class CorpusGenerationWorkflow(Workflow):
    """Build one candidate and leave promotion to the reviewer."""

    def __init__(
        self,
        service: GenerateCorpusSummaryService,
        repositories: Path,
        units: tuple[SummaryUnit, ...],
        candidates: Path,
        settings: RunSettings,
    ) -> None:
        """Bind the source selection and generation service for one run.

        Args:
            service:
                Application service that generates and validates one summary.
            repositories:
                Common parent of the local source checkouts.
            units:
                Summary units to generate in order.
            candidates:
                Directory where complete candidates are staged for review.
            settings:
                Model and prompt configuration written to the run record.
        """
        super().__init__(timeout=None)
        self._service: GenerateCorpusSummaryService = service
        self._repositories: Path = repositories
        self._units: tuple[SummaryUnit, ...] = units
        self._candidates: Path = candidates
        self._settings: RunSettings = settings

    async def execute(self) -> Path:
        """Return the staged candidate path after a successful workflow run."""
        return cast(Path, await self.run())

    @step
    def select(self, event: StartEvent) -> _SnapshotSelected:
        """Load all selected files before spending on any unit."""
        return _SnapshotSelected(
            snapshots=tuple(
                (unit, read_snapshot(self._repositories, unit)) for unit in self._units
            )
        )

    @step
    def generate(self, event: _SnapshotSelected) -> StopEvent:
        """Generate all units in order and stage the complete candidate."""
        results = tuple(
            (unit, self._service.execute(unit.title, unit.focus, sources))
            for unit, sources in event.snapshots
        )
        return StopEvent(
            result=stage_candidate(self._candidates, self._settings, results)
        )
