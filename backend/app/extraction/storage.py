import json
from pathlib import Path

from .document_models import StructuredDocument


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PROCESSED_DATA_DIR = (
    PROJECT_ROOT / "data" / "processed"
)


def save_structured_documents(
    documents: list[StructuredDocument],
    filename: str = "structured_documents.jsonl",
) -> Path:

    PROCESSED_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        PROCESSED_DATA_DIR / filename
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:

        for document in documents:

            record = {
                "url": document.url,
                "title": document.title,
                "description": document.description,
                "sections": [
                    {
                        "heading": section.heading,
                        "level": section.level,
                        "content": section.content,
                    }
                    for section in document.sections
                ],
                "code_blocks": document.code_blocks,
                "links": document.links,
            }

            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )

    return output_path