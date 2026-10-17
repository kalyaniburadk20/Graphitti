from app.retrieval.bm25_retriever import (
    BM25Retriever,
)


retriever = BM25Retriever()


queries = [
    "What does FastAPI depend on?",
    "How does FastAPI use Pydantic?",
    "What is OpenAPI documentation?",
]


for query in queries:

    print(
        "\n" + "=" * 80
    )

    print(
        f"QUERY: {query}"
    )

    results = retriever.search(
        query,
        top_k=5,
    )

    for rank, result in enumerate(
        results,
        start=1,
    ):

        print(
            f"\n[{rank}] "
            f"score={result.score:.4f}"
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
            f"source: "
            f"{result.source_url}"
        )

        print(
            result.text[:500]
        )