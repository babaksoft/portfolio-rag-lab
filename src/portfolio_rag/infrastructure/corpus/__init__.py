"""Public interface for the local portfolio corpus and case formats."""

from portfolio_rag.infrastructure.corpus.loading import (
    LoadedCorpus,
    load_corpus,
    load_evaluation_cases,
)
from portfolio_rag.infrastructure.corpus.models import (
    CitationLocation,
    CorpusManifest,
    CorpusSource,
    EvaluationCase,
    EvaluationDataset,
)

__all__ = [
    "CitationLocation",
    "CorpusManifest",
    "CorpusSource",
    "EvaluationCase",
    "EvaluationDataset",
    "LoadedCorpus",
    "load_corpus",
    "load_evaluation_cases",
]
