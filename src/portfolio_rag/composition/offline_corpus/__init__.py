"""Public composition for the offline corpus command."""

from portfolio_rag.composition.offline_corpus.settings import load_corpus_openai_key
from portfolio_rag.composition.offline_corpus.workflow import CorpusGenerationWorkflow

__all__ = ["CorpusGenerationWorkflow", "load_corpus_openai_key"]
