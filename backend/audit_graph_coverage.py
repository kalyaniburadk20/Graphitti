from app.retrieval.graph_retriever import GraphRetriever


# ============================================================
# RELATIONS THAT ARE ACTUALLY SUPPORTED BY THE CURRENT
# NLP EXTRACTION PIPELINE AND ARE EXPECTED IN NEO4J.
# ============================================================

EXTRACTED_RELATIONS = [
    (
        "FastAPI",
        "DEPENDS_ON",
        "Pydantic",
    ),
    (
        "FastAPI",
        "DEPENDS_ON",
        "Starlette",
    ),
    (
        "FastAPI",
        "USES",
        "Uvicorn",
    ),
    (
        "FastAPI",
        "VALIDATES",
        "PUT",
    ),
    (
        "Pydantic",
        "USES",
        "FastAPI",
    ),
    (
        "Starlette",
        "USES",
        "HTTPX",
    ),
    (
        "orjson",
        "USES",
        "ORJSONResponse",
    ),
]


# ============================================================
# RELATIONS THAT ARE SEMANTICALLY SUGGESTED BY THE SOURCE
# BUT ARE NOT CURRENTLY EXTRACTED INTO relations.jsonl.
#
# These are tracked separately so the audit does not call
# correctly-ingested data "missing".
# ============================================================

UNEXTRACTED_EXPECTATIONS = [
    (
        "FastAPI",
        "BUILT_ON",
        "Starlette",
        "The source expresses this across chunk boundaries."
    ),
    (
        "FastAPI",
        "VALIDATES",
        "Pydantic",
        "Pydantic is discussed in validation-related text, "
        "but the current entity/relation extraction does not "
        "produce this exact relation."
    ),
    (
        "FastAPI",
        "COMPATIBLE_WITH",
        "OpenAPI",
        "The source contains the compatibility statement, "
        "but the current extractor cannot establish the "
        "subject for this relation."
    ),
]


def check_relation(
    graph,
    subject,
    predicate,
    object_name,
):
    query = """
    MATCH (
        s:Entity
    )-[r]->(
        o:Entity
    )

    WHERE
        toLower(s.name)
            = toLower($subject)

        AND type(r)
            = $predicate

        AND toLower(o.name)
            = toLower($object)

    RETURN
        s.name AS subject,
        type(r) AS predicate,
        o.name AS object,
        r.claim_id AS claim_id,
        r.confidence AS confidence,
        r.source_url AS source_url

    LIMIT 10
    """

    with graph.driver.session() as session:

        result = session.run(
            query,
            subject=subject,
            predicate=predicate,
            object=object_name,
        )

        return [
            record.data()
            for record in result
        ]


def main():

    graph = GraphRetriever()

    try:

        print("=" * 80)
        print("GRAPH COVERAGE AUDIT")
        print("=" * 80)

        print()
        print("1. CONFIRMED EXTRACTED RELATIONS")
        print("-" * 80)

        found = 0
        missing = 0

        for (
            subject,
            predicate,
            object_name,
        ) in EXTRACTED_RELATIONS:

            results = check_relation(
                graph,
                subject,
                predicate,
                object_name,
            )

            if results:

                found += 1

                print(
                    f"✅ {subject} "
                    f"--{predicate}--> "
                    f"{object_name}"
                )

                # Show provenance for the first matching edge.
                result = results[0]

                print(
                    f"   claim_id: {result.get('claim_id')}"
                )

                print(
                    f"   confidence: "
                    f"{result.get('confidence')}"
                )

            else:

                missing += 1

                print(
                    f"❌ {subject} "
                    f"--{predicate}--> "
                    f"{object_name}"
                )

        total = len(EXTRACTED_RELATIONS)

        coverage = (
            found / total * 100
            if total
            else 0.0
        )

        print()
        print("=" * 80)
        print("EXTRACTED GRAPH COVERAGE SUMMARY")
        print("=" * 80)

        print(
            f"Confirmed: {found}"
        )

        print(
            f"Missing:   {missing}"
        )

        print(
            f"Coverage:  {coverage:.2f}%"
        )

        print()
        print(
            "2. UNEXTRACTED SOURCE EXPECTATIONS"
        )

        print("-" * 80)

        for (
            subject,
            predicate,
            object_name,
            reason,
        ) in UNEXTRACTED_EXPECTATIONS:

            print(
                f"⚠️ {subject} "
                f"--{predicate}--> "
                f"{object_name}"
            )

            print(
                f"   Reason: {reason}"
            )

        print()
        print("=" * 80)
        print("AUDIT COMPLETE")
        print("=" * 80)

    finally:
        graph.close()


if __name__ == "__main__":
    main()