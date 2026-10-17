import json
from pathlib import Path
from collections import defaultdict


# =========================================================
# PATHS
# =========================================================

BACKEND_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_ROOT.parent

RESULTS_PATH = (
    PROJECT_ROOT
    / "data"
    / "benchmark"
    / "benchmark_results.json"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "benchmark"
    / "benchmark_analysis.json"
)


# =========================================================
# LOAD RESULTS
# =========================================================

def load_results():

    with RESULTS_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


# =========================================================
# GENERAL QUERY ANALYSIS
# =========================================================

def analyze_general_results(data):

    strategies = [
        "bm25",
        "dense",
        "graph",
        "hybrid_rrf",
    ]

    # -----------------------------------------------------
    # query_id -> strategy -> result
    # -----------------------------------------------------

    by_query = defaultdict(dict)

    for strategy in strategies:

        strategy_data = data.get(
            strategy,
            {},
        )

        for item in strategy_data.get(
            "queries",
            [],
        ):

            by_query[
                item["id"]
            ][strategy] = item

    # -----------------------------------------------------
    # Per-query comparison
    # -----------------------------------------------------

    query_analysis = []

    for query_id in sorted(by_query):

        strategy_results = by_query[
            query_id
        ]

        first_result = next(
            iter(
                strategy_results.values()
            )
        )

        row = {
            "id": query_id,
            "query": first_result["query"],
            "intent": first_result["intent"],
            "strategies": {},
        }

        for strategy in strategies:

            result = strategy_results.get(
                strategy
            )

            if result is None:

                row["strategies"][
                    strategy
                ] = None

                continue

            row["strategies"][
                strategy
            ] = {
                "hit_at_1": bool(
                    result["recall_at_1"]
                ),
                "hit_at_3": bool(
                    result["recall_at_3"]
                ),
                "hit_at_5": bool(
                    result["recall_at_5"]
                ),
                "mrr": result["mrr"],
                "latency_ms": result[
                    "latency_ms"
                ],
                "retrieved_chunk_ids": [
                    item["chunk_id"]
                    for item in result[
                        "retrieved"
                    ]
                ],
            }

        # -------------------------------------------------
        # Winner by MRR
        # -------------------------------------------------

        valid = {
            strategy: result
            for strategy, result
            in row["strategies"].items()
            if result is not None
        }

        if valid:

            best_strategy = max(
                valid,
                key=lambda strategy: (
                    valid[strategy]["mrr"]
                ),
            )

            row["best_strategy_by_mrr"] = (
                best_strategy
            )

        query_analysis.append(
            row
        )

    return query_analysis


# =========================================================
# INTENT-WISE ANALYSIS
# =========================================================

def analyze_by_intent(
    query_analysis,
):

    strategies = [
        "bm25",
        "dense",
        "graph",
        "hybrid_rrf",
    ]

    grouped = defaultdict(
        lambda: defaultdict(list)
    )

    for query in query_analysis:

        intent = query["intent"]

        for strategy in strategies:

            result = query[
                "strategies"
            ].get(strategy)

            if result is not None:

                grouped[intent][
                    strategy
                ].append(result)

    summary = {}

    for intent, strategy_data in grouped.items():

        summary[intent] = {}

        for strategy in strategies:

            results = strategy_data.get(
                strategy,
                [],
            )

            if not results:
                continue

            summary[intent][strategy] = {
                "num_queries": len(results),

                "hit_at_1": round(
                    sum(
                        1
                        for item in results
                        if item["hit_at_1"]
                    )
                    / len(results),
                    4,
                ),

                "hit_at_3": round(
                    sum(
                        1
                        for item in results
                        if item["hit_at_3"]
                    )
                    / len(results),
                    4,
                ),

                "hit_at_5": round(
                    sum(
                        1
                        for item in results
                        if item["hit_at_5"]
                    )
                    / len(results),
                    4,
                ),

                "mrr": round(
                    sum(
                        item["mrr"]
                        for item in results
                    )
                    / len(results),
                    4,
                ),

                "avg_latency_ms": round(
                    sum(
                        item["latency_ms"]
                        for item in results
                    )
                    / len(results),
                    2,
                ),
            }

    return summary


# =========================================================
# FAILURE ANALYSIS
# =========================================================

def analyze_failures(
    query_analysis,
):

    strategies = [
        "bm25",
        "dense",
        "graph",
        "hybrid_rrf",
    ]

    failures = []

    for query in query_analysis:

        failed = []
        succeeded = []

        for strategy in strategies:

            result = query[
                "strategies"
            ].get(strategy)

            if result is None:
                continue

            if result["hit_at_5"]:
                succeeded.append(
                    strategy
                )
            else:
                failed.append(
                    strategy
                )

        if failed:

            failures.append(
                {
                    "id": query["id"],
                    "query": query["query"],
                    "intent": query["intent"],
                    "failed_at_recall_5": failed,
                    "succeeded_at_recall_5": (
                        succeeded
                    ),
                }
            )

    return failures


# =========================================================
# STRATEGY WINS
# =========================================================

