import json
from pathlib import Path

from .claim_models import Claim


PROJECT_ROOT = Path(__file__).resolve().parents[3]

CLAIM_DATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
)


def save_claims(
    claims: list[Claim],
    filename: str = "claims.jsonl",
) -> Path:

    CLAIM_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        CLAIM_DATA_DIR / filename
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:

        for claim in claims:

            record = {
                "claim_id": claim.claim_id,

                "subject_entity_id": (
                    claim.subject_entity_id
                ),
                "subject_text": (
                    claim.subject_text
                ),
                "subject_type": (
                    claim.subject_type
                ),

                "predicate": claim.predicate,

                "object_entity_id": (
                    claim.object_entity_id
                ),
                "object_text": (
                    claim.object_text
                ),
                "object_type": (
                    claim.object_type
                ),

                "source_sentence": (
                    claim.source_sentence
                ),
                "source_url": (
                    claim.source_url
                ),
                "chunk_id": claim.chunk_id,

                "confidence": claim.confidence,

                "extracted_at": (
                    claim.extracted_at.isoformat()
                ),
            }

            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )

    return output_path