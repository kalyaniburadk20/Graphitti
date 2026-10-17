from dataclasses import dataclass


@dataclass
class CanonicalEntity:
    entity_id: str
    canonical_name: str
    entity_type: str