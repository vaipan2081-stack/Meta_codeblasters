"""Minimal Gradio UI for human incident-triage review."""

from __future__ import annotations

import json
import os
from typing import Any

import gradio as gr
import requests


ENV_URL = os.getenv("ENV_URL", "http://127.0.0.1:7860").rstrip("/")
DEFAULT_TASK = os.getenv("TASK_NAME", "task1_easy")


def _post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(f"{ENV_URL}{path}", json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def _get(path: str) -> dict[str, Any]:
    response = requests.get(f"{ENV_URL}{path}", timeout=30)
    response.raise_for_status()
    return response.json()


def reset_episode(task_id: str, seed: float | None) -> str:
    payload: dict[str, Any] = {"task_id": task_id}
    if seed is not None:
        payload["seed"] = int(seed)
    data = _post("/reset", payload)
    return json.dumps(data, indent=2)


def take_action(action_type: str, parameters_json: str) -> tuple[str, str]:
    try:
        params = json.loads(parameters_json) if parameters_json.strip() else {}
    except json.JSONDecodeError as e:
        return "", f"Invalid JSON in parameters: {e}"

    payload = {"action_type": action_type, "parameters": params}
    data = _post("/step", payload)
    return json.dumps(data, indent=2), ""


def get_state() -> str:
    data = _get("/state")
    return json.dumps(data, indent=2)


def grade_episode() -> str:
    data = _post("/grader", {})
    return json.dumps(data, indent=2)


def list_tasks() -> tuple[list[str], str]:
    tasks = _get("/tasks")
    ids = [t["task_id"] for t in tasks]
    details = json.dumps(tasks, indent=2)
    return ids, details


with gr.Blocks(title="Incident Triage Demo") as demo:
    gr.Markdown("# Incident Triage Human Demo")
    gr.Markdown(
        "Use this UI to run a manual episode against the OpenEnv incident environment."
    )

    with gr.Row():
        task_id = gr.Dropdown(
            choices=["task1_easy", "task2_medium", "task3_hard"],
            value=DEFAULT_TASK,
            label="Task",
        )
        seed = gr.Number(value=None, label="Seed (optional)", precision=0)
        reset_btn = gr.Button("Reset Episode", variant="primary")

    initial_observation = gr.Code(label="Initial Observation", language="json")

    with gr.Row():
        action_type = gr.Dropdown(
            choices=[
                "list_services",
                "check_alerts",
                "query_logs",
                "query_metrics",
                "get_service_info",
                "check_dependencies",
                "query_traces",
                "submit_diagnosis",
            ],
            value="list_services",
            label="Action Type",
        )
        action_btn = gr.Button("Run Step", variant="secondary")

    parameters_json = gr.Textbox(
        label="Action Parameters (JSON)",
        value="{}",
        lines=5,
    )
    step_result = gr.Code(label="Step Result", language="json")
    action_error = gr.Textbox(label="Action Error", interactive=False)

    with gr.Row():
        state_btn = gr.Button("Get State")
        grade_btn = gr.Button("Grade Episode")
        task_refresh_btn = gr.Button("Refresh Tasks")

    state_json = gr.Code(label="Environment State", language="json")
    grade_json = gr.Code(label="Grader Output", language="json")
    tasks_json = gr.Code(label="Tasks Metadata", language="json")

    reset_btn.click(reset_episode, [task_id, seed], [initial_observation])
    action_btn.click(take_action, [action_type, parameters_json], [step_result, action_error])
    state_btn.click(get_state, [], [state_json])
    grade_btn.click(grade_episode, [], [grade_json])
    task_refresh_btn.click(list_tasks, [], [task_id, tasks_json])


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7861)
