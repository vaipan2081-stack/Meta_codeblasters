"""
Submission inference script for Incident Triage OpenEnv environment.

This script follows the required structured stdout format:
[START], [STEP], [END]
"""

from __future__ import annotations

import json
import os
from typing import Any

import requests
from openai import OpenAI

API_BASE_URL = os.getenv("API_BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.getenv("HF_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
API_KEY = HF_TOKEN or OPENAI_API_KEY
ENV_URL = os.getenv("ENV_URL", "http://localhost:7860")

TASK_NAME = os.getenv("TASK_NAME", "task1_easy")
MAX_STEPS = int(os.getenv("MAX_STEPS", "20"))
SUCCESS_SCORE_THRESHOLD = float(os.getenv("SUCCESS_SCORE_THRESHOLD", "0.65"))
BENCHMARK = "incident-triage"
SUPPORTED_TASKS = ["task1_easy", "task2_medium", "task3_hard"]


SYSTEM_PROMPT = """You are an SRE agent diagnosing a production incident.
Respond ONLY with compact JSON:
{"action_type":"<action>","parameters":{...}}
Prefer this sequence: list_services -> check_alerts -> query_logs -> check_dependencies -> query_metrics -> submit_diagnosis.
"""


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: str | None) -> None:
    error_text = error if error else "none"
    print(
        f"[STEP] step={step} action={action} reward={reward:.4f} done={str(done).lower()} error={error_text}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: list[float]) -> None:
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.4f} rewards={json.dumps(rewards)}",
        flush=True,
    )


def parse_json_action(text: str) -> dict[str, Any] | None:
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        payload = json.loads(text[start:end])
        if "action_type" not in payload:
            return None
        if "parameters" not in payload:
            payload["parameters"] = {}
        return payload
    except Exception:
        return None


def build_prompt(observation: dict[str, Any], history: list[str]) -> str:
    return (
        "Current observation:\n"
        f"type: {observation.get('observation_type')}\n"
        f"message: {observation.get('message')}\n"
        f"data: {json.dumps(observation.get('data', {}), ensure_ascii=True)}\n\n"
        "Recent steps:\n"
        + "\n".join(history[-6:])
        + "\n\nReturn next JSON action only."
    )


def run_task(client: OpenAI, task_name: str) -> None:
    reset_resp = requests.post(f"{ENV_URL.rstrip('/')}/reset", json={"task_id": task_name, "seed": 42}, timeout=30)
    reset_resp.raise_for_status()
    observation = reset_resp.json()

    rewards: list[float] = []
    history: list[str] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

    for step in range(1, MAX_STEPS + 1):
        prompt = build_prompt(observation, history)

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=400,
        )

        content = response.choices[0].message.content or ""
        action = parse_json_action(content)
        if not action:
            action = {"action_type": "check_alerts", "parameters": {}}

        step_resp = requests.post(f"{ENV_URL.rstrip('/')}/step", json=action, timeout=30)
        step_resp.raise_for_status()
        step_payload = step_resp.json()

        observation = step_payload.get("observation", {})
        reward = float(step_payload.get("reward", 0.0))
        done = bool(step_payload.get("done", False))

        rewards.append(reward)
        steps_taken = step
        history.append(f"step={step} action={action.get('action_type')} reward={reward:.4f}")
        log_step(step=step, action=action.get("action_type", "unknown"), reward=reward, done=done, error=None)

        if done:
            break

    grade_resp = requests.post(f"{ENV_URL.rstrip('/')}/grader", timeout=30)
    grade_resp.raise_for_status()
    grade_payload = grade_resp.json()
    score = float(grade_payload.get("reward", {}).get("total_score", 0.0))
    success = score >= SUCCESS_SCORE_THRESHOLD

    log_end(success=success, steps=steps_taken, score=score, rewards=rewards)


def run() -> None:
    if not API_KEY:
        raise RuntimeError("Missing API key. Set HF_TOKEN or OPENAI_API_KEY.")
    if not API_BASE_URL:
        raise RuntimeError("Missing API_BASE_URL for model endpoint.")

    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    if TASK_NAME.lower() == "all":
        for task_name in SUPPORTED_TASKS:
            run_task(client, task_name)
        return

    run_task(client, TASK_NAME)


if __name__ == "__main__":
    run()
