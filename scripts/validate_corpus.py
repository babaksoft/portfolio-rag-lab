"""Validate a portfolio corpus and its hand-authored evaluation cases."""

import argparse
from pathlib import Path

from portfolio_rag.infrastructure.corpus import load_corpus, load_evaluation_cases


def main() -> None:
    """Check the supplied artifacts and report their corpus version."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus_directory", type=Path)
    parser.add_argument("evaluation_dataset", type=Path)
    args = parser.parse_args()

    try:
        corpus = load_corpus(args.corpus_directory)
        dataset = load_evaluation_cases(args.evaluation_dataset, corpus)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Validation failed: {exc}\n")
    print(
        f"Validated {len(corpus.documents)} sources and {len(dataset.cases)} cases "
        f"for corpus {corpus.version}."
    )


if __name__ == "__main__":
    main()
