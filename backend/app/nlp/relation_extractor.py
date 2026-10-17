import hashlib
import re

import spacy

from .chunking_models import SemanticChunk
from .entity_models import Entity
from .relation_models import Relation
from .relation_validator import validate_relation


class RelationExtractor:

    def __init__(
        self,
        model_name: str = "en_core_web_sm",
    ):
        self.nlp = spacy.load(model_name)

        # =====================================================
        # RELATION PATTERNS
        # =====================================================

        self.patterns = {

            # -------------------------------------------------
            # USES
            # -------------------------------------------------

            "uses": "USES",
            "use": "USES",
            "using": "USES",

            # -------------------------------------------------
            # BUILT_ON
            # -------------------------------------------------

            "based on": "BUILT_ON",
            "built on": "BUILT_ON",
            "powered by": "BUILT_ON",

            # Natural-language formulation used by FastAPI docs.
            "stands on the shoulders of": "BUILT_ON",

            # -------------------------------------------------
            # DEPENDS_ON
            # -------------------------------------------------

            "depends on": "DEPENDS_ON",
            "depend on": "DEPENDS_ON",
            "depends upon": "DEPENDS_ON",
            "depend upon": "DEPENDS_ON",

            # -------------------------------------------------
            # REQUIRES
            # -------------------------------------------------

            "requires": "REQUIRES",
            "require": "REQUIRES",

            # -------------------------------------------------
            # SUPPORTS
            # -------------------------------------------------

            "supports": "SUPPORTS",
            "support": "SUPPORTS",

            # -------------------------------------------------
            # PROVIDES
            # -------------------------------------------------

            "provides": "PROVIDES",
            "provide": "PROVIDES",

            # -------------------------------------------------
            # INCLUDES
            # -------------------------------------------------

            "includes": "INCLUDES",
            "include": "INCLUDES",

            # -------------------------------------------------
            # COMPATIBILITY
            # -------------------------------------------------

            "compatible with": "COMPATIBLE_WITH",
            "works with": "COMPATIBLE_WITH",

            # -------------------------------------------------
            # INTEGRATION
            # -------------------------------------------------

            "integrates with": "INTEGRATES_WITH",
            "integrated with": "INTEGRATES_WITH",

            # -------------------------------------------------
            # IMPLEMENTATION
            # -------------------------------------------------

            "implements": "IMPLEMENTS",
            "implement": "IMPLEMENTS",

            # -------------------------------------------------
            # REPLACEMENT
            # -------------------------------------------------

            "replaces": "REPLACES",
            "replace": "REPLACES",

            # -------------------------------------------------
            # VALIDATION
            # -------------------------------------------------

            "validates": "VALIDATES",
            "validate": "VALIDATES",

            # -------------------------------------------------
            # TESTING
            # -------------------------------------------------

            "tested using": "TESTED_WITH",
            "tested with": "TESTED_WITH",
        }

        # =====================================================
        # SPECIAL TEMPLATES
        # =====================================================

        self.reverse_patterns = {

            # "X is used by Y" means:
            #
            # Y USES X
            #
            "used by": "USES",
        }

    # =========================================================
    # RELATION ID
    # =========================================================

    @staticmethod
    def _make_relation_id(
        subject_id: str,
        predicate: str,
        object_id: str,
        chunk_id: str,
    ) -> str:

        raw = (
            f"{subject_id}|"
            f"{predicate}|"
            f"{object_id}|"
            f"{chunk_id}"
        )

        return hashlib.sha1(
            raw.encode("utf-8")
        ).hexdigest()[:16]

    # =========================================================
    # ENTITY OVERLAP
    # =========================================================

    @staticmethod
    def _overlap(
        entity: Entity,
        start: int,
        end: int,
    ) -> bool:

        return not (
            entity.end_char <= start
            or entity.start_char >= end
        )

    # =========================================================
    # ENTITIES IN SENTENCE
    # =========================================================

    def _sentence_entities(
        self,
        sentence,
        entities: list[Entity],
    ) -> list[Entity]:

        return [
            entity
            for entity in entities
            if self._overlap(
                entity,
                sentence.start_char,
                sentence.end_char,
            )
        ]

    # =========================================================
    # FIND NORMAL PATTERN
    # =========================================================

    def _find_pattern(
        self,
        text: str,
    ):
        """
        Return:

            predicate,
            start,
            end

        for the first valid relation phrase.

        Patterns are matched longest-first.
        """

        lowered = text.lower()

        for phrase in sorted(
            self.patterns,
            key=len,
            reverse=True,
        ):

            match = re.search(
                rf"\b{re.escape(phrase)}\b",
                lowered,
            )

            if not match:
                continue

            # -------------------------------------------------
            # Avoid false BUILT_ON extraction:
            #
            # "tests based on HTTPX"
            # -------------------------------------------------

            if phrase == "based on":

                window_start = max(
                    0,
                    match.start() - 50,
                )

                context = lowered[
                    window_start:
                    match.end() + 30
                ]

                if (
                    "tests based on" in context
                    or "test based on" in context
                    or "testing based on" in context
                ):
                    continue

            return (
                self.patterns[phrase],
                match.start(),
                match.end(),
            )

        return None

    # =========================================================
    # FIND REVERSE PATTERN
    # =========================================================

    def _find_reverse_pattern(
        self,
        text: str,
    ):
        """
        Detect constructions such as:

            "X is used by Y"

        where the grammatical direction is:

            Y USES X
        """

        lowered = text.lower()

        for phrase in sorted(
            self.reverse_patterns,
            key=len,
            reverse=True,
        ):

            match = re.search(
                rf"\b{re.escape(phrase)}\b",
                lowered,
            )

            if not match:
                continue

            return (
                self.reverse_patterns[phrase],
                match.start(),
                match.end(),
            )

        return None

    # =========================================================
    # ENTITY POSITION
    # =========================================================

    @staticmethod
    def _entity_relative_start(
        entity: Entity,
        sentence,
    ) -> int:

        return (
            entity.start_char
            - sentence.start_char
        )

    # =========================================================
    # SUBJECT
    # =========================================================

    def _find_subject(
        self,
        sentence,
        sentence_entities,
        predicate_start,
    ):
        """
        Find the subject using:
        1. Dependency parsing.
        2. Closest entity before predicate.
        """

        if not sentence_entities:
            return None

        absolute_predicate_start = (
            sentence.start_char
            + predicate_start
        )

        # -----------------------------------------------------
        # First: grammatical subject
        # -----------------------------------------------------

        subject_candidates = []

        for entity in sentence_entities:

            entity_tokens = [
                token
                for token in sentence
                if (
                    token.idx >= entity.start_char
                    and token.idx < entity.end_char
                )
            ]

            for token in entity_tokens:

                if token.dep_ in {
                    "nsubj",
                    "nsubjpass",
                    "csubj",
                }:

                    subject_candidates.append(
                        entity
                    )

                    break

        if subject_candidates:

            return max(
                subject_candidates,
                key=lambda entity: entity.end_char,
            )

        # -----------------------------------------------------
        # Second: closest entity before predicate
        # -----------------------------------------------------

        before = [
            entity
            for entity in sentence_entities
            if entity.end_char
            <= absolute_predicate_start
        ]

        if not before:
            return None

        return max(
            before,
            key=lambda entity: entity.end_char,
        )

    # =========================================================
    # OBJECTS AFTER PREDICATE
    # =========================================================

    def _objects_after_predicate(
        self,
        sentence,
        sentence_entities,
        predicate_end,
        subject,
    ):
        """
        Position-based object extraction.

        This is especially important for:

            FastAPI depends on Pydantic and Starlette.

        where dependency parsing may identify only one
        coordinated object.
        """

        absolute_predicate_end = (
            sentence.start_char
            + predicate_end
        )

        candidates = [
            entity
            for entity in sentence_entities
            if (
                entity.start_char
                >= absolute_predicate_end
                and entity.entity_id
                != subject.entity_id
            )
        ]

        # Sort by appearance.
        candidates.sort(
            key=lambda entity: entity.start_char
        )

        return candidates

    # =========================================================
    # OBJECTS USING DEPENDENCY PARSING
    # =========================================================

    def _objects_from_dependencies(
        self,
        sentence,
        sentence_entities,
        subject,
    ):

        candidates = []

        for entity in sentence_entities:

            if (
                entity.entity_id
                == subject.entity_id
            ):
                continue

            entity_tokens = [
                token
                for token in sentence
                if (
                    token.idx >= entity.start_char
                    and token.idx < entity.end_char
                )
            ]

            for token in entity_tokens:

                if token.dep_ in {
                    "dobj",
                    "obj",
                    "pobj",
                    "attr",
                    "oprd",
                    "dative",
                }:

                    candidates.append(
                        entity
                    )

                    break

        return candidates

    # =========================================================
    # MERGE OBJECT CANDIDATES
    # =========================================================

    def _find_objects(
        self,
        sentence,
        sentence_entities,
        predicate_end,
        subject,
        predicate,
    ):
        """
        Combine dependency-based and position-based
        object extraction.

        Special handling for DEPENDS_ON / BUILT_ON / USES
        makes coordinated entities much more reliable.
        """

        dependency_objects = (
            self._objects_from_dependencies(
                sentence,
                sentence_entities,
                subject,
            )
        )

        positional_objects = (
            self._objects_after_predicate(
                sentence,
                sentence_entities,
                predicate_end,
                subject,
            )
        )

        candidates = []

        # -----------------------------------------------------
        # Dependency objects first.
        # -----------------------------------------------------

        candidates.extend(
            dependency_objects
        )

        # -----------------------------------------------------
        # Add positional candidates.
        #
        # This fixes:
        #
        # FastAPI depends on Pydantic and Starlette.
        # -----------------------------------------------------

        if predicate in {
            "DEPENDS_ON",
            "BUILT_ON",
            "USES",
            "SUPPORTS",
            "PROVIDES",
            "REQUIRES",
            "COMPATIBLE_WITH",
        }:

            candidates.extend(
                positional_objects
            )

        else:

            # For other predicates only add positional
            # candidates if dependency parsing found nothing.
            if not candidates:
                candidates.extend(
                    positional_objects
                )

        # -----------------------------------------------------
        # Remove duplicates.
        # -----------------------------------------------------

        unique_objects = []

        seen_ids = set()

        for entity in sorted(
            candidates,
            key=lambda item: item.start_char,
        ):

            if (
                entity.entity_id
                == subject.entity_id
            ):
                continue

            if entity.entity_id in seen_ids:
                continue

            seen_ids.add(
                entity.entity_id
            )

            unique_objects.append(
                entity
            )

        return unique_objects

    # =========================================================
    # REVERSE OBJECT / SUBJECT RESOLUTION
    # ========================================================

    def _resolve_reverse_relation(
        self,
        sentence,
        sentence_entities,
        predicate_start,
        predicate_end,
    ):
        """
        Resolve reverse formulations such as:

            "Used by Starlette: HTTPX"
            "Used by FastAPI: uvicorn"

        Semantics:

            Starlette USES HTTPX
            FastAPI USES Uvicorn

        The grammatical form is:

            [used by] SUBJECT : OBJECT
        """

        absolute_predicate_start = (
            sentence.start_char
            + predicate_start
        )

        absolute_predicate_end = (
            sentence.start_char
            + predicate_end
        )

        # Text after the reverse predicate.
        after_text = sentence.text[predicate_end:]

        # ---------------------------------------------------------
        # CASE 1
        #
        # "Used by Starlette: HTTPX"
        #
        # Everything after "used by" is:
        #
        #     SUBJECT : OBJECT
        #
        # ---------------------------------------------------------

        colon_relative = after_text.find(":")

        if colon_relative != -1:

            colon_absolute = (
                absolute_predicate_end
                + colon_relative
            )

            subject_candidates = [
                entity
                for entity in sentence_entities
                if (
                    entity.start_char
                    >= absolute_predicate_end
                    and entity.end_char
                    <= colon_absolute
                )
            ]

            object_candidates = [
                entity
                for entity in sentence_entities
                if entity.start_char
                > colon_absolute
            ]

            if subject_candidates and object_candidates:

                subject = min(
                    subject_candidates,
                    key=lambda entity: entity.start_char,
                )

                object_entity = min(
                    object_candidates,
                    key=lambda entity: entity.start_char,
                )

                return subject, [object_entity]

        # ---------------------------------------------------------
        # CASE 2
        #
        # Generic fallback:
        #
        # "X ... used by Y"
        #
        # where X is the object and Y is the subject.
        # ---------------------------------------------------------

        before = [
            entity
            for entity in sentence_entities
            if entity.end_char
            <= absolute_predicate_start
        ]

        after = [
            entity
            for entity in sentence_entities
            if entity.start_char
            >= absolute_predicate_end
        ]

        if not before or not after:
            return None

        object_entity = max(
            before,
            key=lambda entity: entity.end_char,
        )

        subject_candidates = [
            entity
            for entity in after
            if entity.entity_id
            != object_entity.entity_id
        ]

        if not subject_candidates:
            return None

        subject = min(
            subject_candidates,
            key=lambda entity: entity.start_char,
        )

        return subject, [object_entity]

    # =========================================================
    # EXTRACT RELATIONS
    # =========================================================

    def extract_relations(
        self,
        chunk: SemanticChunk,
        entities: list[Entity],
    ) -> list[Relation]:

        if len(entities) < 2:
            return []

        doc = self.nlp(
            chunk.text
        )

        relations = []

        # Deduplicate at semantic level rather than just
        # relying on relation IDs.
        seen_relation_keys = set()

        for sentence in doc.sents:

            print("\n" + "=" * 70)
            print("SENTENCE:")
            print(sentence.text)

            # -------------------------------------------------
            # Entities inside sentence
            # -------------------------------------------------

            sentence_entities = (
                self._sentence_entities(
                    sentence,
                    entities,
                )
            )

            # -------------------------------------------------
            # Remove duplicate entity IDs
            # -------------------------------------------------

            unique_entities = []

            seen_entity_ids = set()

            for entity in sentence_entities:

                if entity.entity_id in seen_entity_ids:
                    continue

                seen_entity_ids.add(
                    entity.entity_id
                )

                unique_entities.append(
                    entity
                )

            sentence_entities = (
                unique_entities
            )

            print("\nENTITIES:")

            for entity in sentence_entities:

                print(
                    f"{entity.text} "
                    f"[{entity.start_char}:{entity.end_char}] "
                    f"{entity.label}"
                )

            if len(sentence_entities) < 2:

                print(
                    "SKIP: fewer than 2 entities"
                )

                continue

            # =================================================
            # REVERSE PATTERN FIRST
            # =================================================

            reverse_info = (
                self._find_reverse_pattern(
                    sentence.text
                )
            )

            if reverse_info:

                (
                    predicate,
                    reverse_start,
                    reverse_end,
                ) = reverse_info

                print(
                    "\nREVERSE RELATION PATTERN:"
                )

                print(
                    (
                        predicate,
                        reverse_start,
                        reverse_end,
                    )
                )

                reverse_result = (
                    self._resolve_reverse_relation(
                        sentence,
                        sentence_entities,
                        reverse_start,
                        reverse_end,
                    )
                )

                if reverse_result:

                    subject, object_entities = (
                        reverse_result
                    )

                    for object_entity in object_entities:

                        self._append_relation(
                            relations=relations,
                            seen_relation_keys=(
                                seen_relation_keys
                            ),
                            subject=subject,
                            predicate=predicate,
                            object_entity=object_entity,
                            chunk=chunk,
                            sentence=sentence,
                        )

                    # A reverse construction has been fully
                    # handled. Do not also extract a second,
                    # incorrect forward relation.
                    continue

            # =================================================
            # NORMAL PATTERN
            # =================================================

            relation_info = (
                self._find_pattern(
                    sentence.text
                )
            )

            print(
                "\nRELATION PATTERN:"
            )

            print(
                relation_info
            )

            if relation_info is None:

                print(
                    "SKIP: no known relation phrase"
                )

                continue

            (
                predicate,
                start,
                end,
            ) = relation_info

            print(
                f"FOUND: {predicate}"
            )

            # =================================================
            # SUBJECT
            # =================================================

            subject = self._find_subject(
                sentence,
                sentence_entities,
                start,
            )

            if subject is None:

                print(
                    "SKIP: could not determine subject"
                )

                continue

            # =================================================
            # OBJECTS
            # =================================================

            object_entities = (
                self._find_objects(
                    sentence,
                    sentence_entities,
                    end,
                    subject,
                    predicate,
                )
            )

            print(
                "\nSUBJECT:"
            )

            print(
                subject.text
            )

            print(
                "\nOBJECTS:"
            )

            for object_entity in object_entities:

                print(
                    object_entity.text
                )

            if not object_entities:

                print(
                    "SKIP: could not determine objects"
                )

                continue

            # =================================================
            # CREATE RELATIONS
            # =================================================

            for object_entity in object_entities:

                self._append_relation(
                    relations=relations,
                    seen_relation_keys=(
                        seen_relation_keys
                    ),
                    subject=subject,
                    predicate=predicate,
                    object_entity=object_entity,
                    chunk=chunk,
                    sentence=sentence,
                )

        return relations

    # =========================================================
    # APPEND RELATION
    # =========================================================

    def _append_relation(
        self,
        relations,
        seen_relation_keys,
        subject,
        predicate,
        object_entity,
        chunk,
        sentence,
    ):

        if (
            subject.entity_id
            == object_entity.entity_id
        ):

            print(
                "SKIP: self relation"
            )

            return

        # -----------------------------------------------------
        # Semantic deduplication
        # -----------------------------------------------------

        relation_key = (
            subject.entity_id,
            predicate,
            object_entity.entity_id,
            chunk.chunk_id,
        )

        if relation_key in seen_relation_keys:

            print(
                "SKIP: duplicate semantic relation"
            )

            return

        relation_id = (
            self._make_relation_id(
                subject.entity_id,
                predicate,
                object_entity.entity_id,
                chunk.chunk_id,
            )
        )

        relation = Relation(
            relation_id=relation_id,

            subject_entity_id=(
                subject.entity_id
            ),
            subject_text=subject.text,
            subject_type=subject.label,

            predicate=predicate,

            object_entity_id=(
                object_entity.entity_id
            ),
            object_text=object_entity.text,
            object_type=object_entity.label,

            chunk_id=chunk.chunk_id,
            source_url=chunk.document_url,

            source_sentence=sentence.text,

            confidence=0.80,
        )

        if not validate_relation(
            relation
        ):

            print(
                "SKIP: relation failed validation"
            )

            return

        seen_relation_keys.add(
            relation_key
        )

        relations.append(
            relation
        )

        print(
            f"✅ {subject.text} "
            f"--[{predicate}]--> "
            f"{object_entity.text}"
        )