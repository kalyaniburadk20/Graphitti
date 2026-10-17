from dataclasses import dataclass


@dataclass
class Entity:
    entity_id: str
    text: str
    label: str
    start_char: int
    end_char: int
    chunk_id: str
    source_url: str
    confidence: float