"""
Baseline agent for the Incident Triage environment.

Uses an LLM (GPT-4o by default) to systematically investigate and diagnose
production incidents. This serves as a reference point for evaluating the
environment's difficulty calibration.

Usage:
    python baseline.py --task task1_easy --api-url http://localhost:7860
    python baseline.py --task task2_medium --api-url http://localhost:7860 --model gpt-4o-mini
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import requests

try:
    from openai import OpenAI
except ImportError:
    print("ERROR: openai package not installed. Run: pip install openai")
    sys.exit(1)


SYSTEM_PROMPT = """You are an expert Site Reliability Engineer (SRE) diagnosing a production incident.
You have access to a simulated distributed system environment with the following actions:

1. list_services - List all services in scope
2. check_alerts - View active alerts (optional: service, severity)
3. query_logs - Query logs for a service (required: service, optional: level, keyword)
4. query_metrics - Query metrics for a service (required: service, optional: metric_name)
5. get_service_info - Get detailed service info (required: service)
6. check_dependencies - Check dependency graph (required: service)
7. query_traces - Query distributed traces (optional: trace_id, service)
8. submit_diagnosis - Submit final diagnosis (required: root_cause, root_cause_service, affected_services, remediation)

Your goal is to identify:
- The root cause of the incident
- Which service is the origin of the problem
- All affected services
- Recommended remediation steps

Strategy:
1. First, list services and check all alerts to understand the scope
2. Query logs for services that have alerts, starting with the most critical
3. Check dependencies to understand the service topology
4. Query metrics to confirm your hypotheses
5. Once confident, submit your diagnosis

Respond with a JSON object for each action:
{"action_type": "<action_name>", "parameters": {<params>}}

When ready to diagnose, use:
{"action_type": "submit_diagnosis", "parameters": {"root_cause": "...", "root_cause_service": "...", "affected_services": ["..."], "severity": "...", "remediation": "...", "evidence": ["..."]}}
"""


def run_baseline(
    task_id: str,
    api_url: str,
    model: str = "gpt-4o",
    seed: int | None = None,
    verbose: bool = True,
) -> dict[str, Any]:
    """Run the baseline agent on a task and return the grading result."""
    client = OpenAI()
    base = api_url.rstrip("/")

    # Reset environment
    reset_resp = requests.post(f"{base}/reset", json={"task_id": task_id, "seed": seed})
    reset_resp.raise_for_status()
    observation = reset_resp.json()

    if verbose:
        print(f"\n{'='*60}")
        print(f"TASK: {task_id}")
        print(f"{'='*60}")
        print(f"Initial alert: {observation['data']['alert_message']}")
        print(f"Services: {observation['data']['services_in_scope']}")
        print(f"Max steps: {observation['remaining_steps']}")
        print()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"INCIDENT ALERT:\n{observation['data']['alert_message']}\n\n"
            f"Services in scope: {observation['data']['services_in_scope']}\n"
            f"Available actions: {observation['data']['available_actions']}\n"
            f"You have {observation['remaining_steps']} steps. Begin your investigation."
        )},
    ]

    step = 0
    max_steps = observation["remaining_steps"]

    while step < max_steps:
        # Get LLM action
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.1,
            max_tokens=1024,
        )

        assistant_msg = response.choices[0].message.content
        messages.append({"role": "assistant", "content": assistant_msg})

        # Parse action from response
        try:
            # Extract JSON from the response
            json_start = assistant_msg.index("{")
            json_end = assistant_msg.rindex("}") + 1
            action = json.loads(assistant_msg[json_start:json_end])
        except (ValueError, json.JSONDecodeError):
            messages.append({
                "role": "user",
                "content": "ERROR: Could not parse your response as JSON. Please respond with a valid JSON action.",
            })
            step += 1
            continue

        if verbose:
            print(f"Step {step + 1}: {action.get('action_type', '?')} "
                  f"params={json.dumps(action.get('parameters', {}), indent=None)}")

        # Execute action
        step_resp = requests.post(f"{base}/step", json=action)
        step_resp.raise_for_status()
        obs = step_resp.json()

        step += 1

        if verbose:
            print(f"  → {obs['message']}")

        # Check if episode is done
        if obs.get("observation_type") in ("diagnosis_submitted", "timeout"):
            break

        # Feed observation back to LLM
        messages.append({
            "role": "user",
            "content": (
                f"Observation (step {obs['step_number']}/{max_steps}, "
                f"{obs['remaining_steps']} remaining):\n"
                f"Type: {obs['observation_type']}\n"
                f"Message: {obs['message']}\n"
                f"Data:\n{json.dumps(obs['data'], indent=2)}"
            ),
        })

    # Grade
    grade_resp = requests.post(f"{base}/grader")
    grade_resp.raise_for_status()
    result = grade_resp.json()

    if verbose:
        print(f"\n{'='*60}")
        print("GRADING RESULT")
        print(f"{'='*60}")
        reward = result["reward"]
        print(f"Total Score: {reward['total_score']}")
        print(f"Root Cause:  {reward['root_cause_score']}")
        print(f"Affected:    {reward['affected_services_score']}")
        print(f"Remediation: {reward['remediation_score']}")
        print(f"Efficiency:  {reward['efficiency_bonus']}")
        print(f"\n{reward['explanation']}")
        print(f"\nGround Truth: {result['ground_truth_summary']}")

    return result


def main():
    parser = argparse.ArgumentParser(description="Run baseline agent on Incident Triage environment")
    parser.add_argument("--task", default="task1_easy", choices=["task1_easy", "task2_medium", "task3_hard"])
    parser.add_argument("--api-url", default="http://localhost:7860")
    parser.add_argument("--model", default="gpt-4o")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    result = run_baseline(
        task_id=args.task,
        api_url=args.api_url,
        model=args.model,
        seed=args.seed,
        verbose=not args.quiet,
    )

    print(f"\nFinal score: {result['reward']['total_score']}")


if __name__ == "__main__":
    main()
