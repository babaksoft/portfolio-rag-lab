# Architecture Decision Records

ADRs capture consequential architectural choices and their tradeoffs. They do
not replace the current architecture in `DESIGN.md` or implementation detail in
stage records.

## Index

| ADR | Decision | Status | Date |
| --- | --- | --- | --- |
| [0001](0001-modular-application-shape.md) | Adopt a modular application with explicit UI and API boundaries | Accepted | 2026-11-17 |
| [0002](0002-framework-neutral-domain-boundary.md) | Keep the domain boundary framework-neutral | Accepted | 2026-11-17 |
| [0003](0003-co-locate-ui-and-api-in-one-ecs-task.md) | Co-locate the UI and API in one ECS task | Accepted | 2026-11-17 |
| [0004](0004-verify-alb-and-cognito-credentials-in-api.md) | Verify ALB and Cognito credentials in FastAPI | Accepted | 2026-11-22 |
| [0005](0005-use-llamaindex-for-baseline-rag.md) | Use LlamaIndex for baseline RAG and offline corpus generation | Proposed | 2026-11-27 |
| [0006](0006-instrument-rag-and-monitor-application-health.md) | Instrument RAG and monitor application health | Proposed | 2026-11-27 |
| [0007](0007-own-rag-evaluation-and-score-with-ragas.md) | Own RAG evaluation and score with Ragas | Proposed | 2026-11-27 |

## Convention

Copy [the template](template.md), assign the next four-digit number, and use a
short kebab-case filename. An ADR moves from `Proposed` to `Accepted` or
`Rejected`; an accepted ADR may later become `Deprecated` or `Superseded by
ADR-NNNN`. Do not rewrite an accepted decision to change its meaning. Record a
replacement in a new ADR and update this index and the earlier ADR's status.
