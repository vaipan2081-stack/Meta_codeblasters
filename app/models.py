"""Pydantic models for the Incident Triage environment."""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Enums ───────────────────────────────────────────────────────────────────

class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ActionType(str, Enum):
    """Actions the agent can take in the environment."""
    QUERY_LOGS = "query_logs"
    QUERY_METRICS = "query_metrics"
    LIST_SERVICES = "list_services"
    GET_SERVICE_INFO = "get_service_info"
    CHECK_DEPENDENCIES = "check_dependencies"
    CHECK_ALERTS = "check_alerts"
    QUERY_TRACES = "query_traces"
    SUBMIT_DIAGNOSIS = "submit_diagnosis"


# ── Request / Response Models ───────────────────────────────────────────────

class ResetRequest(BaseModel):
    task_id: str = Field("task1_easy", description="Task identifier, e.g. 'task1_easy'")
    seed: Optional[int] = Field(None, description="Random seed for scenario selection")


class Action(BaseModel):
    action_type: ActionType = Field(..., description="Type of action to perform")
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Action-specific parameters",
    )


class LogEntry(BaseModel):
    timestamp: str
    service: str
    level: LogLevel
    message: str
    trace_id: Optional[str] = None
    span_id: Optional[str] = None


class MetricDataPoint(BaseModel):
    timestamp: str
    value: float


class Alert(BaseModel):
    timestamp: str
    service: str
    severity: str
    title: str
    description: str


class TraceSpan(BaseModel):
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    service: str
    operation: str
    duration_ms: float
    status: str
    timestamp: str


class ServiceInfo(BaseModel):
    name: str
    type: str  # e.g., "api-gateway", "database", "message-queue", etc.
    status: str
    uptime_hours: float
    version: str
    dependencies: list[str]


class Observation(BaseModel):
    """What the agent sees after taking an action."""
    observation_type: str = Field(..., description="Type of data returned")
    data: Any = Field(..., description="The actual observation data")
    message: str = Field("", description="Human-readable description")
    step_number: int = Field(0, description="Current step in the episode")
    remaining_steps: int = Field(0, description="Steps remaining before timeout")


class StepResult(BaseModel):
    """Structured response for each environment step."""
    observation: Observation
    reward: float = Field(..., ge=0.0, le=1.0)
    done: bool
    info: dict[str, Any] = Field(default_factory=dict)


class Reward(BaseModel):
    """Reward signal returned after episode completion."""
    total_score: float = Field(..., ge=0.0, le=1.0, description="Overall score 0-1")
    root_cause_score: float = Field(0.0, ge=0.0, le=1.0)
    affected_services_score: float = Field(0.0, ge=0.0, le=1.0)
    remediation_score: float = Field(0.0, ge=0.0, le=1.0)
    efficiency_bonus: float = Field(0.0, ge=0.0, le=1.0)
    explanation: str = Field("", description="Human-readable breakdown")


class Diagnosis(BaseModel):
    """Agent's final diagnosis submission."""
    root_cause: str = Field(..., description="Identified root cause")
    root_cause_service: str = Field(..., description="Service where the root cause originates")
    affected_services: list[str] = Field(default_factory=list, description="All affected services")
    severity: str = Field("high", description="Assessed severity: low/medium/high/critical")
    remediation: str = Field(..., description="Recommended remediation steps")
    evidence: list[str] = Field(default_factory=list, description="Key evidence supporting diagnosis")


class EnvironmentState(BaseModel):
    """Current state of the environment."""
    task_id: Optional[str] = None
    scenario_id: Optional[str] = None
    difficulty: Optional[Difficulty] = None
    step_number: int = 0
    max_steps: int = 0
    is_done: bool = False
    services: list[str] = Field(default_factory=list)
    initial_alert: Optional[str] = None


class TaskInfo(BaseModel):
    """Information about an available task."""
    task_id: str
    name: str
    description: str
    difficulty: Difficulty
    max_steps: int


class GraderResult(BaseModel):
    """Result from the grading endpoint."""
    task_id: str
    scenario_id: str
    reward: Reward
    diagnosis_submitted: Optional[Diagnosis] = None
    ground_truth_summary: str = Field("", description="Summary of expected answer (post-grading)")
