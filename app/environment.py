"""
Core environment state machine for the Incident Triage environment.

Manages episode lifecycle: reset → step* → grade
"""

from __future__ import annotations

import sys
import os
from typing import Any, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import (
    Action,
    ActionType,
    Diagnosis,
    Difficulty,
    EnvironmentState,
    LogEntry,
    MetricDataPoint,
    Observation,
    Reward,
    ServiceInfo,
)
from data.scenarios.scenarios import SERVICES_CATALOG, get_scenario
from graders.grader import compute_reward



class IncidentTriageEnvironment:
    """State machine for a single incident triage episode."""

    def __init__(self) -> None:
        self._scenario: Optional[dict[str, Any]] = None
        self._task_id: Optional[str] = None
        self._step: int = 0
        self._max_steps: int = 0
        self._done: bool = True
        self._diagnosis: Optional[Diagnosis] = None
        self._action_history: list[dict[str, Any]] = []

    # ── Task config ─────────────────────────────────────────────────────

    TASK_CONFIG = {
        "task1_easy": {"max_steps": 15, "difficulty": Difficulty.EASY},
        "task2_medium": {"max_steps": 25, "difficulty": Difficulty.MEDIUM},
        "task3_hard": {"max_steps": 35, "difficulty": Difficulty.HARD},
    }

    # ── Lifecycle ───────────────────────────────────────────────────────

    def reset(self, task_id: str, seed: int | None = None) -> Observation:
        """Reset environment to a new episode."""
        if task_id not in self.TASK_CONFIG:
            raise ValueError(f"Unknown task: {task_id}. Available: {list(self.TASK_CONFIG)}")

        cfg = self.TASK_CONFIG[task_id]
        self._task_id = task_id
        self._max_steps = cfg["max_steps"]
        self._step = 0
        self._done = False
        self._diagnosis = None
        self._action_history = []

        self._scenario = get_scenario(task_id, seed)

        return Observation(
            observation_type="initial_alert",
            data={
                "alert_message": self._scenario["initial_alert"],
                "services_in_scope": self._scenario["services"],
                "available_actions": [a.value for a in ActionType],
                "difficulty": self._scenario["difficulty"],
            },
            message=f"Incident alert received. You have {self._max_steps} steps to diagnose the issue. "
                    f"Services in scope: {', '.join(self._scenario['services'])}.",
            step_number=0,
            remaining_steps=self._max_steps,
        )

    def step(self, action: Action) -> Observation:
        """Process an agent action and return observation."""
        if self._done:
            return Observation(
                observation_type="error",
                data={"error": "Episode is done. Call /reset to start a new episode."},
                message="Episode already finished.",
                step_number=self._step,
                remaining_steps=0,
            )

        self._step += 1
        remaining = self._max_steps - self._step

        # Record action
        self._action_history.append({
            "step": self._step,
            "action_type": action.action_type.value,
            "parameters": action.parameters,
        })

        # Handle submit_diagnosis
        if action.action_type == ActionType.SUBMIT_DIAGNOSIS:
            self._done = True
            try:
                self._diagnosis = Diagnosis(**action.parameters)
            except Exception as e:
                self._diagnosis = Diagnosis(
                    root_cause=action.parameters.get("root_cause", "unknown"),
                    root_cause_service=action.parameters.get("root_cause_service", "unknown"),
                    affected_services=action.parameters.get("affected_services", []),
                    remediation=action.parameters.get("remediation", "none provided"),
                )
            return Observation(
                observation_type="diagnosis_submitted",
                data={"diagnosis": self._diagnosis.model_dump()},
                message="Diagnosis submitted. Call /grader to see your score.",
                step_number=self._step,
                remaining_steps=0,
            )

        # Check step limit
        if self._step >= self._max_steps:
            self._done = True
            return Observation(
                observation_type="timeout",
                data={"message": "Step limit reached without submitting a diagnosis."},
                message=f"Episode timed out after {self._max_steps} steps. No diagnosis submitted.",
                step_number=self._step,
                remaining_steps=0,
            )

        # Dispatch action
        handler = self._ACTION_HANDLERS.get(action.action_type)
        if handler is None:
            return Observation(
                observation_type="error",
                data={"error": f"Unknown action type: {action.action_type}"},
                message=f"Invalid action type. Available: {[a.value for a in ActionType]}",
                step_number=self._step,
                remaining_steps=remaining,
            )

        try:
            result = handler(self, action.parameters)
        except Exception as e:
            result = Observation(
                observation_type="error",
                data={"error": str(e)},
                message=f"Error processing action: {e}",
                step_number=self._step,
                remaining_steps=remaining,
            )

        result.step_number = self._step
        result.remaining_steps = remaining
        return result

    def step_with_feedback(self, action: Action) -> tuple[Observation, float, bool, dict[str, Any]]:
        """Return observation plus reward/done/info for evaluator compatibility."""
        observation = self.step(action)
        done = self._done
        reward = self._compute_step_reward(action, observation)
        info = {
            "step": self._step,
            "max_steps": self._max_steps,
            "task_id": self._task_id,
        }
        return observation, reward, done, info

    def _compute_step_reward(self, action: Action, observation: Observation) -> float:
        """Heuristic trajectory reward in [0, 1]."""
        if observation.observation_type == "error":
            return 0.0

        if observation.observation_type == "timeout":
            return 0.0

        if observation.observation_type == "diagnosis_submitted":
            try:
                reward, _ = self.grade()
                return reward.total_score
            except ValueError:
                return 0.0

        # Reward informative exploration with a small dense signal.
        data = observation.data if isinstance(observation.data, dict) else {}
        count = data.get("count") if isinstance(data.get("count"), int) else None

        if count is not None:
            return 0.12 if count > 0 else 0.03

        if observation.observation_type in {"service_info", "dependencies", "metrics", "logs", "alerts", "traces", "service_list"}:
            return 0.1

        return 0.05

    # ── Action Handlers ─────────────────────────────────────────────────

    def _handle_query_logs(self, params: dict[str, Any]) -> Observation:
        service = params.get("service")
        level = params.get("level")  # optional filter
        keyword = params.get("keyword")  # optional search

        if not service:
            return Observation(
                observation_type="error",
                data={"error": "Parameter 'service' is required."},
                message="Please specify which service's logs to query.",
            )

        logs = [l for l in self._scenario["logs"] if l["service"] == service]

        if level:
            logs = [l for l in logs if l["level"] == level.upper()]

        if keyword:
            logs = [l for l in logs if keyword.lower() in l["message"].lower()]

        if not logs:
            return Observation(
                observation_type="logs",
                data={"logs": [], "count": 0},
                message=f"No logs found for service '{service}' with the given filters.",
            )

        return Observation(
            observation_type="logs",
            data={"logs": logs, "count": len(logs)},
            message=f"Found {len(logs)} log entries for service '{service}'.",
        )

    def _handle_query_metrics(self, params: dict[str, Any]) -> Observation:
        service = params.get("service")
        metric_name = params.get("metric_name")

        if not service:
            return Observation(
                observation_type="error",
                data={"error": "Parameter 'service' is required."},
                message="Please specify which service's metrics to query.",
            )

        svc_metrics = self._scenario.get("metrics", {}).get(service, {})

        if not svc_metrics:
            return Observation(
                observation_type="metrics",
                data={"metrics": {}, "available_metrics": []},
                message=f"No metrics available for service '{service}'.",
            )

        if metric_name:
            if metric_name not in svc_metrics:
                return Observation(
                    observation_type="metrics",
                    data={
                        "metrics": {},
                        "available_metrics": list(svc_metrics.keys()),
                    },
                    message=f"Metric '{metric_name}' not found. Available: {list(svc_metrics.keys())}",
                )
            return Observation(
                observation_type="metrics",
                data={
                    "metrics": {metric_name: svc_metrics[metric_name]},
                    "service": service,
                },
                message=f"Metric '{metric_name}' for service '{service}': {len(svc_metrics[metric_name])} data points.",
            )

        return Observation(
            observation_type="metrics",
            data={
                "metrics": svc_metrics,
                "service": service,
            },
            message=f"All metrics for service '{service}': {list(svc_metrics.keys())}",
        )

    def _handle_list_services(self, params: dict[str, Any]) -> Observation:
        services = []
        for svc_name in self._scenario["services"]:
            catalog_entry = SERVICES_CATALOG.get(svc_name, {})
            services.append({
                "name": svc_name,
                "type": catalog_entry.get("type", "unknown"),
                "version": catalog_entry.get("version", "unknown"),
            })

        return Observation(
            observation_type="service_list",
            data={"services": services, "count": len(services)},
            message=f"{len(services)} services in scope for this incident.",
        )

    def _handle_get_service_info(self, params: dict[str, Any]) -> Observation:
        service = params.get("service")
        if not service:
            return Observation(
                observation_type="error",
                data={"error": "Parameter 'service' is required."},
                message="Please specify which service to inspect.",
            )

        catalog_entry = SERVICES_CATALOG.get(service)
        if not catalog_entry or service not in self._scenario["services"]:
            return Observation(
                observation_type="error",
                data={"error": f"Service '{service}' not found in this incident scope."},
                message=f"Unknown service. Available: {self._scenario['services']}",
            )

        # Determine current status from logs
        error_logs = [l for l in self._scenario["logs"]
                      if l["service"] == service and l["level"] in ("ERROR", "CRITICAL")]
        status = "degraded" if error_logs else "healthy"

        info = {
            "name": service,
            "type": catalog_entry["type"],
            "version": catalog_entry["version"],
            "status": status,
            "dependencies": catalog_entry["dependencies"],
            "available_metrics": list(self._scenario.get("metrics", {}).get(service, {}).keys()),
        }

        return Observation(
            observation_type="service_info",
            data=info,
            message=f"Service '{service}' ({catalog_entry['type']}) - Status: {status}",
        )

    def _handle_check_dependencies(self, params: dict[str, Any]) -> Observation:
        service = params.get("service")
        if not service:
            return Observation(
                observation_type="error",
                data={"error": "Parameter 'service' is required."},
                message="Please specify which service's dependencies to check.",
            )

        catalog_entry = SERVICES_CATALOG.get(service)
        if not catalog_entry:
            return Observation(
                observation_type="error",
                data={"error": f"Service '{service}' not found."},
                message=f"Unknown service.",
            )

        deps = catalog_entry["dependencies"]
        dep_status = {}
        for dep in deps:
            dep_entry = SERVICES_CATALOG.get(dep, {})
            error_logs = [l for l in self._scenario["logs"]
                          if l["service"] == dep and l["level"] in ("ERROR", "CRITICAL")]
            dep_status[dep] = {
                "type": dep_entry.get("type", "unknown"),
                "status": "degraded" if error_logs else "healthy",
                "has_errors_in_logs": len(error_logs) > 0,
            }

        # Also find reverse dependencies (who depends on this service)
        reverse_deps = []
        for svc, entry in SERVICES_CATALOG.items():
            if service in entry.get("dependencies", []) and svc in self._scenario["services"]:
                reverse_deps.append(svc)

        return Observation(
            observation_type="dependencies",
            data={
                "service": service,
                "depends_on": dep_status,
                "depended_on_by": reverse_deps,
            },
            message=f"'{service}' depends on: {deps}. Depended on by: {reverse_deps}",
        )

    def _handle_check_alerts(self, params: dict[str, Any]) -> Observation:
        service = params.get("service")  # optional
        severity = params.get("severity")  # optional

        alerts = self._scenario.get("alerts", [])

        if service:
            alerts = [a for a in alerts if a["service"] == service]
        if severity:
            alerts = [a for a in alerts if a["severity"] == severity.lower()]

        return Observation(
            observation_type="alerts",
            data={"alerts": alerts, "count": len(alerts)},
            message=f"Found {len(alerts)} alerts" + (f" for service '{service}'" if service else ""),
        )

    def _handle_query_traces(self, params: dict[str, Any]) -> Observation:
        trace_id = params.get("trace_id")
        service = params.get("service")

        traces = self._scenario.get("traces", [])

        if trace_id:
            traces = [t for t in traces if t["trace_id"] == trace_id]
        if service:
            traces = [t for t in traces if t["service"] == service]

        if not traces:
            return Observation(
                observation_type="traces",
                data={"traces": [], "count": 0},
                message="No traces found with the given filters.",
            )

        return Observation(
            observation_type="traces",
            data={"traces": traces, "count": len(traces)},
            message=f"Found {len(traces)} trace spans.",
        )

    # Handler dispatch map
    _ACTION_HANDLERS = {
        ActionType.QUERY_LOGS: _handle_query_logs,
        ActionType.QUERY_METRICS: _handle_query_metrics,
        ActionType.LIST_SERVICES: _handle_list_services,
        ActionType.GET_SERVICE_INFO: _handle_get_service_info,
        ActionType.CHECK_DEPENDENCIES: _handle_check_dependencies,
        ActionType.CHECK_ALERTS: _handle_check_alerts,
        ActionType.QUERY_TRACES: _handle_query_traces,
    }

    # ── State ───────────────────────────────────────────────────────────

    def get_state(self) -> EnvironmentState:
        return EnvironmentState(
            task_id=self._task_id,
            scenario_id=self._scenario["scenario_id"] if self._scenario else None,
            difficulty=Difficulty(self._scenario["difficulty"]) if self._scenario else None,
            step_number=self._step,
            max_steps=self._max_steps,
            is_done=self._done,
            services=self._scenario["services"] if self._scenario else [],
            initial_alert=self._scenario["initial_alert"] if self._scenario else None,
        )

    # ── Grading ─────────────────────────────────────────────────────────

    def grade(self) -> tuple[Reward, dict[str, Any]]:
        """Grade the agent's diagnosis against ground truth."""
        if self._scenario is None:
            raise ValueError("No active scenario. Call /reset first.")

        gt = self._scenario["ground_truth"]

        # Call standalone grader
        diagnosis_dict = self._diagnosis.model_dump() if self._diagnosis else {}
        results = compute_reward(
            diagnosis=diagnosis_dict,
            ground_truth=gt,
            steps_used=self._step,
            max_steps=self._max_steps,
            action_history=self._action_history,
        )

        reward = Reward(
            total_score=results["total_score"],
            root_cause_score=results["root_cause_score"],
            affected_services_score=results["affected_services_score"],
            remediation_score=results["remediation_score"],
            efficiency_bonus=results["efficiency_bonus"],
            reasoning_trace_score=results["reasoning_trace_score"],
            explanation=results["explanation"],
        )

        return reward, gt
