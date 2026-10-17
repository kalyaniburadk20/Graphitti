from dataclasses import dataclass


@dataclass
class SemanticChunk:
    chunk_id: str
    document_url: str
    section_heading: str
    section_level: int
    text: str
    chunk_index: int
    token_estimate: int