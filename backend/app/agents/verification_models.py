from dataclasses import dataclass


@dataclass
class VerificationResult:
    faithful: bool
    confidence: float
    supported_claims: int
    unsupported_claims: int
    reason: str