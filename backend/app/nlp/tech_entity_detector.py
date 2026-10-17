import re

from .entity_models import Entity
from .entity_normalizer import (
    TECH_ALIASES,
    TECHNOLOGY_TYPES,
    normalize_entity,
)


class TechnicalEntityDetector:

    def __init__(self):
        self.aliases = sorted(
            TECH_ALIASES.keys(),
            key=len,
            reverse=True,
        )

    def detect(
        self,
        text: str,
        chunk_id: str,
        source_url: str,
    ) -> list[Entity]:

        entities = []

        for alias in self.aliases:

            pattern = (
                rf"(?<!\w)"
                rf"{re.escape(alias)}"
                rf"(?!\w)"
            )

            for match in re.finditer(
                pattern,
                text,
                flags=re.IGNORECASE,
            ):

                surface = match.group(0)

                canonical = normalize_entity(
                    surface
                )

                entity_type = (
                    TECHNOLOGY_TYPES.get(
                        canonical,
                        "TECHNOLOGY",
                    )
                )

                entity_id = (
                    f"{canonical.lower()}"
                    f"::{entity_type.lower()}"
                )

                entities.append(
                    Entity(
                        entity_id=entity_id,
                        text=canonical,
                        label=entity_type,
                        start_char=match.start(),
                        end_char=match.end(),
                        chunk_id=chunk_id,
                        source_url=source_url,
                        confidence=0.95,
                    )
                )

        return self._remove_overlaps(
            entities
        )

    @staticmethod
    def _remove_overlaps(
        entities: list[Entity],
    ) -> list[Entity]:

        entities = sorted(
            entities,
            key=lambda e: (
                e.start_char,
                -(e.end_char - e.start_char),
            ),
        )

        selected = []

        for entity in entities:

            overlaps = any(
                not (
                    entity.end_char <= existing.start_char
                    or entity.start_char >= existing.end_char
                )
                for existing in selected
            )

            if not overlaps:
                selected.append(entity)

        return selected