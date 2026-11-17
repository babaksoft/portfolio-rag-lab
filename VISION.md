# Portfolio Retrieval Lab — Vision

## Project statement

Portfolio Retrieval Lab is an evaluated progression from deterministic
retrieval to bounded agentic retrieval, with measured quality, latency, cost,
and reliability tradeoffs.

The public product is a portfolio assistant that answers questions about a
curated collection of projects and professional material. The engineering
purpose is broader: demonstrate how retrieval architectures should be selected
from evidence rather than fashion.

## Product goals

- Provide a public, useful, and trustworthy portfolio-question answering
  experience.
- Support multi-turn conversations in which follow-up questions can refer to
  earlier questions, answers, projects, and retrieved evidence.
- Require retrieved evidence for factual claims about the portfolio.
- Expose citations and abstain when evidence is insufficient.
- Compare increasingly capable retrieval configurations on the same evaluation
  dataset.
- Deploy the least complex approach that meets measured quality requirements.
- Remain understandable to a developer learning production AI engineering.

## Conversation requirements

The final assistant is a multi-turn conversational product, not a collection of
isolated single-turn searches. A user must be able to ask natural follow-ups
such as:

- "How did you evaluate it?"
- "Compare that project with the other RAG system."
- "What would you change if latency mattered more?"

Conversation history provides context for resolving references and intent, but
it is not evidence. Every factual portfolio claim still requires current
retrieved evidence and citations. The system should keep conversation identity,
message history, retrieval traces, and cited evidence explicit rather than
hiding them in an unstructured prompt.

Multi-turn behavior must eventually be evaluated with conversation-level cases,
including reference resolution, topic changes, follow-up retrieval, citation
continuity, context limits, and recovery from an incorrect assumption.

## Retrieval progression

### Baseline deterministic RAG

Use a deliberately simple path:

```text
query -> vector retrieval -> generation
```

This configuration establishes the scientific and operational baseline.

### Enhanced deterministic RAG

Add improvements through predictable code paths, as justified by evaluation:

- metadata filtering and project-aware retrieval;
- lexical/vector hybrid search;
- query rewriting and retrieval routing;
- reranking and context deduplication;
- evidence-sufficiency checks and abstention.

### Bounded agentic retrieval

Give one agent a small, read-only retrieval toolset. It may decompose questions,
select a retrieval strategy, assess evidence, and retry within strict time,
token, iteration, and tool limits. It must terminate deterministically, expose
tool traces, and abstain without sufficient evidence.

### Production routing

The eventual router selects among:

- clarification;
- rejection or capability explanation;
- enhanced deterministic retrieval;
- bounded agentic retrieval.

The non-retrieval routes never make factual portfolio claims. Agentic behavior
is used only where evaluation demonstrates that its additional cost is earned.

## Evaluation principles

All retrieval configurations use the same versioned evaluation dataset and are
compared on:

- retrieval quality, including recall@K, MRR, and nDCG;
- answer correctness and required-fact coverage;
- faithfulness and citation precision/recall;
- abstention and routing accuracy;
- tool selection and argument accuracy where applicable;
- model calls, searches, tokens, latency, and estimated cost;
- timeout, loop, tool, retrieval, and generation failure rates.

## Architectural direction

The initial product uses:

- Python 3.12 and `uv`;
- Streamlit as a replaceable browser-facing UI;
- FastAPI for API and application boundaries;
- an explicit API client between Streamlit and FastAPI;
- PostgreSQL with pgvector for persistence and retrieval;
- AWS ECS/Fargate for application runtime;
- Terraform for infrastructure;
- GitHub Actions with AWS OIDC for CI/CD;
- Cognito federated with Google for authentication;
- Route 53, ACM, an Application Load Balancer, ECR, Secrets Manager, and
  CloudWatch.

Streamlit and FastAPI initially run as two containers in one ECS task. The
system is production-shaped but learning-sized: one service, one task, one
production environment, and a single-AZ-sized initial footprint where
appropriate. Components may be separated later when measured operational needs
justify it.

## Engineering principles

- Build live vertical slices: learn, select, implement, evaluate, and deploy.
- Keep domain and retrieval logic independent of UI and orchestration
  frameworks.
- Prefer explicit application-owned interfaces over framework-shaped domain
  models.
- Keep changes small, coherent, independently verifiable, and reviewable.
- Treat stages as outcomes and slices as implementation/review units.
- Record enduring decisions in concise ADRs.
- Reuse donor-repository code only after reviewing and adapting the smallest
  useful unit; do not inherit its architecture wholesale.

## Explicit non-goals for early releases

- multiple cooperating agents;
- arbitrary code execution by models;
- automated source synchronization;
- multiple speculative retrieval strategies at once;
- sophisticated administrative dashboards;
- Kubernetes, service meshes, multi-account AWS topology, or complex deployment
  systems;
- high-availability spending before it is justified.

## Success condition

The project succeeds when it can publicly demonstrate, with reproducible
evaluation evidence, where deterministic retrieval is sufficient, where
bounded agentic retrieval improves outcomes, and what each improvement costs in
latency, money, and operational complexity.