def count_strategy_wins(
    query_analysis,
):

    wins = defaultdict(int)

    for query in query_analysis:

        best = query.get(
            "best_strategy_by_mrr"
        )

        if best:
            wins[best] += 1

    return dict(wins)


# =========================================================
# PRINT QUERY MATRIX
# =========================================================

def print_query_matrix(
    query_analysis,
):

    print()
    print("=" * 110)
    print("PER-QUERY RESULTS")
    print("=" * 110)

    header = (
        f"{'ID':<6}"
        f"{'Intent':<14}"
        f"{'BM25':>12}"
        f"{'Dense':>12}"
        f"{'Graph':>12}"
        f"{'Hybrid':>12}"
        f"{'Winner':>14}"
    )

    print(header)
    print("-" * 110)

    for query in query_analysis:

        values = []

        for strategy in [
            "bm25",
            "dense",
            "graph",
            "hybrid_rrf",
        ]:

            result = query[
                "strategies"
            ].get(strategy)

            if result is None:
                values.append("-")
            else:
                values.append(
                    "✅"
                    if result["hit_at_5"]
                    else "❌"
                )

        winner = query.get(
            "best_strategy_by_mrr",
            "-",
        )

        print(
            f"{query['id']:<6}"
            f"{query['intent']:<14}"
            f"{values[0]:>12}"
            f"{values[1]:>12}"
            f"{values[2]:>12}"
            f"{values[3]:>12}"
            f"{winner:>14}"
        )


# =========================================================
# PRINT INTENT SUMMARY
# =========================================================

def print_intent_summary(
    intent_summary,
):

    print()
    print("=" * 110)
    print("INTENT-WISE PERFORMANCE")
    print("=" * 110)

    for intent, strategies in intent_summary.items():

        print()
        print(
            f"--- {intent} ---"
        )

        header = (
            f"{'Strategy':<15}"
            f"{'Hit@1':>10}"
            f"{'Hit@3':>10}"
            f"{'Hit@5':>10}"
            f"{'MRR':>10}"
            f"{'Latency':>14}"
        )

        print(header)
        print("-" * 75)

        for strategy, metrics in strategies.items():

            print(
                f"{strategy:<15}"
                f"{metrics['hit_at_1']:>10.4f}"
                f"{metrics['hit_at_3']:>10.4f}"
                f"{metrics['hit_at_5']:>10.4f}"
                f"{metrics['mrr']:>10.4f}"
                f"{metrics['avg_latency_ms']:>14.2f}"
            )


# =========================================================
# MAIN
# =========================================================

def main():

    print("=" * 110)
    print("GRAPHITTI BENCHMARK ERROR ANALYSIS")
    print("=" * 110)

    data = load_results()

    # -----------------------------------------------------
    # General retrieval
    # -----------------------------------------------------

    query_analysis = analyze_general_results(
        data
    )

    intent_summary = analyze_by_intent(
        query_analysis
    )

    failures = analyze_failures(
        query_analysis
    )

    wins = count_strategy_wins(
        query_analysis
    )

    # -----------------------------------------------------
    # Multi-hop
    # -----------------------------------------------------

    multi_hop = data.get(
        "multi_hop",
        {},
    )

    # -----------------------------------------------------
    # Final analysis object
    # -----------------------------------------------------

    analysis = {
        "query_matrix": query_analysis,

        "intent_summary": intent_summary,

        "failures": failures,

        "strategy_wins_by_mrr": wins,

        "multi_hop": (
            multi_hop.get(
                "summary",
                {},
            )
        ),
    }

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            analysis,
            file,
            indent=2,
            ensure_ascii=False,
        )

    # -----------------------------------------------------
    # Display
    # -----------------------------------------------------

    print_query_matrix(
        query_analysis
    )

    print_intent_summary(
        intent_summary
    )

    print()
    print("=" * 110)
    print("STRATEGY WINS BY MRR")
    print("=" * 110)

    for strategy, count in sorted(
        wins.items(),
        key=lambda item: item[1],
        reverse=True,
    ):

        print(
            f"{strategy:<20} {count}"
        )

    print()
    print("=" * 110)
    print("RECALL@5 FAILURES")
    print("=" * 110)

    if not failures:

        print(
            "No Recall@5 failures found."
        )

    else:

        for item in failures:

            print()
            print(
                f"{item['id']}: "
                f"{item['query']}"
            )

            print(
                f"  Intent: "
                f"{item['intent']}"
            )

            print(
                f"  Failed: "
                f"{', '.join(item['failed_at_recall_5'])}"
            )

            print(
                f"  Succeeded: "
                f"{', '.join(item['succeeded_at_recall_5'])}"
            )

    print()
    print("=" * 110)
    print("MULTI-HOP")
    print("=" * 110)

    print(
        json.dumps(
            multi_hop.get(
                "summary",
                {},
            ),
            indent=2,
        )
    )

    print()
    print("=" * 110)
    print("ANALYSIS COMPLETE")
    print("=" * 110)

    print(
        f"Saved to:\n{OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()