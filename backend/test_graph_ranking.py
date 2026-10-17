from app.retrieval.graph_retriever import GraphRetriever


def run_test(query, entity):

    graph = GraphRetriever()

    try:

        print()
        print("=" * 80)
        print("QUERY:", query)
        print("ENTITY:", entity)
        print("=" * 80)

        results = graph.search(
            entity_name=entity,
            query=query,
            top_k=5,
        )

        for index, result in enumerate(
            results,
            start=1,
        ):

            print()
            print(
                f"#{index}"
            )

            print(
                "Score:",
                round(
                    result.score,
                    4,
                ),
            )

            print(
                "Claim:",
                result.subject,
                result.predicate,
                result.object,
            )

            print(
                "Evidence:",
                result.text,
            )

            print(
                "Confidence:",
                result.confidence,
            )

    finally:

        graph.close()


if __name__ == "__main__":

    run_test(
        "What does FastAPI use for data validation?",
        "FastAPI",
    )

    run_test(
        "What is FastAPI built on?",
        "FastAPI",
    )

    run_test(
        "What server is used to serve FastAPI applications?",
        "FastAPI",
    )

    run_test(
        "How does FastAPI relate to OpenAPI?",
        "FastAPI",
    )