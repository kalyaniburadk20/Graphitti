import json
from pathlib import Path

from .entity_models import Entity


PROJECT_ROOT = Path(__file__).resolve().parents[3]

ENTITY_DATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
)


def save_entities(
    entities: list[Entity],
    filename: str = "entities.jsonl",
) -> Path:

    ENTITY_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        ENTITY_DATA_DIR / filename
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:

        for entity in entities:

            record = {
                "entity_id": entity.entity_id,
                "text": entity.text,
                "label": entity.label,
                "start_char": entity.start_char,
                "end_char": entity.end_char,
                "chunk_id": entity.chunk_id,
                "source_url": entity.source_url,
                "confidence": entity.confidence,
            }

            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )

    return output_path