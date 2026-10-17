from app.retrieval.hybrid_retriever import (
    HybridRetriever,
)


retriever = HybridRetriever()


queries = [
    (
        "What does FastAPI depend on?",
        "FastAPI",
    ),
    (
        "How does FastAPI use Pydantic?",
        "FastAPI",
    ),
    (
        "What is OpenAPI documentation?",
        "OpenAPI",
    ),
]


for query, entity_name in queries:

    print(
        "\n" + "=" * 80
    )

    print(
        f"QUERY: {query}"
    )

    print(
        f"ENTITY: {entity_name}"
    )

    results = retriever.search(
        query=query,
        entity_name=entity_name,
        top_k=5,
    )

    for rank, result in enumerate(
        results,
        start=1,
    ):

        print(
            f"\n[{rank}] "
            f"RRF={result.score:.6f}"
        )

        print(
            f"chunk_id: "
            f"{result.chunk_id}"
        )

        print(
            f"section: "
            f"{result.section_heading}"
        )

        print(
            f"strategy: "
            f"{result.strategy}"
        )

        print(
            f"source: "
            f"{result.source_url}"
        )

        print(
            result.text[:500]
        )