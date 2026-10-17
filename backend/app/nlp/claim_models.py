from dataclasses import dataclass
from datetime import datetime


@dataclass
class Claim:
    claim_id: str

    subject_entity_id: str
    subject_text: str
    subject_type: str

    predicate: str

    object_entity_id: str
    object_text: str
    object_type: str

    source_sentence: str
    source_url: str
    chunk_id: str

    confidence: float
    extracted_at: datetime