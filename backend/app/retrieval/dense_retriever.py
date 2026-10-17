import json
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from .retrieval_models import RetrievalResult


class DenseRetriever:

    def __init__(
        self,
        chunks_file: str | None = None,
        model_name: str = "all-MiniLM-L6-v2",
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

        self.model = SentenceTransformer(
            model_name
        )

        self.chunks = []
        self.embeddings = None
        self.index = None

        self._load_chunks()
        self._build_index()

    def _load_chunks(self):

        if not self.chunks_file.exists():
            raise FileNotFoundError(
                f"Chunks file not found: "
                f"{self.chunks_file}"
            )

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

        if not self.chunks:
            raise ValueError(
                "No chunks found."
            )

    def _build_index(self):

        texts = [
            chunk["text"]
            for chunk in self.chunks
        ]

        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True,
        )

        embeddings = np.asarray(
            embeddings,
            dtype="float32",
        )

        self.embeddings = embeddings

        dimension = embeddings.shape[1]

        # Inner product on normalized vectors
        # is cosine similarity.
        self.index = faiss.IndexFlatIP(
            dimension
        )

        self.index.add(
            embeddings
        )

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[RetrievalResult]:

        if not query.strip():
            return []

        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        query_embedding = np.asarray(
            query_embedding,
            dtype="float32",
        )

        scores, indices = (
            self.index.search(
                query_embedding,
                top_k,
            )
        )

        results = []

        for score, index in zip(
            scores[0],
            indices[0],
        ):

            if index < 0:
                continue

            chunk = self.chunks[
                int(index)
            ]

            results.append(
                RetrievalResult(
                    chunk_id=chunk["chunk_id"],
                    text=chunk["text"],
                    score=float(score),
                    source_url=(
                        chunk["document_url"]
                    ),
                    section_heading=(
                        chunk["section_heading"]
                    ),
                    strategy="dense",
                )
            )

        return results