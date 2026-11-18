# Portfolio Retrieval Lab

An evaluated progression from deterministic retrieval to bounded agentic
retrieval, with measured quality, latency, cost, and reliability tradeoffs.

The first Phase 0 slices provide a local Streamlit-to-FastAPI walking skeleton
that runs either as native development processes or as separate containers.
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

## Containerized runtime

Install Docker with the Compose plugin, then build and start both containers:

```sh
docker compose up --build --wait
```

Open <http://127.0.0.1:8501>. The UI container reaches the API at its Compose
service address, matching the task-local configuration boundary planned for
ECS. The API is also exposed locally at <http://127.0.0.1:8000> for health and
boundary checks. Both published ports bind only to the loopback interface.

Stop the runtime within its configured grace period with:

```sh
docker compose down --timeout 10
```

To build, start, health-check, exercise the UI container's typed API client,
verify both processes run as non-root users, and stop the runtime, run:

```sh
uv run python scripts/container_smoke.py
```

Pull requests run the same checks in GitHub Actions. Repository automation,
dependency maintenance, and the planned AWS OIDC trust boundary are documented
in [`docs/github-operations.md`](docs/github-operations.md).

## License

This project is available under the [MIT License](LICENSE).
