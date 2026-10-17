from app.graph.graph_ingestor import GraphIngestor


ingestor = GraphIngestor()

try:

    ingestor.setup_schema()

    url = "https://example.com/graphitti-multihop"

    # -------------------------------------------------
    # Entities
    # -------------------------------------------------

    ingestor.ingest_entity(
        entity_id="mh::fastapi",
        name="FastAPI",
        entity_type="FRAMEWORK",
    )

    ingestor.ingest_entity(
        entity_id="mh::starlette",
        name="Starlette",
        entity_type="LIBRARY",
    )

    ingestor.ingest_entity(
        entity_id="mh::pydantic",
        name="Pydantic",
        entity_type="LIBRARY",
    )

    # -------------------------------------------------
    # Page
    # -------------------------------------------------

    ingestor.ingest_page(
        url=url,
        title="Graphitti Multi-Hop Test",
    )

    # -------------------------------------------------
    # Chunks
    # -------------------------------------------------

    ingestor.ingest_chunk(
        chunk_id="mh_chunk_001",
        text=(
            "FastAPI depends on Starlette."
        ),
        section_heading="Dependencies",
        source_url=url,
    )

    ingestor.ingest_chunk(
        chunk_id="mh_chunk_002",
        text=(
            "Starlette uses Pydantic."
        ),
        section_heading="Libraries",
        source_url=url,
    )

    # -------------------------------------------------
    # Claims
    # -------------------------------------------------

    claim1 = {
        "claim_id": "mh_claim_001",
        "subject_entity_id": "mh::fastapi",
        "object_entity_id": "mh::starlette",
        "chunk_id": "mh_chunk_001",
        "predicate": "DEPENDS_ON",
        "confidence": 0.95,
        "source_sentence": (
            "FastAPI depends on Starlette."
        ),
        "source_url": url,
        "extracted_at": "2026-08-31T00:00:00+00:00",
    }

    claim2 = {
        "claim_id": "mh_claim_002",
        "subject_entity_id": "mh::starlette",
        "object_entity_id": "mh::pydantic",
        "chunk_id": "mh_chunk_002",
        "predicate": "USES",
        "confidence": 0.95,
        "source_sentence": (
            "Starlette uses Pydantic."
        ),
        "source_url": url,
        "extracted_at": "2026-08-31T00:00:00+00:00",
    }

    ingestor.ingest_claim(claim1)
    ingestor.ingest_claim(claim2)

    # -------------------------------------------------
    # Semantic edges
    # -------------------------------------------------

    ingestor.create_semantic_edge(
        subject_entity_id="mh::fastapi",
        object_entity_id="mh::starlette",
        predicate="DEPENDS_ON",
        claim_id="mh_claim_001",
    )

    ingestor.create_semantic_edge(
        subject_entity_id="mh::starlette",
        object_entity_id="mh::pydantic",
        predicate="USES",
        claim_id="mh_claim_002",
    )

    print(
        "✅ Real multi-hop fixture created"
    )

finally:

    ingestor.close()