from dataclasses import dataclass


@dataclass
class AgentTrace:
    attempt: int
    status: str
    intent: str
    strategies: list[str]
    result_count: int
    confidence: float
    message: str