from dataclasses import dataclass


@dataclass
class ConfidenceResult:
    score: float
    sufficient: bool
    reason: str