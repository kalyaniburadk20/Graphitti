from app.graph.graph_ingestor import GraphIngestor


ingestor = GraphIngestor()

try:

    ingestor.setup_schema()

    # -------------------------------------------------
    # Page
    # -------------------------------------------------

    page_url = "https://fastapi.tiangolo.com/"

    ingestor.create_page(
        url=page_url,
        title="FastAPI",
    )

    # -------------------------------------------------
    # Chunk
    # -------------------------------------------------

    chunk_id = "demo_chunk_001"

    ingestor.create_chunk(
        chunk_id=chunk_id,
        text="FastAPI depends on Pydantic.",
        section_heading="Example",
        source_url=page_url,
    )

    # -------------------------------------------------
    # Entities
    # -------------------------------------------------

    ingestor.create_entity(
        entity_id="fastapi::framework",
        name="FastAPI",
        entity_type="FRAMEWORK",
    )

    ingestor.create_entity(
        entity_id="pydantic::library",
        name="Pydantic",
        entity_type="LIBRARY",
    )

    # -------------------------------------------------
    # Chunk -> Entity
    # -------------------------------------------------

    ingestor.link_chunk_entity(
        chunk_id=chunk_id,
        entity_id="fastapi::framework",
    )

    ingestor.link_chunk_entity(
        chunk_id=chunk_id,
        entity_id="pydantic::library",
    )

    # -------------------------------------------------
    # Claim
    # -------------------------------------------------

    ingestor.create_claim(
        claim_id="demo_claim_001",
        predicate="DEPENDS_ON",
        confidence=0.95,
        source_sentence=(
            "FastAPI depends on Pydantic."
        ),
        source_url=page_url,
        extracted_at="2026-08-24T12:00:00+05:30",
        subject_entity_id="fastapi::framework",
        object_entity_id="pydantic::library",
        chunk_id=chunk_id,
    )

    print(
        "✅ Graph ingestion test successful"
    )

finally:

    ingestor.close()