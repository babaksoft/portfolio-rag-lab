# ADR-0006: Instrument RAG and monitor application health

- **Status:** Accepted
- **Date:** 2026-11-27

## Context

Phase 0 has correlated JSON logs and CloudWatch infrastructure alarms. Phase 1
introduces paid model calls and a retrieval path whose failures and latency
need to be visible even when the infrastructure appears healthy. The donor
includes opt-in LlamaIndex tracing, and its custom spans require review against
this project's content-handling policy before reuse.

## Decision

Use self-hosted Phoenix for request traces. Export via OpenTelemetry and use
OpenInference attributes for LlamaIndex and explicit application spans. Add
instrumentation as retrieval and generation land. Capture timings, outcomes,
bounded error categories, model identifiers, and token usage when available.
Correlate traces with the existing request logs. Exclude prompts, answers,
retrieved text, identity attributes, and credentials by default, including in
automatically instrumented spans.

Collect application metrics with Prometheus and use Grafana for dashboards and
application alerts. Start with one dashboard for request volume, error rate,
request latency, and provider timeouts. Keep metric labels bounded and use
Grafana alert rules once the baseline provides evidence for thresholds. Keep
CloudWatch and SNS as the existing infrastructure alarm path.

Verify locally first and target live traces and collected metrics before public
RAG availability. A short, supervised reviewer pilot can provide the evidence
to finish the live setup. Choose the Prometheus and Grafana hosting model and
the Phoenix topology using expected usage, retention, cost, and upkeep. Keep
telemetry access restricted and keep exporter failures out of the serving path.

## Consequences

The baseline can be diagnosed per request and measured across requests.
Operating the stack adds compute, storage, access management, and maintenance.
Validate representative exported records before live use. Revisit the live
hosting arrangement when measured cost, retention, or maintenance warrants it.

## Alternatives considered

- CloudWatch logs and existing alarms cover the walking skeleton and support
  infrastructure response. RAG-specific traces and aggregate metrics support
  finding provider, retrieval, and generation problems.
- AWS-managed Prometheus and Grafana reduce the services to operate. Compare
  their usage and workspace charges with self-hosted compute and storage when
  choosing the live topology.
