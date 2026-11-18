# Portfolio Retrieval Lab

An evaluated progression from deterministic retrieval to bounded agentic
retrieval, with measured quality, latency, cost, and reliability tradeoffs.

The first Phase 0 slice provides a local Streamlit-to-FastAPI walking skeleton.
See [`VISION.md`](VISION.md) for the project charter and [`PLAN.md`](PLAN.md) for
the staged delivery plan. The current architecture is described in
[`DESIGN.md`](DESIGN.md), with consequential decisions indexed in
[`docs/adr/`](docs/adr/README.md).

## Local development

Install Python 3.12 and [`uv`](https://docs.astral.sh/uv/), then synchronize the
locked environment:

```sh
uv sync --locked
```

Configuration has safe local defaults. To customize them, copy
`.env.example` to `.env` and edit the local file.

Start the API in one terminal:

```sh
uv run uvicorn portfolio_rag.api:app --host 127.0.0.1 --port 8000
```

Start the UI in another terminal:

```sh
uv run streamlit run src/portfolio_rag/ui/app.py \
  --server.address 127.0.0.1 \
  --server.port 8501
```

Open <http://127.0.0.1:8501> and submit a message. The response is deliberately
labeled as a non-factual placeholder. API liveness and readiness are available
at `/health/live` and `/health/ready`; Streamlit exposes its process health at
`/_stcore/health`.

Run the complete local check suite with:

```sh
./scripts/quality.sh
```

The command synchronizes the locked environment, checks formatting and linting
with Ruff, checks types with mypy, and runs the pytest suite.

Pull requests run the same checks in GitHub Actions. Repository automation,
dependency maintenance, and the planned AWS OIDC trust boundary are documented
in [`docs/github-operations.md`](docs/github-operations.md).

## License

This project is available under the [MIT License](LICENSE).
