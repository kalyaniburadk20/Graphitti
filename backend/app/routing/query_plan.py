from dataclasses import dataclass, field


@dataclass
class QueryStep:
    step_id: int
    operation: str

    entity: str | None = None
    predicate: str | None = None
    target: str | None = None

    status: str = "PENDING"
    result: list = field(
        default_factory=list
    )


@dataclass
class QueryPlan:
    original_query: str
    intent: str

    steps: list[QueryStep] = field(
        default_factory=list
    )

    termination_reason: str | None = None