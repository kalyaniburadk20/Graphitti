import json
from pathlib import Path

from app.graph.graph_ingestor import GraphIngestor


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "processed"

STRUCTURED_DOCUMENTS_FILE = (
    DATA_DIR / "structured_documents.jsonl"
)

SEMANTIC_CHUNKS_FILE = (
    DATA_DIR / "semantic_chunks.jsonl"
)

ENTITIES_FILE = (
    DATA_DIR / "entities.jsonl"
)

CLAIMS_FILE = (
    DATA_DIR / "claims.jsonl"
)


# ============================================================
# JSONL LOADER
# ============================================================

def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    records = []

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        for line_number, line in enumerate(
            file,
            start=1,
        ):

            line = line.strip()

            if not line:
                continue

            try:
                records.append(
                    json.loads(line)
                )

            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON in "
                    f"{path} at line "
                    f"{line_number}: {exc}"
                ) from exc

    return records


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("Graphitti — Neo4j Graph Synchronization")
    print("=" * 70)

    print()
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Data directory: {DATA_DIR}")

    print()
    print("Loading processed data...")

    documents = load_jsonl(
        STRUCTURED_DOCUMENTS_FILE
    )

    chunks = load_jsonl(
        SEMANTIC_CHUNKS_FILE
    )

    entities = load_jsonl(
        ENTITIES_FILE
    )

    claims = load_jsonl(
        CLAIMS_FILE
    )

    print(
        f"Documents : {len(documents)}"
    )

    print(
        f"Chunks    : {len(chunks)}"
    )

    print(
        f"Entities  : {len(entities)}"
    )

    print(
        f"Claims    : {len(claims)}"
    )

    print()
    print("Connecting to Neo4j...")

    ingestor = GraphIngestor()

    try:

        if not ingestor.client.verify_connection():
            raise RuntimeError(
                "Neo4j connection verification failed."
            )

        print("Neo4j connection: OK")

        # ----------------------------------------------------
        # SCHEMA
        # ----------------------------------------------------

        print()
        print("Setting up schema...")

        ingestor.setup_schema()

        print("Schema: OK")

        # ----------------------------------------------------
        # PAGES
        # ----------------------------------------------------

        print()
        print("Ingesting pages...")

        pages_ingested = 0

        for document in documents:

            url = document["url"]

            title = document.get(
                "title",
                "",
            )

            ingestor.ingest_page(
                url=url,
                title=title,
            )

            pages_ingested += 1

        print(
            f"Pages ingested: {pages_ingested}"
        )

        # ----------------------------------------------------
        # CHUNKS
        # ----------------------------------------------------

        print()
        print("Ingesting chunks...")

        chunks_ingested = 0

        for chunk in chunks:

            ingestor.ingest_chunk(
                chunk_id=chunk["chunk_id"],
                text=chunk["text"],
                section_heading=chunk.get(
                    "section_heading"
                )
                or "",
                source_url=chunk[
                    "document_url"
                ],
            )

            chunks_ingested += 1

        print(
            f"Chunks ingested: {chunks_ingested}"
        )

        # ----------------------------------------------------
        # ENTITIES
        # ----------------------------------------------------

        print()
        print("Ingesting entities...")

        entities_ingested = 0

        for entity in entities:

            ingestor.ingest_entity(
                entity_id=entity[
                    "entity_id"
                ],
                name=entity["text"],
                entity_type=entity[
                    "label"
                ],
            )

            entities_ingested += 1

        print(
            f"Entities ingested: "
            f"{entities_ingested}"
        )

        # ----------------------------------------------------
        # CHUNK -> ENTITY
        # ----------------------------------------------------

        print()
        print("Creating chunk/entity links...")

        chunk_entity_links = 0

        seen_chunk_entity = set()

        for entity in entities:

            key = (
                entity["chunk_id"],
                entity["entity_id"],
            )

            if key in seen_chunk_entity:
                continue

            seen_chunk_entity.add(key)

            ingestor.ingest_chunk_entity(
                chunk_id=entity[
                    "chunk_id"
                ],
                entity_id=entity[
                    "entity_id"
                ],
            )

            chunk_entity_links += 1

        print(
            "Chunk/entity links created: "
            f"{chunk_entity_links}"
        )

        # ----------------------------------------------------
        # CLAIMS
        # ----------------------------------------------------

        print()
        print("Ingesting claims...")

        claims_ingested = 0

        for claim in claims:

            ingestor.ingest_claim(
                claim=claim
            )

            claims_ingested += 1

        print(
            f"Claims ingested: {claims_ingested}"
        )

        # ----------------------------------------------------
        # SEMANTIC EDGES
        # ----------------------------------------------------

        print()
        print("Creating semantic edges...")

        semantic_edges_created = 0

        for claim in claims:

            predicate = claim[
                "predicate"
            ]

            ingestor.create_semantic_edge(
                subject_entity_id=claim[
                    "subject_entity_id"
                ],
                object_entity_id=claim[
                    "object_entity_id"
                ],
                predicate=predicate,
                claim_id=claim[
                    "claim_id"
                ],
            )

            semantic_edges_created += 1

        print(
            "Semantic edges processed: "
            f"{semantic_edges_created}"
        )

        # ----------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------

        print()
        print("=" * 70)
        print("Graph synchronization completed successfully.")
        print("=" * 70)

        print()
        print("Summary:")
        print(
            f"  Pages             : {pages_ingested}"
        )
        print(
            f"  Chunks            : {chunks_ingested}"
        )
        print(
            f"  Entities          : {entities_ingested}"
        )
        print(
            f"  Chunk/entity links: {chunk_entity_links}"
        )
        print(
            f"  Claims            : {claims_ingested}"
        )
        print(
            f"  Semantic edges    : {semantic_edges_created}"
        )

    finally:

        ingestor.close()


if __name__ == "__main__":
    main()