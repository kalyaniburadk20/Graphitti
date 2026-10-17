from app.graph.graph_ingestor import (
    GraphIngestor,
)


ingestor = GraphIngestor()

try:

    ingestor.setup_schema()

    # -------------------------------------------------
    # Entities
    # -------------------------------------------------

    ingestor.ingest_entity(
        entity_id="demo::fastapi",
        name="FastAPIDemo",
        entity_type="FRAMEWORK",
    )

    ingestor.ingest_entity(
        entity_id="demo::library",
        name="DemoLibrary",
        entity_type="LIBRARY",
    )

    ingestor.ingest_entity(
        entity_id="demo::pydantic",
        name="PydanticDemo",
        entity_type="LIBRARY",
    )

    # -------------------------------------------------
    # Page + chunk
    # -------------------------------------------------

    url = (
        "https://example.com/"
        "graphitti-demo"
    )

    ingestor.ingest_page(
        url=url,
        title="Graphitti Demo",
    )

    ingestor.ingest_chunk(
        chunk_id="demo_multi_hop_chunk_1",
        text=(
            "FastAPIDemo depends on "
            "DemoLibrary."
        ),
        section_heading="Demo",
        source_url=url,
    )

    ingestor.ingest_chunk(
        chunk_id="demo_multi_hop_chunk_2",
        text=(
            "DemoLibrary uses "
            "PydanticDemo."
        ),
        section_heading="Demo",
        source_url=url,
    )

    # -------------------------------------------------
    # Claims
    # -------------------------------------------------

    claim1 = {
        "claim_id": "demo_mh_claim_1",
        "subject_entity_id": "demo::fastapi",
        "object_entity_id": "demo::library",
        "chunk_id": "demo_multi_hop_chunk_1",
        "predicate": "DEPENDS_ON",
        "confidence": 0.95,
        "source_sentence": (
            "FastAPIDemo depends on "
            "DemoLibrary."
        ),
        "source_url": url,
        "extracted_at": (
            "2026-08-31T00:00:00+00:00"
        ),
    }

    claim2 = {
        "claim_id": "demo_mh_claim_2",
        "subject_entity_id": "demo::library",
        "object_entity_id": "demo::pydantic",
        "chunk_id": "demo_multi_hop_chunk_2",
        "predicate": "USES",
        "confidence": 0.95,
        "source_sentence": (
            "DemoLibrary uses "
            "PydanticDemo."
        ),
        "source_url": url,
        "extracted_at": (
            "2026-08-31T00:00:00+00:00"
        ),
    }

    ingestor.ingest_claim(
        claim1
    )

    ingestor.ingest_claim(
        claim2
    )

    ingestor.create_semantic_edge(
        subject_entity_id=(
            "demo::fastapi"
        ),
        object_entity_id=(
            "demo::library"
        ),
        predicate="DEPENDS_ON",
        claim_id="demo_mh_claim_1",
    )

    ingestor.create_semantic_edge(
        subject_entity_id=(
            "demo::library"
        ),
        object_entity_id=(
            "demo::pydantic"
        ),
        predicate="USES",
        claim_id="demo_mh_claim_2",
    )

    print(
        "✅ Multi-hop fixture created"
    )

finally:

    ingestor.close()