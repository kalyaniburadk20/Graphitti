from app.routing.query_router import QueryRouter

from .bm25_retriever import BM25Retriever
from .dense_retriever import DenseRetriever
from .graph_retriever import GraphRetriever
from .hybrid_retriever import HybridRetriever


class RoutingService:

    def __init__(self):

        self.router = QueryRouter()

        self.bm25 = BM25Retriever()
        self.dense = DenseRetriever()
        self.graph = GraphRetriever()
        self.hybrid = HybridRetriever()

    @staticmethod
    def _extract_entity_candidates(
        query: str,
    ) -> list[str]:
        """
        Temporary baseline entity extraction.

        Later this will be replaced by the
        actual NER/entity-linking query pipeline.
        """

        candidates = []

        known_entities = [
            "FastAPI",
            "Pydantic",
            "Starlette",
            "OpenAPI",
            "Swagger",
            "HTTPX",
            "WebSockets",
            "OAuth2",
            "JSON Schema",
        ]

        query_lower = query.lower()

        for entity in known_entities:

            if entity.lower() in query_lower:
                candidates.append(entity)

        return candidates

    def search_with_strategies(
        self,
        query: str,
        strategies: list[str],
        entity_name: str | None = None,
        top_k: int = 5,
    ):
        results = []

        # -------------------------------------------------
        # BM25
        # -------------------------------------------------

        if "bm25" in strategies:

            results.extend(
                self.bm25.search(
                    query,
                    top_k=top_k,
                )
            )

        # -------------------------------------------------
        # Dense
        # -------------------------------------------------

        if "dense" in strategies:

            results.extend(
                self.dense.search(
                    query,
                    top_k=top_k,
                )
            )

        # -------------------------------------------------
        # Graph
        # -------------------------------------------------

        if (
            "graph" in strategies
            and entity_name
        ):

            results.extend(
                self.graph.search(
                    entity_name=entity_name,
                    query=query,
                    top_k=top_k,
                )
            )

        return results

    def search(
        self,
        query: str,
        top_k: int = 5,
    ):

        decision = self.router.classify(
            query
        )

        entity_candidates = (
            self._extract_entity_candidates(
                query
            )
        )

        graph_entity = (
            entity_candidates[0]
            if entity_candidates
            else None
        )

        results = []

        # -----------------------------------------
        # BM25
        # -----------------------------------------

        if "bm25" in decision.retrievers:

            results.extend(
                self.bm25.search(
                    query,
                    top_k=top_k,
                )
            )

        # -----------------------------------------
        # Dense
        # -----------------------------------------

        if "dense" in decision.retrievers:

            results.extend(
                self.dense.search(
                    query,
                    top_k=top_k,
                )
            )

        # -----------------------------------------
        # Graph
        # -----------------------------------------

        if (
            "graph" in decision.retrievers
            and graph_entity
        ):

            results.extend(
                self.graph.search(
                    entity_name=graph_entity,
                    query=query,
                    top_k=top_k,
                )
            )

        return {
            "query": query,
            "routing": decision,
            "entity_candidates": (
                entity_candidates
            ),
            "results": results,
        }