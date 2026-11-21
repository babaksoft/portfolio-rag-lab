# Portfolio Retrieval Lab

An evaluated progression from deterministic retrieval to bounded agentic
retrieval, with measured quality, latency, cost, and reliability tradeoffs.

The first Phase 0 slices provide a local Streamlit-to-FastAPI walking skeleton
backed by PostgreSQL/pgvector. It runs either as native development processes
or as separate containers. See [`VISION.md`](VISION.md) for the project charter
and [`PLAN.md`](PLAN.md) for the staged delivery plan. The current architecture
is described in [`DESIGN.md`](DESIGN.md), with consequential decisions indexed
in [`docs/adr/`](docs/adr/README.md).

## Local development

Install Python 3.12 and [`uv`](https://docs.astral.sh/uv/), then synchronize the
locked environment:

```sh
uv sync --locked
```

Configuration has safe local defaults. To customize them, copy
`.env.example` to `.env` and edit the local file.

Start the local PostgreSQL/pgvector dependency and apply all migrations before
starting native application processes:

```sh
docker compose up -d --wait db
uv run alembic upgrade head
```

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

Install Docker with the Compose plugin, then build and start the UI, API, and
database. The one-shot migration container must complete before the API starts:

```sh
docker compose up --build --wait
```

Open <http://127.0.0.1:8501>. The UI container reaches the API at its Compose
service address, matching the task-local configuration boundary planned for
ECS. The API is also exposed locally at <http://127.0.0.1:8000> for health and
boundary checks. PostgreSQL is exposed at `127.0.0.1:5432` for native tools.
All published ports bind only to the loopback interface. If a default port is
occupied, set `PORTFOLIO_RAG_DATABASE_PORT`, `PORTFOLIO_RAG_API_PORT`, or
`PORTFOLIO_RAG_UI_PORT` for the Compose command.

Alembic migrations live in the repository-root `alembic/` directory. Common
migration operations are:

```sh
uv run alembic current
uv run alembic revision -m "describe the schema change"
uv run alembic upgrade head
uv run alembic downgrade -1
```

Review generated revisions before applying them. Application startup never
changes schema. To run the PostgreSQL integration tests against the local
Compose database after migration:

```sh
PORTFOLIO_RAG_TEST_DATABASE_URL=postgresql+asyncpg://portfolio_rag:portfolio_rag@127.0.0.1:5432/portfolio_rag \
  uv run pytest -m integration
```

Stop the runtime within its configured grace period with:

```sh
docker compose down --timeout 10
```

To build, start, health-check, exercise the UI container's typed API client,
verify both application processes run as non-root users, and stop the runtime,
run:

```sh
uv run python scripts/container_smoke.py
```

Pull requests run the same checks in GitHub Actions. Repository automation,
dependency maintenance, and the planned AWS OIDC trust boundary are documented
in [`docs/github-operations.md`](docs/github-operations.md).

## AWS deployment

The Terraform-managed Phase 0 AWS deployment is under
[`terraform/`](terraform/). Its runbook documents state bootstrap, immutable
image publishing, the controlled migration task, staged initial deployment,
smoke testing, rollback, cost and recovery assumptions, and every explicit
apply/destroy approval gate. Run its local formatting and validation checks
with:

```sh
./scripts/terraform_quality.sh
```

No Terraform apply is part of the repository quality suite or permitted without
explicit approval.

## License

This project is available under the [MIT License](LICENSE).
