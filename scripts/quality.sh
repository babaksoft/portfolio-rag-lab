#!/usr/bin/env bash

set -euo pipefail

unset VIRTUAL_ENV

uv sync --locked
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
