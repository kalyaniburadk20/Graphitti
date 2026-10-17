from app.retrieval.graph_retriever import GraphRetriever


graph = GraphRetriever()

query = """
MATCH (n)
WHERE
    (n.chunk_id IS NOT NULL AND n.chunk_id STARTS WITH "mh_")
    OR
    (n.claim_id IS NOT NULL AND n.claim_id STARTS WITH "mh_")
RETURN
    labels(n) AS labels,
    n.chunk_id AS chunk_id,
    n.claim_id AS claim_id,
    n.text AS text
ORDER BY chunk_id, claim_id
"""


try:
    with graph.driver.session() as session:
        for record in session.run(query):
            print(record.data())
finally:
    graph.close()