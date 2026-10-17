from app.graph.neo4j_client import Neo4jClient


client = Neo4jClient()

try:

    connected = client.verify_connection()

    if connected:
        print(
            "✅ Neo4j connection successful"
        )
    else:
        print(
            "❌ Neo4j connection failed"
        )

finally:

    client.close()