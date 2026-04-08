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

### LM Studio (OpenAI-Compatible) Local Testing

Using LM Studio is acceptable for local development/testing as long as it exposes OpenAI-compatible APIs.

Verified endpoints:
- `GET /v1/models`
- `POST /v1/chat/completions`

Verified local models (example):
- `qwen/qwen3.5-9b`
- `dolphin-2.9.4-llama3.1-8b`

Windows example for local run with LM Studio + Qwen:

```bash
set ENV_URL=http://127.0.0.1:7860
set API_BASE_URL=http://localhost:1234/v1
set MODEL_NAME=qwen/qwen3.5-9b
set OPENAI_API_KEY=lm-studio
set MAX_STEPS=4
py inference.py
```

Windows example for local run with LM Studio + Dolphin:

```bash
set ENV_URL=http://127.0.0.1:7860
set API_BASE_URL=http://localhost:1234/v1
set MODEL_NAME=dolphin-2.9.4-llama3.1-8b
set OPENAI_API_KEY=lm-studio
set MAX_STEPS=4
py inference.py
```

Observed test output pattern:
- `[START] task=task1_easy ...`
- `[STEP] ...` (multiple steps)
- `[END] success=false steps=4 score=0.0000 rewards=[0.12, 0.12, 0.12, 0.1]`

Observed Dolphin run output:
- `[START] task=task1_easy env=incident-triage model=dolphin-2.9.4-llama3.1-8b`
- `[STEP] step=1 action=list_services reward=0.1200 done=false error=none`
- `[STEP] step=2 action=check_alerts reward=0.1200 done=false error=none`
- `[STEP] step=3 action=query_logs reward=0.0300 done=false error=none`
- `[STEP] step=4 action=query_metrics reward=0.0000 done=false error=none`
- `[END] success=false steps=4 score=0.0000 rewards=[0.12, 0.12, 0.03, 0.0]`

Note:
- If LM Studio unloads the model during a run, the API may return `400 Model unloaded.`. Reload the model in LM Studio and rerun.

### Run Human Demo UI (Gradio)

```bash
# Start backend first (required)
py -m uvicorn app.main:app --host 0.0.0.0 --port 7860

# Optional ENV_URL if API is remote
set ENV_URL=http://127.0.0.1:7860

py app_ui.py
```

The UI starts on `http://127.0.0.1:7861` and supports reset, step actions, state inspection, and grading.

## 🏆 Baseline Performance (Reproducible)

Run the baseline with a fixed seed and record real scores before final submission.

```bash
py baseline.py --task task1_easy --model gpt-4o-mini --seed 42
py baseline.py --task task2_medium --model gpt-4o-mini --seed 42
py baseline.py --task task3_hard --model gpt-4o-mini --seed 42
```

Fill this table from real run output (keep the terminal logs as evidence):

| Task | Score | Model | Seed | Evidence |
|------|-------|-------|------|----------|
| `task1_easy` | `TBD` | `gpt-4o-mini` | `42` | `baseline log` |
| `task2_medium` | `TBD` | `gpt-4o-mini` | `42` | `baseline log` |
| `task3_hard` | `TBD` | `gpt-4o-mini` | `42` | `baseline log` |

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

## 👀 Observation Space

Every step returns a structured payload:

```json
{
	"observation": {
		"observation_type": "logs|metrics|alerts|traces|service_info|service_list|dependencies|diagnosis_submitted|timeout|error",
		"data": {},
		"message": "human-readable summary",
		"step_number": 0,
		"remaining_steps": 15
	},
	"reward": 0.0,
	"done": false,
	"info": {
		"step": 0,
		"max_steps": 15,
		"task_id": "task1_easy"
	}
}
```

## 📈 Scoring

The environment uses a multi-step scoring system for more rigorous evaluation (USPs):

| Component | Weight | Metric | Description |
| :--- | :--- | :--- | :--- |
| **Root Cause ID** | 30% | Keyword Match + SVC | Identifying the core issue and origin service. |
| **Affected Services** | 20% | **F1 Score** | Balancing precision and recall of downstream impacts (USP #1). |
| **Remediation** | 20% | Keyword Coverage | Effectiveness of the proposed fix actions. |
| **Reasoning Trace** | 15% | **Rule-based Audit** | Verifying the agent actually investigated the root cause logs/metrics (USP #2). |
| **Efficiency** | 15% | Linear Decay | Penalizing excessive steps and redundant queries. |

### Key Evaluation Features (USPs)
1.  **Strict Affected Service Scorer (USP #1):** Uses an **F1 score** to reward precision and penalize "hallucinated" affected services or missed ones. The grader output includes a detailed diff showing exactly where the agent's diagnosis diverged from the ground truth.
2.  **Reasoning Trace Auditor (USP #2):** Verifies that agents actually investigated relevant logs and metrics before submitting a diagnosis. The grader audits the action history to ensure the correct services were targeted during the investigation window.


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
