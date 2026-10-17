from dataclasses import dataclass, field

from .trace_models import AgentTrace
from .latency_models import RunMetrics


@dataclass
class AgentState:
    query: str

    intent: str = ""
    intent_confidence: float = 0.0

    entity_candidates: list[str] = field(default_factory=list)

    plan: object | None = None

    results: list = field(default_factory=list)
    evidence: list = field(default_factory=list)

    answer: str | None = None
    confidence: float = 0.0

    attempts: int = 0
    max_attempts: int = 3

    status: str = "STARTING"
    termination_reason: str | None = None

    trace: list[AgentTrace] = field(default_factory=list)

    metrics: RunMetrics = field(default_factory=RunMetrics)