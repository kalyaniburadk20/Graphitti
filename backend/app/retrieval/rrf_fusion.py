from collections import defaultdict

from .retrieval_models import RetrievalResult


class RRFFusion:

    def __init__(
        self,
        k: int = 60,
    ):
        self.k = k

    def fuse(
        self,
        result_lists: list[list[RetrievalResult]],
        top_k: int = 10,
    ) -> list[RetrievalResult]:

        scores = defaultdict(float)
        result_by_chunk = {}

        for results in result_lists:

            for rank, result in enumerate(
                results,
                start=1,
            ):

                chunk_id = result.chunk_id

                scores[chunk_id] += (
                    1.0
                    / (self.k + rank)
                )

                # Keep the best representation
                # we've seen for this chunk.
                if (
                    chunk_id
                    not in result_by_chunk
                ):
                    result_by_chunk[
                        chunk_id
                    ] = result

        ranked_chunk_ids = sorted(
            scores,
            key=lambda chunk_id: scores[
                chunk_id
            ],
            reverse=True,
        )

        fused_results = []

        for chunk_id in ranked_chunk_ids[:top_k]:

            original = result_by_chunk[
                chunk_id
            ]

            fused_results.append(
                RetrievalResult(
                    chunk_id=original.chunk_id,
                    text=original.text,
                    score=scores[chunk_id],
                    source_url=original.source_url,
                    section_heading=(
                        original.section_heading
                    ),
                    strategy="hybrid_rrf",
                )
            )

        return fused_results