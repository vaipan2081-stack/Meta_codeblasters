#!/usr/bin/env python3
"""
Smoke test for the Incident Triage environment.

Runs a complete episode without an LLM — uses a hardcoded investigation
strategy to verify all endpoints work correctly.

Usage:
    python smoke_test.py [--api-url http://localhost:7860]
"""

from __future__ import annotations

import argparse
import json
import sys

import requests


def smoke_test(base_url: str) -> bool:
    base = base_url.rstrip("/")
    passed = 0
    failed = 0

    def check(name: str, condition: bool, detail: str = ""):
        nonlocal passed, failed
        status = "✅" if condition else "❌"
        print(f"  {status} {name}" + (f" — {detail}" if detail else ""))
        if condition:
            passed += 1
        else:
            failed += 1

    print("\n🔍 Smoke Test: Incident Triage Environment")
    print("=" * 55)

    # 1. Health check
    print("\n1️⃣  Health Check")
    r = requests.get(f"{base}/health")
    check("GET /health returns 200", r.status_code == 200)
    check("Response contains status", r.json().get("status") == "healthy")

    # 2. List tasks
    print("\n2️⃣  List Tasks")
    r = requests.get(f"{base}/tasks")
    tasks = r.json()
    check("GET /tasks returns 200", r.status_code == 200)
    check("Returns 3 tasks", len(tasks) == 3)
    check("Tasks have correct IDs",
          {t["task_id"] for t in tasks} == {"task1_easy", "task2_medium", "task3_hard"})

    # 3. Reset with easy task
    print("\n3️⃣  Reset (task1_easy)")
    r = requests.post(f"{base}/reset", json={"task_id": "task1_easy", "seed": 42})
    obs = r.json()
    check("POST /reset returns 200", r.status_code == 200)
    check("Returns initial_alert observation", obs["observation_type"] == "initial_alert")
    check("Has alert message", len(obs["data"].get("alert_message", "")) > 10)
    check("Has services list", len(obs["data"].get("services_in_scope", [])) > 0)
    check("Has available actions", len(obs["data"].get("available_actions", [])) > 0)

    # 4. Get state
    print("\n4️⃣  Get State")
    r = requests.get(f"{base}/state")
    state = r.json()
    check("GET /state returns 200", r.status_code == 200)
    check("Task ID is set", state["task_id"] == "task1_easy")
    check("Step is 0", state["step_number"] == 0)
    check("Not done", state["is_done"] is False)

    # 5. Step: list_services
    print("\n5️⃣  Step: list_services")
    r = requests.post(f"{base}/step", json={
        "action_type": "list_services", "parameters": {}
    })
    step_result = r.json()
    obs = step_result["observation"]
    check("POST /step returns 200", r.status_code == 200)
    check("Step includes reward", 0.0 <= step_result.get("reward", -1) <= 1.0)
    check("Step includes done flag", isinstance(step_result.get("done"), bool))
    check("Returns service_list", obs["observation_type"] == "service_list")
    check("Has services data", len(obs["data"].get("services", [])) > 0)
    check("Step incremented", obs["step_number"] == 1)

    # 6. Step: check_alerts
    print("\n6️⃣  Step: check_alerts")
    r = requests.post(f"{base}/step", json={
        "action_type": "check_alerts", "parameters": {}
    })
    obs = r.json()["observation"]
    check("Returns alerts", obs["observation_type"] == "alerts")
    check("Has alert data", obs["data"].get("count", 0) > 0)

    # 7. Step: query_logs
    print("\n7️⃣  Step: query_logs")
    services = state["services"]
    first_service = services[0] if services else "api-gateway"
    r = requests.post(f"{base}/step", json={
        "action_type": "query_logs",
        "parameters": {"service": first_service}
    })
    obs = r.json()["observation"]
    check("Returns logs", obs["observation_type"] == "logs")

    # 8. Step: query_logs with level filter
    print("\n8️⃣  Step: query_logs (ERROR level)")
    r = requests.post(f"{base}/step", json={
        "action_type": "query_logs",
        "parameters": {"service": first_service, "level": "ERROR"}
    })
    obs = r.json()["observation"]
    check("Returns filtered logs", obs["observation_type"] == "logs")

    # 9. Step: query_metrics
    print("\n9️⃣  Step: query_metrics")
    r = requests.post(f"{base}/step", json={
        "action_type": "query_metrics",
        "parameters": {"service": first_service}
    })
    obs = r.json()["observation"]
    check("Returns metrics", obs["observation_type"] == "metrics")

    # 10. Step: check_dependencies
    print("\n🔟  Step: check_dependencies")
    r = requests.post(f"{base}/step", json={
        "action_type": "check_dependencies",
        "parameters": {"service": first_service}
    })
    obs = r.json()["observation"]
    check("Returns dependencies", obs["observation_type"] == "dependencies")
    check("Has depends_on", "depends_on" in obs["data"])
    check("Has depended_on_by", "depended_on_by" in obs["data"])

    # 11. Step: get_service_info
    print("\n1️⃣1️⃣  Step: get_service_info")
    r = requests.post(f"{base}/step", json={
        "action_type": "get_service_info",
        "parameters": {"service": first_service}
    })
    obs = r.json()["observation"]
    check("Returns service_info", obs["observation_type"] == "service_info")

    # 12. Step: query_traces
    print("\n1️⃣2️⃣  Step: query_traces")
    r = requests.post(f"{base}/step", json={
        "action_type": "query_traces",
        "parameters": {}
    })
    obs = r.json()["observation"]
    check("Returns traces", obs["observation_type"] == "traces")

    # 13. Submit diagnosis
    print("\n1️⃣3️⃣  Step: submit_diagnosis")
    r = requests.post(f"{base}/step", json={
        "action_type": "submit_diagnosis",
        "parameters": {
            "root_cause": "Database out of memory crash",
            "root_cause_service": "order-db",
            "affected_services": ["order-db", "order-service", "api-gateway"],
            "severity": "critical",
            "remediation": "Restart database and increase memory limit",
            "evidence": ["OOM killer logs", "Connection pool exhausted"],
        }
    })
    obs = r.json()["observation"]
    check("Returns diagnosis_submitted", obs["observation_type"] == "diagnosis_submitted")

    # 14. Grade
    print("\n1️⃣4️⃣  Grade Episode")
    r = requests.post(f"{base}/grader")
    result = r.json()
    check("POST /grader returns 200", r.status_code == 200)
    check("Has reward", "reward" in result)
    reward = result["reward"]
    check("Total score is 0-1", 0.0 <= reward["total_score"] <= 1.0)
    check("Has explanation", len(reward.get("explanation", "")) > 0)
    check("Has ground truth summary", len(result.get("ground_truth_summary", "")) > 0)
    print(f"\n  📊 Score: {reward['total_score']:.3f}")
    print(f"     Root cause:      {reward['root_cause_score']:.3f}")
    print(f"     Affected (F1):   {reward['affected_services_score']:.3f}")
    print(f"     Remediation:     {reward['remediation_score']:.3f}")
    print(f"     Reasoning Trace: {reward['reasoning_trace_score']:.3f}")
    print(f"     Efficiency:      {reward['efficiency_bonus']:.3f}")

    # 14b. Determinism check: same scenario + same diagnosis should produce same score
    print("\n1️⃣4️⃣b  Determinism Check")
    requests.post(f"{base}/reset", json={"task_id": "task1_easy", "seed": 999}).raise_for_status()
    requests.post(f"{base}/step", json={
        "action_type": "submit_diagnosis",
        "parameters": {
            "root_cause": "Database out of memory crash",
            "root_cause_service": "order-db",
            "affected_services": ["order-db", "order-service", "api-gateway"],
            "severity": "critical",
            "remediation": "Restart database and increase memory limit",
            "evidence": ["OOM killer logs", "Connection pool exhausted"],
        }
    }).raise_for_status()
    first = requests.post(f"{base}/grader").json()["reward"]["total_score"]

    requests.post(f"{base}/reset", json={"task_id": "task1_easy", "seed": 999}).raise_for_status()
    requests.post(f"{base}/step", json={
        "action_type": "submit_diagnosis",
        "parameters": {
            "root_cause": "Database out of memory crash",
            "root_cause_service": "order-db",
            "affected_services": ["order-db", "order-service", "api-gateway"],
            "severity": "critical",
            "remediation": "Restart database and increase memory limit",
            "evidence": ["OOM killer logs", "Connection pool exhausted"],
        }
    }).raise_for_status()
    second = requests.post(f"{base}/grader").json()["reward"]["total_score"]
    check("Same seed/action gives same score", abs(first - second) < 1e-9, f"first={first}, second={second}")

    # 15. Baseline endpoint
    print("\n1️⃣5️⃣  Baseline Info")
    r = requests.get(f"{base}/baseline")
    check("GET /baseline returns 200", r.status_code == 200)
    check("Has run_command", "run_command" in r.json())

    # 16. Test medium task
    print("\n1️⃣6️⃣  Reset (task2_medium)")
    r = requests.post(f"{base}/reset", json={"task_id": "task2_medium", "seed": 42})
    obs = r.json()
    check("Medium task resets OK", r.status_code == 200)
    check("Different scenario loaded", obs["observation_type"] == "initial_alert")

    # 17. Test hard task
    print("\n1️⃣7️⃣  Reset (task3_hard)")
    r = requests.post(f"{base}/reset", json={"task_id": "task3_hard", "seed": 42})
    obs = r.json()
    check("Hard task resets OK", r.status_code == 200)
    check("Hard has more services", len(obs["data"].get("services_in_scope", [])) >= 4)

    # Summary
    total = passed + failed
    print(f"\n{'='*55}")
    print(f"Results: {passed}/{total} passed, {failed}/{total} failed")
    print(f"{'='*55}")

    return failed == 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-url", default="http://localhost:7860")
    args = parser.parse_args()

    success = smoke_test(args.api_url)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
