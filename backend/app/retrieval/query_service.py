from .graph_retriever import GraphRetriever


class QueryService:

    def __init__(self):
        self.graph = GraphRetriever()

    def answer_entity_query(
        self,
        entity_name: str,
    ) -> dict:

        entities = self.graph.find_entity(
            entity_name
        )

        if not entities:
            return {
                "entity": entity_name,
                "claims": [],
                "message": "Entity not found",
            }

        entity = entities[0]

        claims = self.graph.get_claims_for_entity(
            entity["entity_id"]
        )

        return {
            "entity": entity,
            "claims": claims,
        }

    def close(self):
        self.graph.close()