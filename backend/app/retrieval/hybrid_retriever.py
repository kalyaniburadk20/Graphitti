from .bm25_retriever import BM25Retriever
from .dense_retriever import DenseRetriever
from .graph_retriever import GraphRetriever
from .rrf_fusion import RRFFusion
from .retrieval_models import RetrievalResult


class HybridRetriever:

    def __init__(
        self,
        top_k_each: int = 10,
    ):
        self.top_k_each = top_k_each

        self.bm25 = BM25Retriever()
        self.dense = DenseRetriever()
        self.graph = GraphRetriever()

        self.fusion = RRFFusion()

    def search(
        self,
        query: str,
        entity_name: str | None = None,
        top_k: int = 5,
    ) -> list[RetrievalResult]:

        bm25_results = self.bm25.search(
            query,
            top_k=self.top_k_each,
        )

        dense_results = self.dense.search(
            query,
            top_k=self.top_k_each,
        )

        graph_results = []

        if entity_name:
            graph_results = self.graph.search(
                entity_name,
                top_k=self.top_k_each,
            )

        return self.fusion.fuse(
            [
                bm25_results,
                dense_results,
                graph_results,
            ],
            top_k=top_k,
        )