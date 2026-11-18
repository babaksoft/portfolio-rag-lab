# Portfolio Retrieval Lab

An evaluated progression from deterministic retrieval to bounded agentic
retrieval, with measured quality, latency, cost, and reliability tradeoffs.

Repository bootstrap is complete, and Phase 0 is planned for implementation.
See [`VISION.md`](VISION.md) for the project charter and [`PLAN.md`](PLAN.md) for
the staged delivery plan. Current architecture is described in
[`DESIGN.md`](DESIGN.md), with consequential decisions indexed in
[`docs/adr/`](docs/adr/README.md).

## Local development

Install Python 3.12 and [`uv`](https://docs.astral.sh/uv/), then run the complete
local check suite:

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
