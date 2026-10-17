import hashlib
import re

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from app.extraction.document_models import StructuredDocument
from .chunking_models import SemanticChunk


class SemanticChunker:

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        similarity_threshold: float = 0.55,
        max_words: int = 180,
    ):
        self.model = SentenceTransformer(model_name)
        self.similarity_threshold = similarity_threshold
        self.max_words = max_words

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """
        Rough token estimate.
        Later we can replace this with the
        tokenizer of the final embedding/LLM model.
        """
        return max(1, len(text.split()))

    @staticmethod
    def _split_into_sentences(text: str) -> list[str]:
        sentences = re.split(
            r"(?<=[.!?])\s+",
            text.strip(),
        )

        return [
            sentence.strip()
            for sentence in sentences
            if sentence.strip()
        ]

    @staticmethod
    def _chunk_id(
        url: str,
        heading: str,
        index: int,
        text: str,
    ) -> str:
        raw = f"{url}|{heading}|{index}|{text}"

        return hashlib.sha1(
            raw.encode("utf-8")
        ).hexdigest()[:16]

    def _build_chunk(
        self,
        document: StructuredDocument,
        heading: str,
        level: int,
        text: str,
        index: int,
    ) -> SemanticChunk:

        return SemanticChunk(
            chunk_id=self._chunk_id(
                document.url,
                heading,
                index,
                text,
            ),
            document_url=document.url,
            section_heading=heading,
            section_level=level,
            text=text.strip(),
            chunk_index=index,
            token_estimate=self._estimate_tokens(text),
        )

    def chunk_document(
        self,
        document: StructuredDocument,
    ) -> list[SemanticChunk]:

        chunks: list[SemanticChunk] = []

        global_chunk_index = 0

        for section in document.sections:

            paragraphs = self._split_into_sentences(
                section.content
            )

            if not paragraphs:
                continue

            current_group = [
                paragraphs[0]
            ]

            previous_embedding = (
                self.model.encode(
                    [paragraphs[0]]
                )[0]
            )

            for paragraph in paragraphs[1:]:

                current_embedding = (
                    self.model.encode(
                        [paragraph]
                    )[0]
                )

                similarity = cosine_similarity(
                    [previous_embedding],
                    [current_embedding],
                )[0][0]

                current_text = " ".join(
                    current_group
                )

                exceeds_size = (
                    len(current_text.split())
                    >= self.max_words
                )

                if (
                    similarity < self.similarity_threshold
                    or exceeds_size
                ):
                    chunks.append(
                        self._build_chunk(
                            document=document,
                            heading=section.heading,
                            level=section.level,
                            text=current_text,
                            index=global_chunk_index,
                        )
                    )

                    global_chunk_index += 1

                    current_group = [
                        paragraph
                    ]

                else:
                    current_group.append(
                        paragraph
                    )

                previous_embedding = (
                    current_embedding
                )

            # Store remaining text.
            if current_group:

                chunks.append(
                    self._build_chunk(
                        document=document,
                        heading=section.heading,
                        level=section.level,
                        text=" ".join(
                            current_group
                        ),
                        index=global_chunk_index,
                    )
                )

                global_chunk_index += 1

        return chunks