import json
from pathlib import Path

from .chunking_models import SemanticChunk


PROJECT_ROOT = Path(__file__).resolve().parents[3]

CHUNK_DATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
)


def save_chunks(
    chunks: list[SemanticChunk],
    filename: str = "semantic_chunks.jsonl",
) -> Path:

    CHUNK_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        CHUNK_DATA_DIR / filename
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:

        for chunk in chunks:

            record = {
                "chunk_id": chunk.chunk_id,
                "document_url": chunk.document_url,
                "section_heading": chunk.section_heading,
                "section_level": chunk.section_level,
                "text": chunk.text,
                "chunk_index": chunk.chunk_index,
                "token_estimate": chunk.token_estimate,
            }

            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )

    return output_path