from dataclasses import dataclass, field


@dataclass
class AnswerCitation:
    source_url: str
    source_sentence: str
    chunk_id: str

    claim_id: str | None = None

    subject: str | None = None
    predicate: str | None = None
    object: str | None = None

    confidence: float = 0.0


@dataclass
class SynthesizedAnswer:
    query: str
    answer: str
    confidence: float

    citations: list[AnswerCitation] = field(
        default_factory=list
    )

    supporting_claims: list[dict] = field(
        default_factory=list
    )