from app.graph.graph_ingestor import GraphIngestor


ingestor = GraphIngestor()

try:

    ingestor.setup_schema()

    ingestor.create_entity(
        entity_id="fastapi::framework",
        name="FastAPI",
        entity_type="FRAMEWORK",
    )

    print(
        "✅ FastAPI inserted into Neo4j"
    )

finally:

    ingestor.close()