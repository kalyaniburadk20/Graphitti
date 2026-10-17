def precision_at_k(
    predicted: list[str],
    gold: set[str],
    k: int,
) -> float:

    if k <= 0:
        return 0.0

    predicted_k = predicted[:k]

    if not predicted_k:
        return 0.0

    hits = sum(
        1
        for chunk_id in predicted_k
        if chunk_id in gold
    )

    return hits / len(predicted_k)


def recall_at_k(
    predicted: list[str],
    gold: set[str],
    k: int,
) -> float:

    if not gold:
        return 0.0

    predicted_k = predicted[:k]

    hits = sum(
        1
        for chunk_id in predicted_k
        if chunk_id in gold
    )

    return hits / len(gold)


def reciprocal_rank(
    predicted: list[str],
    gold: set[str],
) -> float:

    for rank, chunk_id in enumerate(
        predicted,
        start=1,
    ):

        if chunk_id in gold:
            return 1.0 / rank

    return 0.0


def ndcg_at_k(
    predicted: list[str],
    gold: set[str],
    k: int,
) -> float:

    import math

    predicted_k = predicted[:k]

    dcg = 0.0

    for rank, chunk_id in enumerate(
        predicted_k,
        start=1,
    ):

        relevance = (
            1
            if chunk_id in gold
            else 0
        )

        if relevance:
            dcg += (
                relevance
                / math.log2(rank + 1)
            )

    ideal_hits = min(
        len(gold),
        k,
    )

    if ideal_hits == 0:
        return 0.0

    idcg = sum(
        1.0 / math.log2(rank + 1)
        for rank in range(
            1,
            ideal_hits + 1,
        )
    )

    return dcg / idcg