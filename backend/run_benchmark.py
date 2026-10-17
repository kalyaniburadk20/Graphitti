import json
import time
from dataclasses import replace
from pathlib import Path

from app.retrieval.routing_service import RoutingService
from app.retrieval.retrieval_models import RetrievalResult


# =========================================================
# PATHS
# =========================================================

BACKEND_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_ROOT.parent

GROUND_TRUTH_PATH = (
    PROJECT_ROOT
    / "data"
    / "benchmark"
    / "benchmark_ground_truth.json"
)

RESULTS_PATH = (
    PROJECT_ROOT
    / "data"
    / "benchmark"
    / "benchmark_results.json"
)


# =========================================================
# CONFIG
# =========================================================

TOP_K = 5

# Standard Reciprocal Rank Fusion constant.
RRF_K = 60

GENERAL_INTENTS = {
    "LEXICAL",
    "SEMANTIC",
    "RELATIONAL",
}


# =========================================================
# LOAD GROUND TRUTH
# =========================================================

def load_ground_truth():

    with GROUND_TRUTH_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


# =========================================================
# ENTITY EXTRACTION
# =========================================================

KNOWN_ENTITIES = [
    "FastAPI",
    "Pydantic",
    "Starlette",
    "OpenAPI",
    "Swagger",
    "HTTPX",
    "WebSockets",
    "OAuth2",
    "ORJSONResponse",
    "Uvicorn",
]


def extract_entity(query: str):

    query_lower = query.lower()

    for entity in KNOWN_ENTITIES:

        if entity.lower() in query_lower:
            return entity

    return None


# =========================================================
# SINGLE STRATEGY RETRIEVAL
# =========================================================

def retrieve(
    service,
    query,
    strategy,
    entity_name=None,
    top_k=TOP_K,
):

    start = time.perf_counter()

    results = service.search_with_strategies(
        query=query,
        strategies=[strategy],
        entity_name=entity_name,
        top_k=top_k,
    )

    latency_ms = (
        time.perf_counter() - start
    ) * 1000

    return results, latency_ms


# =========================================================
# RRF FUSION
# =========================================================

