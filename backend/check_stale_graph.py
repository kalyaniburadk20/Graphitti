from app.retrieval.graph_retriever import GraphRetriever


graph = GraphRetriever()

query = """
MATCH (c:Chunk {chunk_id: "mh_chunk_001"})
OPTIONAL MATCH (cl:Claim)-[:EXTRACTED_FROM]->(c)
RETURN
    c.chunk_id AS chunk_id,
    c.text AS text,
    collect({
        claim_id: cl.claim_id,
        predicate: cl.predicate
    }) AS claims
"""


try:
    with graph.driver.session() as session:
        results = session.run(query)

        for record in results:
            print(record.data())

finally:
    graph.close()