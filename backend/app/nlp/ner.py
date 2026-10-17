import hashlib

import spacy

from .chunking_models import SemanticChunk
from .entity_models import Entity
from .entity_normalizer import (
    map_entity_type,
    normalize_entity,
)
from .tech_entity_detector import TechnicalEntityDetector


class EntityRecognizer:

    def __init__(
        self,
        model_name: str = "en_core_web_sm",
    ):
        self.nlp = spacy.load(model_name)
        self.tech_detector = TechnicalEntityDetector()

    @staticmethod
    def _make_entity_id(
        text: str,
        label: str,
    ) -> str:

        raw = f"{text.lower()}|{label}"

        return hashlib.sha1(
            raw.encode("utf-8")
        ).hexdigest()[:16]

    def extract_entities(
        self,
        chunk: SemanticChunk,
    ) -> list[Entity]:

        # =========================================
        # 1. spaCy NER
        # =========================================

        doc = self.nlp(chunk.text)

        spacy_entities = []

        for span in doc.ents:

            normalized_text = normalize_entity(
                span.text
            )

            entity_type = map_entity_type(
                normalized_text,
                span.label_,
            )

            spacy_entities.append(
                Entity(
                    entity_id=self._make_entity_id(
                        normalized_text,
                        entity_type,
                    ),
                    text=normalized_text,
                    label=entity_type,
                    start_char=span.start_char,
                    end_char=span.end_char,
                    chunk_id=chunk.chunk_id,
                    source_url=chunk.document_url,
                    confidence=0.80,
                )
            )

        # =========================================
        # 2. Technical entity detector
        # =========================================

        technical_entities = (
            self.tech_detector.detect(
                text=chunk.text,
                chunk_id=chunk.chunk_id,
                source_url=chunk.document_url,
            )
        )

        print(
           f"spaCy entities: {len(spacy_entities)}"
        )

        print(
         f"Technical entities: {len(technical_entities)}"
        )

        # =========================================
        # 3. Combine
        # =========================================

        all_entities = (
            spacy_entities
            + technical_entities
        )

        # =========================================
        # 4. Remove overlapping duplicates
        # =========================================

        return self._deduplicate(
            all_entities
        )

    @staticmethod
    def _deduplicate(
        entities: list[Entity],
    ) -> list[Entity]:

        # Highest-confidence entity gets priority.
        entities = sorted(
            entities,
            key=lambda entity: (
                -entity.confidence,
                entity.start_char,
                -(entity.end_char - entity.start_char),
            ),
        )

        selected = []

        for entity in entities:

            has_overlap = False

            for existing in selected:

                overlap = not (
                    entity.end_char
                    <= existing.start_char
                    or
                    entity.start_char
                    >= existing.end_char
                )

                if overlap:
                    has_overlap = True
                    break

            if not has_overlap:
                selected.append(entity)

        return sorted(
            selected,
            key=lambda entity: entity.start_char,
        )