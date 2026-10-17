from app.graph.graph_ingestor import GraphIngestor


ingestor = GraphIngestor()

try:

    ingestor.setup_schema()

    print(
        "✅ Graph schema created successfully"
    )

finally:

    ingestor.close()