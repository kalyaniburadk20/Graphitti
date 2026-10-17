from app.routing.query_router import QueryRouter


router = QueryRouter()


queries = [
    "What does FastAPI depend on?",
    "Which page mentions ORJSONResponse?",
    "Explain FastAPI dependency injection",
    "How does FastAPI work?",
    "What does FastAPI depend on that also uses Pydantic?",
    "Find the documentation for WebSockets",
]


for query in queries:

    decision = router.classify(
        query
    )

    print("\n" + "=" * 80)

    print(
        f"QUERY: {decision.query}"
    )

    print(
        f"INTENT: {decision.intent}"
    )

    print(
        f"CONFIDENCE: {decision.confidence:.2f}"
    )

    print(
        f"RETRIEVERS: {decision.retrievers}"
    )

    print(
        f"REASON: {decision.reason}"
    )