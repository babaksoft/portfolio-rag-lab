# ADR-0003: Co-locate the UI and API in one ECS task

- **Status:** Accepted
- **Date:** 2026-11-17

## Context

The initial deployment must exercise real container, networking, health,
logging, secret, and database boundaries while remaining inexpensive and easy
to operate as a learning-sized portfolio system. Streamlit and FastAPI need
different processes, but current traffic and availability requirements do not
justify independently operated services.

## Decision

Run one ECS/Fargate service with desired task count one. Each task contains a
Streamlit UI container and a FastAPI backend container. The containers
communicate over the task-local network through the explicit API client and are
deployed, restarted, and scaled as one unit. Use an Application Load Balancer as
the public entry point and keep PostgreSQL outside the task as a managed
dependency.

## Consequences

- The system exercises production-shaped boundaries with one service to deploy
  and observe.
- Task-local API traffic is simple and does not require service discovery.
- UI and API share a failure, deployment, and scaling unit.
- A single task provides no application-level redundancy; failures and some
  deployments can interrupt service.
- UI and API resources cannot be scaled independently.
- Splitting services later requires deployment and networking work but does not
  require moving product rules because source boundaries are already explicit.

## Alternatives considered

- Run Streamlit and FastAPI in one container. This weakens process ownership,
  health, and resource boundaries without meaningful operational savings.
- Deploy separate ECS services immediately. This enables independent scaling
  and failures but adds service discovery, deployment, and operating cost before
  evidence justifies it.
- Start with multiple tasks and a highly available database. This reduces
  outages but adds cost before the project has meaningful traffic or an
  availability objective.
