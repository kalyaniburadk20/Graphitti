import json
import time
from pathlib import Path

from app.retrieval.bm25_retriever import (
    BM25Retriever,
)

from app.retrieval.dense_retriever import (
    DenseRetriever,
)

from app.evaluation.retrieval_metrics import (
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
    ndcg_at_k,
)


PROJECT_ROOT = (
    Path(__file__).resolve().parents[1]
)

TEST_FILE = (
    PROJECT_ROOT
    / "data"
    / "evaluation"
    / "retrieval_test.jsonl"
)


def load_queries():

    with TEST_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:

        return [
            json.loads(line)
            for line in file
            if line.strip()
        ]


def evaluate_retriever(
    retriever,
    queries,
    name,
    top_k=5,
):

    precision_scores = []
    recall_scores = []
    mrr_scores = []
    ndcg_scores = []
    latencies = []

    print(
        f"\n========== {name.upper()} ==========\n"
    )

    for item in queries:

        query = item["query"]

        gold = set(
            item["gold_chunk_ids"]
        )

        start = time.perf_counter()

        results = retriever.search(
            query,
            top_k=top_k,
        )

        elapsed = (
            time.perf_counter()
            - start
        )

        predicted = [
            result.chunk_id
            for result in results
        ]

        precision_scores.append(
            precision_at_k(
                predicted,
                gold,
                top_k,
            )
        )

        recall_scores.append(
            recall_at_k(
                predicted,
                gold,
                top_k,
            )
        )

        mrr_scores.append(
            reciprocal_rank(
                predicted,
                gold,
            )
        )

        ndcg_scores.append(
            ndcg_at_k(
                predicted,
                gold,
                top_k,
            )
        )

        latencies.append(
            elapsed * 1000
        )

        print(
            f"\nQuery: {query}"
        )

        print(
            f"Gold: {gold}"
        )

        print(
            f"Predicted: "
            f"{predicted}"
        )

        print(
            f"Latency: "
            f"{elapsed * 1000:.2f} ms"
        )

    count = len(queries)

    print(
        "\n-------- SUMMARY --------"
    )

    print(
        f"Precision@{top_k}: "
        f"{sum(precision_scores) / count:.4f}"
    )

    print(
        f"Recall@{top_k}: "
        f"{sum(recall_scores) / count:.4f}"
    )

    print(
        f"MRR: "
        f"{sum(mrr_scores) / count:.4f}"
    )

    print(
        f"nDCG@{top_k}: "
        f"{sum(ndcg_scores) / count:.4f}"
    )

    print(
        f"Mean latency: "
        f"{sum(latencies) / count:.2f} ms"
    )


queries = load_queries()

bm25 = BM25Retriever()
dense = DenseRetriever()

evaluate_retriever(
    bm25,
    queries,
    "BM25",
)

evaluate_retriever(
    dense,
    queries,
    "Dense",
)