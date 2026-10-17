import json
from pathlib import Path

from app.graph.graph_ingestor import GraphIngestor


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
)


STRUCTURED_FILE = (
    DATA_DIR
    / "structured_documents.jsonl"
)

CHUNKS_FILE = (
    DATA_DIR
    / "semantic_chunks.jsonl"
)

ENTITIES_FILE = (
    DATA_DIR
    / "entities.jsonl"
)

CLAIMS_FILE = (
    DATA_DIR
    / "claims.jsonl"
)


def read_jsonl(path: Path):
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:
            line = line.strip()

            if line:
                yield json.loads(line)


ingestor = GraphIngestor()

try:

    ingestor.setup_schema()

    print(
        "\n========== INGESTING PAGES ==========\n"
    )

    # -------------------------------------------------
    # Pages
    # -------------------------------------------------

    for document in read_jsonl(
        STRUCTURED_FILE
    ):

        ingestor.ingest_page(
            url=document["url"],
            title=document["title"],
        )

    # -------------------------------------------------
    # Chunks
    # -------------------------------------------------

    print(
        "\n========== INGESTING CHUNKS ==========\n"
    )

    for chunk in read_jsonl(
        CHUNKS_FILE
    ):

        ingestor.ingest_chunk(
            chunk_id=chunk["chunk_id"],
            text=chunk["text"],
            section_heading=(
                chunk["section_heading"]
            ),
            source_url=chunk["document_url"],
        )

    # -------------------------------------------------
    # Entities
    # -------------------------------------------------

    print(
        "\n========== INGESTING ENTITIES ==========\n"
    )

    for entity in read_jsonl(
        ENTITIES_FILE
    ):

        ingestor.ingest_entity(
            entity_id=entity["entity_id"],
            name=entity["text"],
            entity_type=entity["label"],
        )

        ingestor.ingest_chunk_entity(
            chunk_id=entity["chunk_id"],
            entity_id=entity["entity_id"],
        )

    # -------------------------------------------------
    # Claims
    # -------------------------------------------------

    print(
        "\n========== INGESTING CLAIMS ==========\n"
    )

    for claim in read_jsonl(
        CLAIMS_FILE
    ):

        ingestor.ingest_claim(
            claim
        )

        ingestor.create_semantic_edge(
        subject_entity_id=(
            claim["subject_entity_id"]
        ),
        object_entity_id=(
            claim["object_entity_id"]
        ),
        predicate=claim["predicate"],
        claim_id=claim["claim_id"],
    )

    print(
        "\n✅ REAL GRAPH INGESTION COMPLETE"
    )

finally:

    ingestor.close()