from dataclasses import dataclass


@dataclass
class RoutingDecision:
    query: str
    intent: str
    confidence: float
    retrievers: list[str]
    reason: str