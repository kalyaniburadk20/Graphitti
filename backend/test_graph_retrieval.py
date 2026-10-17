from app.retrieval.query_service import (
    QueryService,
)


service = QueryService()

try:

    result = service.answer_entity_query(
        "FastAPI"
    )

    print(
        "\n========== QUERY RESULT ==========\n"
    )

    print(
        f"Entity: "
        f"{result['entity']}"
    )

    for claim in result["claims"]:

        print(
            f"\n{claim['subject']} "
            f"--[{claim['predicate']}]--> "
            f"{claim['object']}"
        )

        print(
            f"Evidence: "
            f"{claim['evidence']}"
        )

        print(
            f"Source: "
            f"{claim['source_url']}"
        )

finally:

    service.close()