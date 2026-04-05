"""
FastAPI application for the Incident Triage OpenEnv environment.

Endpoints:
  POST /reset      - Reset environment with a task_id
  POST /step       - Take an action in the environment
  GET  /state      - Get current environment state
  GET  /tasks      - List available tasks
  POST /grader     - Grade the current episode
  GET  /baseline   - Get baseline agent info
  GET  /health     - Health check
"""

from __future__ import annotations

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    Action,
    EnvironmentState,
    GraderResult,
    Observation,
    ResetRequest,
    Reward,
    TaskInfo,
    Difficulty,
)
from app.environment import IncidentTriageEnvironment

# ── App Setup ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Incident Triage Environment",
    description=(
        "OpenEnv-compatible environment for LLM agent evaluation. "
        "Agents must diagnose production incidents by querying logs, metrics, "
        "alerts, and traces across a simulated distributed microservices system."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Single environment instance (stateful per session)
env = IncidentTriageEnvironment()

# ── Task Definitions ────────────────────────────────────────────────────────

TASKS = [
    TaskInfo(
        task_id="task1_easy",
        name="Single Service Failure",
        description=(
            "Diagnose a straightforward single-service crash. "
            "Clear error logs point to the root cause. "
            "Good for calibrating basic log analysis capabilities."
        ),
        difficulty=Difficulty.EASY,
        max_steps=15,
    ),
    TaskInfo(
        task_id="task2_medium",
        name="Cascading Failure",
        description=(
            "Identify the root cause in a multi-service cascading failure. "
            "Requires correlating logs across services and understanding "
            "event-driven architectures. Red herrings may be present."
        ),
        difficulty=Difficulty.MEDIUM,
        max_steps=25,
    ),
    TaskInfo(
        task_id="task3_hard",
        name="Silent Degradation",
        description=(
            "Diagnose subtle performance degradation with misleading symptoms. "
            "Multiple red herrings, indirect causation chains, and services "
            "that appear healthy masking the true root cause. Requires deep "
            "systems reasoning."
        ),
        difficulty=Difficulty.HARD,
        max_steps=35,
    ),
]


# ── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    """Health check for container readiness."""
    return {"status": "healthy", "environment": "incident-triage"}


@app.get("/tasks", response_model=list[TaskInfo])
def get_tasks():
    """List all available tasks with descriptions and difficulty levels."""
    return TASKS


@app.post("/reset", response_model=Observation)
def reset_environment(request: ResetRequest):
    """Reset the environment to start a new episode.

    Args:
        request: Contains task_id (required) and optional seed.

    Returns:
        Initial observation with the incident alert and available actions.
    """
    try:
        obs = env.reset(task_id=request.task_id, seed=request.seed)
        return obs
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/step", response_model=Observation)
def take_step(action: Action):
    """Process an agent action and return the resulting observation.

    Available actions:
    - query_logs: Query logs for a service (params: service, level?, keyword?)
    - query_metrics: Query metrics for a service (params: service, metric_name?)
    - list_services: List all services in scope
    - get_service_info: Get detailed info about a service (params: service)
    - check_dependencies: Check dependency graph (params: service)
    - check_alerts: View alerts (params: service?, severity?)
    - query_traces: Query distributed traces (params: trace_id?, service?)
    - submit_diagnosis: Submit final diagnosis (params: root_cause, root_cause_service, affected_services, remediation)
    """
    obs = env.step(action)
    return obs


@app.get("/state", response_model=EnvironmentState)
def get_state():
    """Get the current environment state including step count and episode status."""
    return env.get_state()


@app.post("/grader", response_model=GraderResult)
def grade_episode():
    """Grade the current episode after the agent has submitted a diagnosis.

    Returns detailed scoring breakdown across:
    - Root cause identification (40%)
    - Affected services (25%)
    - Remediation quality (20%)
    - Efficiency bonus (15%)
    """
    try:
        reward, ground_truth = env.grade()
        state = env.get_state()
        return GraderResult(
            task_id=state.task_id or "unknown",
            scenario_id=state.scenario_id or "unknown",
            reward=reward,
            diagnosis_submitted=env._diagnosis,
            ground_truth_summary=(
                f"Root cause: {ground_truth['root_cause']}. "
                f"Affected: {ground_truth['affected_services']}. "
                f"Severity: {ground_truth['severity']}."
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/baseline")
def baseline_info():
    """Return information about the baseline agent and how to run it."""
    return {
        "description": (
            "Baseline agent uses GPT-4o to systematically investigate the incident. "
            "It follows a structured approach: list services → check alerts → "
            "query logs of alerted services → check dependencies → query metrics → submit diagnosis."
        ),
        "model": "gpt-4o",
        "expected_scores": {
            "task1_easy": "0.70 - 0.90",
            "task2_medium": "0.50 - 0.75",
            "task3_hard": "0.30 - 0.55",
        },
        "run_command": "python baseline.py --task task1_easy --api-url http://localhost:7860",
    }


# ── Entrypoint ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
