from app.retrieval.graph_retriever import (
    GraphRetriever,
)


retriever = GraphRetriever()

try:

    results = retriever.multi_hop_search(
        source_entity="FastAPI",
        first_predicate="DEPENDS_ON",
        second_predicate="USES",
        target_entity="HTTPX",
    )

    print(
        "\n========== MULTI-HOP RESULTS ==========\n"
    )

    for result in results:

        print(
            f"{result['source']} "
            f"--[{result['first_predicate']}]--> "
            f"{result['middle']} "
            f"--[{result['second_predicate']}]--> "
            f"{result['target']}"
        )

        print(
            "\nEvidence 1:"
        )

        print(
            result["first_evidence"]
        )

        print(
            "\nEvidence 2:"
        )

        print(
            result["second_evidence"]
        )

        print(
            "\n" + "-" * 80
        )

finally:

    retriever.close()