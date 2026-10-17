import hashlib
from datetime import datetime, timezone

from .claim_models import Claim
from .relation_models import Relation


class ClaimExtractor:

    @staticmethod
    def _make_claim_id(
        relation: Relation,
    ) -> str:

        raw = (
            f"{relation.subject_entity_id}|"
            f"{relation.predicate}|"
            f"{relation.object_entity_id}|"
            f"{relation.chunk_id}|"
            f"{relation.source_url}"
        )

        return hashlib.sha1(
            raw.encode("utf-8")
        ).hexdigest()[:16]

    def extract_claim(
        self,
        relation: Relation,
    ) -> Claim:

        return Claim(
            claim_id=self._make_claim_id(
                relation
            ),

            subject_entity_id=(
                relation.subject_entity_id
            ),
            subject_text=(
                relation.subject_text
            ),
            subject_type=(
                relation.subject_type
            ),

            predicate=relation.predicate,

            object_entity_id=(
                relation.object_entity_id
            ),
            object_text=(
                relation.object_text
            ),
            object_type=(
                relation.object_type
            ),

            source_sentence=(
                relation.source_sentence
            ),
            source_url=(
                relation.source_url
            ),
            chunk_id=relation.chunk_id,

            confidence=relation.confidence,

            extracted_at=datetime.now(
                timezone.utc
            ),
        )