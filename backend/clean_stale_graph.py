from app.retrieval.graph_retriever import GraphRetriever


STALE_CHUNK_PREFIX = "mh_"
STALE_CLAIM_PREFIX = "mh_"


graph = GraphRetriever()


DELETE_QUERY = """
MATCH (n)
WHERE
    (
        n.chunk_id IS NOT NULL
        AND n.chunk_id STARTS WITH $chunk_prefix
    )
    OR
    (
        n.claim_id IS NOT NULL
        AND n.claim_id STARTS WITH $claim_prefix
    )
DETACH DELETE n
RETURN count(n) AS deleted
"""


VERIFY_QUERY = """
MATCH (n)
WHERE
    (
        n.chunk_id IS NOT NULL
        AND n.chunk_id STARTS WITH $chunk_prefix
    )
    OR
    (
        n.claim_id IS NOT NULL
        AND n.claim_id STARTS WITH $claim_prefix
    )
RETURN count(n) AS remaining
"""


try:
    with graph.driver.session() as session:

        result = session.run(
            DELETE_QUERY,
            chunk_prefix=STALE_CHUNK_PREFIX,
            claim_prefix=STALE_CLAIM_PREFIX,
        )

        deleted = result.single()["deleted"]

        print(f"Deleted stale nodes: {deleted}")

        result = session.run(
            VERIFY_QUERY,
            chunk_prefix=STALE_CHUNK_PREFIX,
            claim_prefix=STALE_CLAIM_PREFIX,
        )

        remaining = result.single()["remaining"]

        print(f"Remaining stale nodes: {remaining}")

finally:
    graph.close()