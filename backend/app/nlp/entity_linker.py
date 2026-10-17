from .canonical_entity import CanonicalEntity
from .entity_models import Entity
from .entity_normalizer import normalize_entity


class EntityLinker:

    def __init__(self):
        self.registry: dict[
            str,
            CanonicalEntity
        ] = {}

    @staticmethod
    def _make_key(
        name: str,
        entity_type: str,
    ) -> str:

        return (
            f"{name.lower().strip()}"
            f"::{entity_type.lower().strip()}"
        )

    def link(
        self,
        entity: Entity,
    ) -> CanonicalEntity:

        canonical_name = normalize_entity(
            entity.text
        )

        key = self._make_key(
            canonical_name,
            entity.label,
        )

        # Entity already exists
        if key in self.registry:
            return self.registry[key]

        # Create a new canonical entity
        canonical_entity = CanonicalEntity(
            entity_id=canonical_name.lower().replace(
                " ",
                "_",
            ),
            canonical_name=canonical_name,
            entity_type=entity.label,
        )

        self.registry[key] = canonical_entity

        return canonical_entity