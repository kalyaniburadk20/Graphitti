from dataclasses import dataclass


@dataclass
class ConfidenceResult:
    score: float
    sufficient: bool
    reason: str


class EvidenceChecker:

    def evaluate(
        self,
        results: list,
    ) -> ConfidenceResult:

        if not results:

            return ConfidenceResult(
                score=0.0,
                sufficient=False,
                reason="No retrieval results.",
            )

        # -------------------------------------------------
        # Remove invalid / empty results
        # -------------------------------------------------

        valid_results = [
            result
            for result in results
            if getattr(
                result,
                "text",
                "",
            ).strip()
        ]

        if not valid_results:

            return ConfidenceResult(
                score=0.0,
                sufficient=False,
                reason="Retrieved results contain no usable text.",
            )

        # -------------------------------------------------
        # Retrieval scores are NOT comparable across
        # BM25, Dense and Graph.
        #
        # Therefore we do not use a fixed numerical
        # threshold on result.score.
        # -------------------------------------------------

        top_result = max(
            valid_results,
            key=lambda result: result.score,
        )

        strategy = getattr(
            top_result,
            "strategy",
            "",
        )

        top_text = getattr(
            top_result,
            "text",
            "",
        ).strip()

        # -------------------------------------------------
        # Graph retrieval
        # -------------------------------------------------

        if strategy in {
            "graph",
            "graph_multi_hop",
        }:

            score = min(
                max(
                    float(
                        getattr(
                            top_result,
                            "confidence",
                            top_result.score,
                        )
                    ),
                    0.0,
                ),
                1.0,
            )

            sufficient = (
                bool(top_text)
                and score >= 0.70
            )

            return ConfidenceResult(
                score=score,
                sufficient=sufficient,
                reason=(
                    "Strong graph-backed evidence found."
                    if sufficient
                    else
                    "Graph evidence confidence is too low."
                ),
            )

        # -------------------------------------------------
        # Dense retrieval
        # -------------------------------------------------

        if strategy == "dense":

            # Cosine similarity for normalized
            # MiniLM embeddings is approximately
            # in the range [-1, 1].
            raw_score = float(
                top_result.score
            )

            normalized_score = max(
                0.0,
                min(
                    raw_score,
                    1.0,
                ),
            )

            sufficient = (
                bool(top_text)
                and normalized_score >= 0.55
            )

            return ConfidenceResult(
                score=normalized_score,
                sufficient=sufficient,
                reason=(
                    "Strong dense semantic evidence found."
                    if sufficient
                    else
                    "Dense evidence is too weak."
                ),
            )

        # -------------------------------------------------
        # BM25
        # -------------------------------------------------

        if strategy == "bm25":

            # BM25 scores are corpus-dependent and can
            # be greater than 1, so normalize only
            # relative to the best score in this result set.
            scores = [
                max(
                    float(
                        result.score
                    ),
                    0.0,
                )
                for result in valid_results
            ]

            best_score = max(
                scores
            )

            if best_score <= 0:

                normalized_score = 0.0

            else:

                normalized_score = 1.0

            sufficient = (
                bool(top_text)
                and best_score > 0
            )

            return ConfidenceResult(
                score=normalized_score,
                sufficient=sufficient,
                reason=(
                    "BM25 returned a non-zero "
                    "top-ranked result."
                    if sufficient
                    else
                    "BM25 returned no meaningful match."
                ),
            )

        # -------------------------------------------------
        # Hybrid / unknown strategy
        # -------------------------------------------------

        if strategy == "hybrid_rrf":

            # RRF score is also not naturally in [0, 1].
            # Presence of multiple supporting results is
            # more useful for this baseline.
            unique_chunks = {
                result.chunk_id
                for result in valid_results
            }

            sufficient = (
                bool(top_text)
                and len(unique_chunks) >= 1
            )

            return ConfidenceResult(
                score=1.0 if sufficient else 0.0,
                sufficient=sufficient,
                reason=(
                    "Hybrid retrieval returned usable evidence."
                    if sufficient
                    else
                    "Hybrid retrieval returned no usable evidence."
                ),
            )

        # -------------------------------------------------
        # Generic fallback
        # -------------------------------------------------

        sufficient = bool(
            top_text
        )

        return ConfidenceResult(
            score=1.0 if sufficient else 0.0,
            sufficient=sufficient,
            reason=(
                "Usable retrieval evidence found."
                if sufficient
                else
                "No usable retrieval evidence found."
            ),
        )