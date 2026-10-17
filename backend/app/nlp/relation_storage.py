import json
from pathlib import Path

from .relation_models import Relation


PROJECT_ROOT = Path(__file__).resolve().parents[3]

RELATION_DATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
)


def save_relations(
    relations: list[Relation],
    filename: str = "relations.jsonl",
) -> Path:

    RELATION_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        RELATION_DATA_DIR / filename
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:

        for relation in relations:

            record = {
                "source_sentence": relation.source_sentence,
                "relation_id": relation.relation_id,

                "subject_entity_id": (
                    relation.subject_entity_id
                ),
                "subject_text": (
                    relation.subject_text
                ),
                "subject_type": (
                    relation.subject_type
                ),

                "predicate": relation.predicate,

                "object_entity_id": (
                    relation.object_entity_id
                ),
                "object_text": (
                    relation.object_text
                ),
                "object_type": (
                    relation.object_type
                ),

                "chunk_id": relation.chunk_id,
                "source_url": relation.source_url,
                "confidence": relation.confidence,
            }

            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )

    return output_path