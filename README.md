---
title: OpenEnv Incident Triage
emoji: 🚨
colorFrom: red
colorTo: blue
sdk: docker
app_port: 7860
---

# Incident Triage OpenEnv Environment

Production incident triage environment for evaluating LLM agents on realistic SRE workflows.

This repository is prepared for Round 1 OpenEnv submission and implements:
- Real-world domain simulation (production outage diagnosis)
- OpenEnv-compatible API (`reset`, `step`, `state`) with typed models
- Three graded tasks (`easy`, `medium`, `hard`) with reward range `[0.0, 1.0]`
- Baseline and submission inference scripts
- Dockerized deployment for Hugging Face Spaces

## 1) Requirement Mapping (Submission)

- Real-world task: incident triage across microservices
- OpenEnv interface: implemented via FastAPI endpoints and typed Pydantic models
- Minimum 3 tasks with graders: `task1_easy`, `task2_medium`, `task3_hard`
- Meaningful reward function: partial progress + component scoring + efficiency
- Baseline script: `baseline.py` with deterministic seed option
- Submission inference script: `inference.py` in repository root, structured `[START]/[STEP]/[END]` logs
- Deployment artifacts: `Dockerfile`, HF Space metadata in README frontmatter, `openenv.yaml`

## 2) Repository Structure

```text
app/
  main.py            FastAPI routes (`/reset`, `/step`, `/state`, `/tasks`, `/grader`, `/health`)
  models.py          Typed request/response models
  environment.py     Core environment state machine and transition logic
data/scenarios/
  scenarios.py       Task scenarios and ground truth
graders/
  grader.py          Standalone grading logic
baseline.py          Baseline runner
inference.py         Required submission inference runner
smoke_test.py        Endpoint smoke tests
openenv.yaml         Environment metadata and tasks
Dockerfile           Container build for local + HF Spaces
```

## 3) Tasks and Difficulty

| Task ID | Difficulty | Max Steps | Objective |
|---|---|---:|---|
| `task1_easy` | Easy | 15 | Diagnose clear single-service failure |
| `task2_medium` | Medium | 25 | Diagnose cascading multi-service failure |
| `task3_hard` | Hard | 35 | Diagnose subtle degradation with red herrings |

## 4) API Contract

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Liveness/health check |
| `GET` | `/tasks` | List available tasks |
| `POST` | `/reset` | Start episode (`task_id`, optional `seed`) |
| `POST` | `/step` | Apply action and return `observation`, `reward`, `done`, `info` |
| `GET` | `/state` | Read current environment state |
| `POST` | `/grader` | Grade current episode |
| `GET` | `/baseline` | Baseline metadata |

### Observation Shape

Each step returns:
- `observation`: typed observation payload
- `reward`: float in `[0.0, 1.0]` contribution space
- `done`: episode completion flag
- `info`: step metadata

### Supported Actions

- `list_services`
- `check_alerts`
- `query_logs`
- `query_metrics`
- `get_service_info`
- `check_dependencies`
- `query_traces`
- `submit_diagnosis`

## 5) Reward and Grading

Current grader component weights:
- Root cause identification: `40%`
- Affected services: `25%`
- Remediation quality: `20%`
- Efficiency bonus: `15%`

Final score is clamped to `[0.0, 1.0]`.

## 6) Quick Start (Local)

### Install

```bash
py -m pip install -r requirements.txt
```

### Run Environment API

```bash
py -m uvicorn app.main:app --host 0.0.0.0 --port 7860
```

### Run Smoke Test

```bash
py smoke_test.py --api-url http://127.0.0.1:7860
```

## 7) Docker (Required)

```bash
docker build -t incident-triage-env .
docker run -p 7860:7860 incident-triage-env
```

Expected health check:

```bash
curl http://127.0.0.1:7860/health
```

## 8) Baseline Script

`baseline.py` supports deterministic runs with `--seed`.

Example:

```bash
py baseline.py --task task1_easy --model gpt-4o-mini --seed 42
py baseline.py --task task2_medium --model gpt-4o-mini --seed 42
py baseline.py --task task3_hard --model gpt-4o-mini --seed 42
```

Reference baseline scores (documented in service metadata):

| Task | Score |
|---|---:|
| `task1_easy` | `0.9100` |
| `task2_medium` | `0.7600` |
| `task3_hard` | `0.4850` |

## 9) Submission Inference Script (Required)

Required environment variables (per submission instructions):
- `API_BASE_URL`
- `MODEL_NAME`
- `HF_TOKEN`

Supported optional variables:
- `OPENAI_API_KEY`
- `ENV_URL` (default `http://localhost:7860`)
- `TASK_NAME` (default `task1_easy`)
- `MAX_STEPS`

Run:

```bash
set API_BASE_URL=https://your-endpoint/v1
set MODEL_NAME=your-model
set HF_TOKEN=your-token
set ENV_URL=http://127.0.0.1:7860
set TASK_NAME=task1_easy
py inference.py
```

`inference.py` emits strict structured logs:
- `[START] task=... env=... model=...`
- `[STEP] step=... action=... reward=... done=... error=...`
- `[END] success=... steps=... score=... rewards=[...]`

## 10) OpenAI-Compatible Local Testing (LM Studio)

For local testing without paid OpenAI API, OpenAI-compatible endpoints can be used.
This does not change the submission requirement to use the OpenAI client in `inference.py`.

Validated local setup examples:

```bash
set ENV_URL=http://127.0.0.1:7860
set API_BASE_URL=http://localhost:1234/v1
set MODEL_NAME=qwen/qwen3.5-9b
set OPENAI_API_KEY=lm-studio
set MAX_STEPS=4
py inference.py
```

```bash
set ENV_URL=http://127.0.0.1:7860
set API_BASE_URL=http://localhost:1234/v1
set MODEL_NAME=dolphin-2.9.4-llama3.1-8b
set OPENAI_API_KEY=lm-studio
set MAX_STEPS=4
py inference.py
```

If LM Studio returns `400 Model unloaded.`, reload the model and rerun.

## 11) Hugging Face Spaces Deployment

This repo is configured for Docker-based HF Spaces deployment:
- `sdk: docker` in README frontmatter
- App served on port `7860`
- `Dockerfile` included in repository root

## 12) Pre-Submission Checklist (Must Pass)

- HF Space deploys and responds (`/health`, `/reset`)
- OpenEnv metadata present in `openenv.yaml`
- Docker image builds and starts cleanly
- `inference.py` exists in repo root and runs with required env vars
- Structured stdout format is preserved: `[START]`, `[STEP]`, `[END]`
- Three tasks are exposed and gradable
- Smoke tests pass against local or hosted API

## 13) References

- Judge runbook: `JUDGE.md`
- Hosted validation checklist: `HOSTED_VALIDATION_CHECKLIST.md`
- Architecture notes: `ARCHITECTURE.md`
- Pending work tracker: `PENDING_WORK_TRACKER.md`
