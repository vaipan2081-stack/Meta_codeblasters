---
title: OpenEnv Incident Triage
emoji: 🚨
colorFrom: red
colorTo: blue
sdk: docker
app_port: 7860
---

# Incident Triage Environment — OpenEnv Hackathon Submission

A production incident triage environment for evaluating LLM agents' ability to diagnose complex distributed system failures.

## Domain: Production Incident Triage

Agents receive an alert about a production incident in a simulated microservices architecture and must:
1. **Investigate** — Query logs, metrics, alerts, traces, and service dependencies
2. **Diagnose** — Identify the root cause and affected services
3. **Prescribe** — Recommend remediation steps

### Why This Domain?
- **Novel**: Unlike code review or Q&A tasks, incident triage requires multi-step systems reasoning
- **Realistic**: Based on actual SRE scenarios (OOM crashes, connection leaks, cascading failures)
- **Measurable**: Clear ground truth enables objective scoring across multiple dimensions
- **Scalable difficulty**: From single-service crashes to complex failures with red herrings

##  Task Difficulty Tiers

| Task | Difficulty | Max Steps | Description |
|------|-----------|-----------|-------------|
| `task1_easy` | Easy | 15 | Single service failure with clear error logs |
| `task2_medium` | Medium | 25 | Multi-service cascading failure with correlated logs |
| `task3_hard` | Hard | 35 | Subtle degradation with misleading symptoms and red herrings |

## Architecture

```
├── app/
│   ├── main.py           # FastAPI endpoints
│   ├── models.py          # Pydantic request/response models
│   └── environment.py     # Core state machine
├── data/
│   └── scenarios/
│       └── scenarios.py   # Pre-built incident scenarios with ground truth
├── graders/
│   └── grader.py          # Standalone grading module
├── baseline.py            # GPT-4o baseline agent
├── smoke_test.py          # Endpoint validation tests
├── openenv.yaml           # Environment configuration
├── Dockerfile             # HuggingFace Spaces deployment
└── requirements.txt
```

##  Quick Start

### Local Development

```bash
# Install dependencies
py -m pip install -r requirements.txt

# Start the server
py -m uvicorn app.main:app --host 0.0.0.0 --port 7860 --reload

# Run smoke tests (in another terminal)
py smoke_test.py --api-url http://127.0.0.1:7860
```

### Docker

```bash
docker build -t incident-triage-env .
docker run -p 7860:7860 incident-triage-env
```

### Run Baseline Agent

```bash
# Requires OPENAI_API_KEY environment variable
py baseline.py --task task1_easy
py baseline.py --task task2_medium --model gpt-4o-mini
py baseline.py --task task3_hard
```

### Run Submission Inference Script

```bash
# Required for model calls
set API_BASE_URL=https://your-llm-endpoint/v1
set MODEL_NAME=your-model-name
set HF_TOKEN=your-token

# Optional, defaults to local server
set ENV_URL=http://127.0.0.1:7860
set TASK_NAME=task1_easy

py inference.py
```

`inference.py` emits structured logs in `[START]`, `[STEP]`, `[END]` format.

### Run Human Demo UI (Gradio)

```bash
# Optional ENV_URL if API is remote
set ENV_URL=http://127.0.0.1:7860

py app_ui.py
```

The UI starts on `http://127.0.0.1:7861` and supports reset, step actions, state inspection, and grading.

## Baseline Performance

The `gpt-4o-mini` baseline agent has been benchmarked with the following deterministic scores (fixed seed):

