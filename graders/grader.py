"""Grader module for the Incident Triage environment."""

from __future__ import annotations

from typing import Any


def compute_reward(
    diagnosis: dict[str, Any],
    ground_truth: dict[str, Any],
    steps_used: int,
    max_steps: int,
    action_history: list[dict[str, Any]] | None = None,
) -> dict[str, float]:
    """
    Standalone grading function for evaluating agent performance.

    This mirrors the grading logic in environment.py but can be used
    independently for batch evaluation.

    Returns dict with component scores and total.
    """
    if not diagnosis:
        return {
            "total_score": 0.0,
            "root_cause_score": 0.0,
            "affected_services_score": 0.0,
            "remediation_score": 0.0,
            "efficiency_bonus": 0.0,
            "reasoning_trace_score": 0.0,
        }

    # Root cause (30%)
    service_match = 0.5 if (
        diagnosis.get("root_cause_service", "").lower().strip()
        == ground_truth.get("root_cause_service", "").lower().strip()
    ) else 0.0

    gt_kw = _extract_keywords(ground_truth.get("root_cause", ""))
    sub_kw = _extract_keywords(diagnosis.get("root_cause", ""))
    gt_set, sub_set = set(gt_kw), set(sub_kw)
    root_cause_kw_score = min(1.0, len(gt_set & sub_set) / max(1, len(gt_set) * 0.5)) if gt_set else 0.0
    root_cause_score = service_match + 0.5 * root_cause_kw_score

    # Affected services (20%) - F1 Score
    gt_svc = {s.lower().strip() for s in ground_truth.get("affected_services", [])}
    sub_svc = {s.lower().strip() for s in diagnosis.get("affected_services", [])}
    if not gt_svc:
        affected_score = 1.0 if not sub_svc else 0.0
    else:
        tp = len(sub_svc & gt_svc)
        fp = len(sub_svc - gt_svc)
        fn = len(gt_svc - sub_svc)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        affected_score = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    # Remediation (20%)
    gt_rem_kw = set(_extract_keywords(ground_truth.get("remediation", "")))
    sub_rem_kw = set(_extract_keywords(diagnosis.get("remediation", "")))
    remediation_score = min(1.0, len(gt_rem_kw & sub_rem_kw) / max(1, len(gt_rem_kw) * 0.3)) if gt_rem_kw else 0.5

    # Efficiency (15%)
    ratio = steps_used / max_steps if max_steps > 1 else 0.0
    efficiency = max(0.2, 1.0 - 0.8 * ratio)

    # Reasoning Trace (15%)
    reasoning_score = 0.0
    if action_history:
        gt_svc_name = ground_truth.get("root_cause_service", "").lower().strip()
        investigated = any(
            h.get("action_type") in ("query_logs", "query_metrics", "get_service_info") and
            h.get("parameters", {}).get("service", "").lower().strip() == gt_svc_name
            for h in action_history
        )
        if investigated:
            reasoning_score += 0.5
        
        checked_deps = any(
            h.get("action_type") == "check_dependencies"
            for h in action_history
        )
        if checked_deps:
            reasoning_score += 0.5

    total = (
        0.30 * root_cause_score
        + 0.20 * affected_score
        + 0.20 * remediation_score
        + 0.15 * efficiency
        + 0.15 * reasoning_score
    )

    return {
        "total_score": round(min(1.0, max(0.0, total)), 4),
        "root_cause_score": round(root_cause_score, 4),
        "affected_services_score": round(affected_score, 4),
        "remediation_score": round(remediation_score, 4),
        "efficiency_bonus": round(efficiency, 4),
        "reasoning_trace_score": round(reasoning_score, 4),
    }


def _extract_keywords(text: str) -> list[str]:
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "to", "of", "in", "for",
        "on", "with", "at", "by", "from", "as", "and", "but", "or", "not",
    }
    words = text.lower().replace(",", " ").replace(".", " ").replace("-", " ").split()
    return [w for w in words if len(w) > 2 and w not in stop_words]
