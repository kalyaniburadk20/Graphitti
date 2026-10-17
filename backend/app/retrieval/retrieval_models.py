from dataclasses import dataclass


@dataclass
class RetrievalResult:
    chunk_id: str
    text: str
    score: float

    source_url: str
    section_heading: str
    strategy: str

    claim_id: str | None = None

    subject: str | None = None
    predicate: str | None = None
    object: str | None = None

    confidence: float = 0.0