def reciprocal_rank_fusion(
    ranked_lists,
    top_k=TOP_K,
    rrf_k=RRF_K,
):
    """
    Fuse multiple ranked RetrievalResult lists
    using Reciprocal Rank Fusion.

    score(d) = sum(
        1 / (rrf_k + rank)
    )
    """

    fused_scores = {}
    representative_results = {}

    for results in ranked_lists:

        for rank, result in enumerate(
            results,
            start=1,
        ):

            chunk_id = result.chunk_id

            contribution = (
                1.0
                / (
                    rrf_k
                    + rank
                )
            )

            fused_scores[chunk_id] = (
                fused_scores.get(
                    chunk_id,
                    0.0,
                )
                + contribution
            )

            if chunk_id not in representative_results:
                representative_results[
                    chunk_id
                ] = result

    ranked = sorted(
        fused_scores.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    fused_results = []

    for chunk_id, score in ranked[:top_k]:

        original = representative_results[
            chunk_id
        ]

        fused_results.append(
            replace(
                original,
                score=score,
                strategy="hybrid_rrf",
            )
        )

    return fused_results


# =========================================================
# METRICS
# =========================================================

def recall_at_k(
    results,
    relevant_ids,
    k,
):
    """
    Binary Recall@K:
    1 if at least one relevant item
    appears in top-k, otherwise 0.
    """

    if not relevant_ids:
        return None

    relevant_ids = set(
        relevant_ids
    )

    retrieved_ids = {
        result.chunk_id
        for result in results[:k]
    }

    return (
        1.0
        if retrieved_ids.intersection(
            relevant_ids
        )
        else 0.0
    )


def reciprocal_rank(
    results,
    relevant_ids,
):
    """
    Reciprocal rank of the first relevant
    result.
    """

    if not relevant_ids:
        return None

    relevant_ids = set(
        relevant_ids
    )

    for rank, result in enumerate(
        results,
        start=1,
    ):

        if result.chunk_id in relevant_ids:

            return 1.0 / rank

    return 0.0


# =========================================================
# MULTI-HOP PATH EVALUATION
# =========================================================

def evaluate_multi_hop(
    service,
    item,
):

    expected = item.get(
        "expected_path"
    )

    if not expected:

        return {
            "path_found": False,
            "path_correct": False,
            "latency_ms": 0.0,
        }

    source = expected["source"]

    edges = expected["edges"]

    middle = expected["middle"]

    target = expected["target"]

    if len(edges) != 2:

        return {
            "path_found": False,
            "path_correct": False,
            "latency_ms": 0.0,
        }

    start = time.perf_counter()

    results = (
        service.graph.multi_hop_search(
            source_entity=source,
            first_predicate=edges[0],
            second_predicate=edges[1],
            target_entity=target,
            max_hops=2,
        )
    )

    latency_ms = (
        time.perf_counter() - start
    ) * 1000

    correct = False

    for result in results:

        result_source = result.get(
            "source"
        )

        result_middle = result.get(
            "middle"
        )

        result_target = result.get(
            "target"
        )

        result_first_predicate = (
            result.get(
                "first_predicate"
            )
        )

        result_second_predicate = (
            result.get(
                "second_predicate"
            )
        )

        if (
            str(result_source).lower()
            == source.lower()
            and str(result_middle).lower()
            == middle.lower()
            and str(result_target).lower()
            == target.lower()
            and str(
                result_first_predicate
            ).upper()
            == edges[0].upper()
            and str(
                result_second_predicate
            ).upper()
            == edges[1].upper()
        ):

            correct = True
            break

    return {
        "path_found": len(results) > 0,
        "path_correct": correct,
        "latency_ms": round(
            latency_ms,
            2,
        ),
    }


# =========================================================
# GENERAL QUERY EVALUATION
# =========================================================

def evaluate_general_query(
    service,
    item,
    strategy,
):
    """
    Evaluate one non-multi-hop query
    with one retrieval strategy.
    """

    query = item["query"]

    entity_name = extract_entity(
        query
    )

    results, latency_ms = retrieve(
        service=service,
        query=query,
        strategy=strategy,
        entity_name=entity_name,
        top_k=TOP_K,
    )

    relevant_ids = item.get(
        "relevant_chunk_ids",
        [],
    )

    return {
        "id": item["id"],
        "query": query,
        "intent": item["intent"],
        "strategy": strategy,
        "entity_name": entity_name,
        "retrieved": [
            {
                "chunk_id": result.chunk_id,
                "score": result.score,
            }
            for result in results
        ],
        "recall_at_1": recall_at_k(
            results,
            relevant_ids,
            1,
        ),
        "recall_at_3": recall_at_k(
            results,
            relevant_ids,
            3,
        ),
        "recall_at_5": recall_at_k(
            results,
            relevant_ids,
            5,
        ),
        "mrr": reciprocal_rank(
            results,
            relevant_ids,
        ),
        "latency_ms": round(
            latency_ms,
            2,
        ),
    }


# =========================================================
# HYBRID QUERY EVALUATION
# =========================================================

def evaluate_hybrid_query(
    service,
    item,
):
    """
    Run BM25 + Dense + Graph independently,
    then fuse their ranked lists with RRF.

    Only general (non-multi-hop) queries
    are evaluated here.
    """

    query = item["query"]

    entity_name = extract_entity(
        query
    )

    ranked_lists = []

    total_start = time.perf_counter()

    # -----------------------------------------------------
    # BM25
    # -----------------------------------------------------

    bm25_results, _ = retrieve(
        service=service,
        query=query,
        strategy="bm25",
        entity_name=entity_name,
        top_k=TOP_K,
    )

    ranked_lists.append(
        bm25_results
    )

    # -----------------------------------------------------
    # Dense
    # -----------------------------------------------------

    dense_results, _ = retrieve(
        service=service,
        query=query,
        strategy="dense",
        entity_name=entity_name,
        top_k=TOP_K,
    )

    ranked_lists.append(
        dense_results
    )

    # -----------------------------------------------------
    # Graph
    # -----------------------------------------------------

    graph_results, _ = retrieve(
        service=service,
        query=query,
        strategy="graph",
        entity_name=entity_name,
        top_k=TOP_K,
    )

    ranked_lists.append(
        graph_results
    )

    # -----------------------------------------------------
    # RRF
    # -----------------------------------------------------

    fused_results = (
        reciprocal_rank_fusion(
            ranked_lists,
            top_k=TOP_K,
            rrf_k=RRF_K,
        )
    )

    total_latency_ms = (
        time.perf_counter()
        - total_start
    ) * 1000

    relevant_ids = item.get(
        "relevant_chunk_ids",
        [],
    )

    return {
        "id": item["id"],
        "query": query,
        "intent": item["intent"],
        "strategy": "hybrid_rrf",
        "entity_name": entity_name,
        "retrieved": [
            {
                "chunk_id": result.chunk_id,
                "score": result.score,
            }
            for result in fused_results
        ],
        "recall_at_1": recall_at_k(
            fused_results,
            relevant_ids,
            1,
        ),
        "recall_at_3": recall_at_k(
            fused_results,
            relevant_ids,
            3,
        ),
        "recall_at_5": recall_at_k(
            fused_results,
            relevant_ids,
            5,
        ),
        "mrr": reciprocal_rank(
            fused_results,
            relevant_ids,
        ),
        "latency_ms": round(
            total_latency_ms,
            2,
        ),
    }


# =========================================================
# SUMMARY
# =========================================================

def summarize(
    query_results,
):

    if not query_results:

        return {
            "num_queries": 0,
            "avg_recall_at_1": None,
            "avg_recall_at_3": None,
            "avg_recall_at_5": None,
            "mrr": None,
            "avg_latency_ms": None,
        }

    summary = {
        "num_queries": len(
            query_results
        ),
        "avg_recall_at_1": round(
            sum(
                item["recall_at_1"]
                for item in query_results
            )
            / len(query_results),
            4,
        ),
        "avg_recall_at_3": round(
            sum(
                item["recall_at_3"]
                for item in query_results
            )
            / len(query_results),
            4,
        ),
        "avg_recall_at_5": round(
            sum(
                item["recall_at_5"]
                for item in query_results
            )
            / len(query_results),
            4,
        ),
        "mrr": round(
            sum(
                item["mrr"]
                for item in query_results
            )
            / len(query_results),
            4,
        ),
        "avg_latency_ms": round(
            sum(
                item["latency_ms"]
                for item in query_results
            )
            / len(query_results),
            2,
        ),
    }

    return summary


# =========================================================
# MAIN
# =========================================================

def main():

    print("=" * 80)
    print("GRAPHITTI RETRIEVAL ABLATION BENCHMARK")
    print("=" * 80)

    benchmark = load_ground_truth()

    print(
        f"Loaded {len(benchmark)} benchmark queries."
    )

    general_queries = [
        item
        for item in benchmark
        if item["intent"] in GENERAL_INTENTS
    ]

    multi_hop_queries = [
        item
        for item in benchmark
        if item["intent"] == "MULTI_HOP"
    ]

    print(
        f"General retrieval queries: "
        f"{len(general_queries)}"
    )

    print(
        f"Multi-hop queries: "
        f"{len(multi_hop_queries)}"
    )

    service = RoutingService()

    all_results = {}

    try:

        # =================================================
        # BASE RETRIEVERS
        # =================================================

        for strategy in [
            "bm25",
            "dense",
            "graph",
        ]:

            print()
            print("=" * 80)
            print(
                f"EVALUATING: {strategy.upper()}"
            )
            print("=" * 80)

            query_results = []

            for item in general_queries:

                result = evaluate_general_query(
                    service=service,
                    item=item,
                    strategy=strategy,
                )

                query_results.append(
                    result
                )

            summary = summarize(
                query_results
            )

            all_results[strategy] = {
                "summary": summary,
                "queries": query_results,
            }

            print(
                json.dumps(
                    summary,
                    indent=2,
                )
            )

        # =================================================
        # HYBRID / RRF
        # =================================================

        print()
        print("=" * 80)
        print("EVALUATING: HYBRID / RRF")
        print("=" * 80)

        hybrid_results = []

        for item in general_queries:

            result = evaluate_hybrid_query(
                service=service,
                item=item,
            )

            hybrid_results.append(
                result
            )

        hybrid_summary = summarize(
            hybrid_results
        )

        all_results["hybrid_rrf"] = {
            "summary": hybrid_summary,
            "queries": hybrid_results,
        }

        print(
            json.dumps(
                hybrid_summary,
                indent=2,
            )
        )

        # =================================================
        # MULTI-HOP
        # =================================================

        print()
        print("=" * 80)
        print("EVALUATING: MULTI-HOP GRAPH PATHS")
        print("=" * 80)

        multi_hop_results = []

        for item in multi_hop_queries:

            result = evaluate_multi_hop(
                service=service,
                item=item,
            )

            multi_hop_results.append(
                {
                    "id": item["id"],
                    "query": item["query"],
                    "intent": item["intent"],
                    "strategy": "graph_multi_hop",
                    **result,
                }
            )

            print()
            print(
                f"{item['id']}: "
                f"{item['query']}"
            )

            print(
                f"  Path found: "
                f"{result['path_found']}"
            )

            print(
                f"  Path correct: "
                f"{result['path_correct']}"
            )

            print(
                f"  Latency: "
                f"{result['latency_ms']} ms"
            )

        path_accuracy = None

        if multi_hop_results:

            path_accuracy = round(
                sum(
                    1
                    for item in multi_hop_results
                    if item["path_correct"]
                )
                / len(multi_hop_results),
                4,
            )

        multi_hop_summary = {
            "num_queries": len(
                multi_hop_results
            ),
            "path_accuracy": (
                path_accuracy
            ),
            "avg_latency_ms": (
                round(
                    sum(
                        item["latency_ms"]
                        for item in multi_hop_results
                    )
                    / len(
                        multi_hop_results
                    ),
                    2,
                )
                if multi_hop_results
                else None
            ),
        }

        all_results["multi_hop"] = {
            "summary": multi_hop_summary,
            "queries": multi_hop_results,
        }

        print()
        print(
            json.dumps(
                multi_hop_summary,
                indent=2,
            )
        )

    finally:

        service.graph.close()

    # =====================================================
    # SAVE RESULTS
    # =====================================================

    with RESULTS_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            all_results,
            file,
            indent=2,
            ensure_ascii=False,
        )

    # =====================================================
    # FINAL COMPARISON
    # =====================================================

    print()
    print("=" * 80)
    print("FINAL GENERAL RETRIEVAL COMPARISON")
    print("=" * 80)

    header = (
        f"{'Strategy':<15}"
        f"{'R@1':>10}"
        f"{'R@3':>10}"
        f"{'R@5':>10}"
        f"{'MRR':>10}"
        f"{'Latency':>14}"
    )

    print(header)
    print("-" * 69)

    for strategy in [
        "bm25",
        "dense",
        "graph",
        "hybrid_rrf",
    ]:

        summary = all_results[
            strategy
        ]["summary"]

        print(
            f"{strategy:<15}"
            f"{summary['avg_recall_at_1']:>10.4f}"
            f"{summary['avg_recall_at_3']:>10.4f}"
            f"{summary['avg_recall_at_5']:>10.4f}"
            f"{summary['mrr']:>10.4f}"
            f"{summary['avg_latency_ms']:>14.2f}"
        )

    print()
    print("=" * 80)
    print("MULTI-HOP GRAPH RESULT")
    print("=" * 80)

    print(
        f"Path Accuracy: "
        f"{multi_hop_summary['path_accuracy']}"
    )

    print(
        f"Average Latency: "
        f"{multi_hop_summary['avg_latency_ms']} ms"
    )

    print()
    print("=" * 80)
    print("BENCHMARK COMPLETE")
    print("=" * 80)

    print(
        f"Results saved to:\n"
        f"{RESULTS_PATH}"
    )


if __name__ == "__main__":
    main()