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

## 🎯 Domain: Production Incident Triage

Agents receive an alert about a production incident in a simulated microservices architecture and must:
1. **Investigate** — Query logs, metrics, alerts, traces, and service dependencies
2. **Diagnose** — Identify the root cause and affected services
3. **Prescribe** — Recommend remediation steps

### Why This Domain?
- **Novel**: Unlike code review or Q&A tasks, incident triage requires multi-step systems reasoning
- **Realistic**: Based on actual SRE scenarios (OOM crashes, connection leaks, cascading failures)
- **Measurable**: Clear ground truth enables objective scoring across multiple dimensions
- **Scalable difficulty**: From single-service crashes to complex failures with red herrings

## 📊 Task Difficulty Tiers

| Task | Difficulty | Max Steps | Description |
|------|-----------|-----------|-------------|
| `task1_easy` | Easy | 15 | Single service failure with clear error logs |
| `task2_medium` | Medium | 25 | Multi-service cascading failure with correlated logs |
| `task3_hard` | Hard | 35 | Subtle degradation with misleading symptoms and red herrings |

## 🏗️ Architecture

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

## 🚀 Quick Start

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

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/tasks` | List available tasks |
| `POST` | `/reset` | Start a new episode (`{"task_id": "task1_easy"}`) |
| `POST` | `/step` | Take an action and receive `observation`, `reward`, `done`, `info` |
| `GET` | `/state` | Get current environment state |
| `POST` | `/grader` | Grade the episode after diagnosis |
| `GET` | `/baseline` | Baseline agent info |

## 🎮 Agent Actions

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

## 📈 Scoring

| Component | Weight | Method |
|-----------|--------|--------|
| Root Cause Identification | 40% | Service match + keyword overlap |
| Affected Services | 25% | Jaccard similarity |
| Remediation Quality | 20% | Keyword coverage |
| Efficiency Bonus | 15% | Linear decay by step count |

## 🧪 Scenarios

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

## 📜 License

MIT

## ✅ Validation Checklist

- Local smoke test passes (`py smoke_test.py --api-url http://127.0.0.1:7860`)
- Docker container starts and `/health` returns 200
- `inference.py` runs with required env vars and prints `[START]/[STEP]/[END]`
- Baseline runs on all three tasks with reproducible seed values
- Hosted URL (HF Space) passes smoke test using public endpoint

## 👩‍⚖️ Judge / Reviewer Guide

- Judge runbook: `JUDGE.md`
- Hosted deployment checklist: `HOSTED_VALIDATION_CHECKLIST.md`
