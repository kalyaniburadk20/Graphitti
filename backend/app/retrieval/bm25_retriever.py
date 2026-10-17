import re
from pathlib import Path

from rank_bm25 import BM25Okapi
from .retrieval_models import RetrievalResult


class BM25Retriever:

    def __init__(
        self,
        chunks_file: str | None = None,
    ):
        if chunks_file is None:
            project_root = (
                Path(__file__)
                .resolve()
                .parents[3]
            )

            chunks_file = str(
                project_root
                / "data"
                / "processed"
                / "semantic_chunks.jsonl"
            )

        self.chunks_file = Path(
            chunks_file
        )

        self.chunks = []
        self.tokenized_corpus = []
        self.bm25 = None

        self._load_chunks()
        self._build_index()

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(
            r"\b\w+\b",
            text.lower(),
        )

    def _load_chunks(self):

        if not self.chunks_file.exists():
            raise FileNotFoundError(
                f"Chunks file not found: "
                f"{self.chunks_file}"
            )

        import json

        with self.chunks_file.open(
            "r",
            encoding="utf-8",
        ) as file:

            for line in file:

                line = line.strip()

                if not line:
                    continue

                self.chunks.append(
                    json.loads(line)
                )

    def _build_index(self):

        self.tokenized_corpus = [
            self._tokenize(
                chunk["text"]
            )
            for chunk in self.chunks
        ]

        if not self.tokenized_corpus:
            raise ValueError(
                "No chunks available "
                "for BM25 indexing."
            )

        self.bm25 = BM25Okapi(
            self.tokenized_corpus
        )

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict]:

        if not query.strip():
            return []

        query_tokens = self._tokenize(
            query
        )

        scores = self.bm25.get_scores(
            query_tokens
        )

        ranked_indices = sorted(
            range(len(scores)),
            key=lambda index: scores[index],
            reverse=True,
        )

        results = []

        for index in ranked_indices[:top_k]:

            chunk = dict(
                self.chunks[index]
            )

            chunk["score"] = float(
                scores[index]
            )

            results.append(
    RetrievalResult(
        chunk_id=chunk["chunk_id"],
        text=chunk["text"],
        score=float(
            scores[index]
        ),
        source_url=chunk["document_url"],
        section_heading=chunk[
            "section_heading"
        ],
        strategy="bm25",
    )
)

        return results