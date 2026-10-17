from dataclasses import dataclass


@dataclass
class Relation:
    relation_id: str

    subject_entity_id: str
    subject_text: str
    subject_type: str

    predicate: str

    object_entity_id: str
    object_text: str
    object_type: str

    chunk_id: str
    source_url: str

    source_sentence: str

    confidence: float