| Task | Score | Component Breakdown |
|------|-------|---------------------|
| `task1_easy` | **0.9100** | Root Cause: 0.40, Affected: 0.25, Remediation: 0.16, Efficiency: 0.10 |
| `task2_medium` | **0.7600** | Root Cause: 0.40, Affected: 0.15, Remediation: 0.13, Efficiency: 0.08 |
| `task3_hard` | **0.4850** | Root Cause: 0.20, Affected: 0.10, Remediation: 0.12, Efficiency: 0.065 |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/tasks` | List available tasks |
| `POST` | `/reset` | Start a new episode (`{"task_id": "task1_easy"}`) |
| `POST` | `/step` | Take an action and receive `observation`, `reward`, `done`, `info` |
| `GET` | `/state` | Get current environment state |
| `POST` | `/grader` | Grade the episode after diagnosis |
| `GET` | `/baseline` | Baseline agent info |

## Agent Actions

| Action | Parameters | Description |
|--------|-----------|-------------|
| `list_services` | — | List all services in scope |
| `check_alerts` | `service?`, `severity?` | View active alerts |
| `query_logs` | `service` (required), `level?`, `keyword?` | Query service logs |
| `query_metrics` | `service` (required), `metric_name?` | Query metrics |
| `get_service_info` | `service` (required) | Detailed service info |
| `check_dependencies` | `service` (required) | Dependency graph |
| `query_traces` | `trace_id?`, `service?` | Distributed traces |
| `submit_diagnosis` | `root_cause`, `root_cause_service`, `affected_services`, `remediation` | Submit diagnosis |

##  Scoring

The environment uses an advanced multi-dimensional grading system to ensure high-fidelity evaluation (USPs):

| Component | Weight | Metric | Description |
| :--- | :--- | :--- | :--- |
| **Root Cause ID** | 30% | Keyword Match + SVC | Identifying the core issue and origin service. |
| **Affected Services** | 20% | **F1 Score** | Balancing precision and recall of downstream impacts (USP #1). |
| **Remediation** | 20% | Keyword Coverage | Effectiveness of the proposed fix actions. |
| **Reasoning Trace** | 15% | **Rule-based Audit** | Verifying the agent actually investigated the root cause logs/metrics (USP #2). |
| **Efficiency** | 15% | Linear Decay | Penalizing excessive steps and redundant queries. |

### Advanced Features (USPs)
1.  **Adversarial Precision Grader (USP #1):** Unlike standard Jaccard similarity, we use a strict **F1 score** to penalize "hallucinated" affected services (False Positives) and missed ones (False Negatives). The grader output includes a diff showing exactly what the agent got wrong.
2.  **Reasoning Trace Scorer (USP #2):** Prevents agents from "guessing" the answer. The grader audits the action history to ensure the agent targeted the correct service's logs and metrics during the investigation window before submitting their final answer.

## Baseline Performance

The `gpt-4o-mini` baseline agent has been benchmarked with the following deterministic scores (fixed seed). *Note: Scores updated following the implementation of advanced USPs.*

| Task | Score | Component Breakdown (RC, Aff, Rem, Trace, Eff) |
| :--- | :--- | :--- |
| `task1_easy` | **0.9250** | 0.30, 0.20, 0.18, 0.15, 0.095 |
| `task2_medium` | **0.7800** | 0.30, 0.15, 0.13, 0.12, 0.08 |
| `task3_hard` | **0.5150** | 0.20, 0.10, 0.10, 0.05, 0.065 |

## Scenarios

### Easy: OOM Database Crash
PostgreSQL OOM on `order-db` → cascading 503s on `order-service`. Clear error trail.

### Easy: Redis Cache Failure
Redis segfault → `auth-service` session fallback to DB → authentication latency spike.

### Medium: Kafka Broker Failure
Broker node loss → partition leader election storm → event processing failures across 3 services.

### Medium: Connection Pool Leak
Slow leak in `payment-service` refund handler → pool exhaustion → payment failures. Stripe latency as red herring.

### Hard: JVM Memory Leak with GC Storm
Subtle memory leak → escalating GC pauses → Kafka heartbeat failures + DB connection resets. Network blip and Redis evictions as red herrings.

##  License

MIT

## Validation Checklist

- Local smoke test passes (`py smoke_test.py --api-url http://127.0.0.1:7860`)
- Docker container starts and `/health` returns 200
- `inference.py` runs with required env vars and prints `[START]/[STEP]/[END]`
- Baseline runs on all three tasks with reproducible seed values
- Hosted URL (HF Space) passes smoke test using public endpoint

## 👩‍⚖️ Judge / Reviewer Guide

- Judge runbook: `JUDGE.md`
- Hosted deployment checklist: `HOSTED_VALIDATION_CHECKLIST.md`
