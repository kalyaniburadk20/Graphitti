from app.retrieval.routing_service import (
    RoutingService,
)


service = RoutingService()


queries = [
    "What does FastAPI depend on?",
    "Which page mentions ORJSONResponse?",
    "Explain FastAPI dependency injection",
    "What does FastAPI depend on that also uses Pydantic?",
]


for query in queries:

    print(
        "\n" + "=" * 100
    )

    result = service.search(
        query,
        top_k=5,
    )

    routing = result["routing"]

    print(
        f"QUERY: {query}"
    )

    print(
        f"INTENT: {routing.intent}"
    )

    print(
        f"CONFIDENCE: {routing.confidence}"
    )

    print(
        f"RETRIEVERS: "
        f"{routing.retrievers}"
    )

    print(
        f"ENTITIES: "
        f"{result['entity_candidates']}"
    )

    print("\nRESULTS:")

    for rank, retrieval in enumerate(
        result["results"],
        start=1,
    ):

        print(
            f"\n[{rank}] "
            f"strategy={retrieval.strategy} "
            f"score={retrieval.score:.6f}"
        )

        print(
            f"chunk={retrieval.chunk_id}"
        )

        print(
            retrieval.text[:300]
        )