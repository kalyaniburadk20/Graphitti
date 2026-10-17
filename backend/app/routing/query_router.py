import re

from .query_models import RoutingDecision


class QueryRouter:

    RELATIONAL_PATTERNS = [
        r"\bwhat does .* depend on\b",
        r"\bwhat dependencies does .* have\b",
        r"\bwhat does .* use\b",
        r"\bwhat supports .*\b",
        r"\bwhat is .* built on\b",
        r"\bwhat does .* provide\b",
        r"\bwhat is compatible with\b",
    ]

    LEXICAL_PATTERNS = [
    r"\bwhich page\b",
    r"\bwhere is\b",
    r"\bfind the page\b",
    r"\bfind the documentation\b",
    r"\bfind documentation\b",
    r"\bmention(ed|s)\b",
    r"\bwhich document\b",
    r"\bwhere does the documentation\b",
    r"\bshow me the documentation\b",
    ]
    MULTI_HOP_PATTERNS = [
        r"\bthat also\b",
        r"\bwhich .* uses\b",
        r"\bthrough\b",
        r"\brelated to\b",
        r"\bconnected to\b",
        r"\bhow are .* connected\b",
    ]

    SEMANTIC_PATTERNS = [
        r"\bexplain\b",
        r"\bwhat is\b",
        r"\bwhat are\b",
        r"\bhow does .* work\b",
        r"\bwhy\b",
        r"\bdescribe\b",
    ]

    def classify(
        self,
        query: str,
    ) -> RoutingDecision:

        normalized = query.lower().strip()

        # -------------------------------------------------
        # Multi-hop should have highest priority.
        # -------------------------------------------------

        if self._matches(
            normalized,
            self.MULTI_HOP_PATTERNS,
        ):
            return RoutingDecision(
                query=query,
                intent="MULTI_HOP",
                confidence=0.95,
                retrievers=[
                    "graph",
                    "dense",
                    "bm25",
                ],
                reason=(
                    "Query contains a multi-hop "
                    "or cross-entity relationship."
                ),
            )

        # -------------------------------------------------
        # Relational
        # -------------------------------------------------

        if self._matches(
            normalized,
            self.RELATIONAL_PATTERNS,
        ):
            return RoutingDecision(
                query=query,
                intent="RELATIONAL",
                confidence=0.92,
                retrievers=[
                    "bm25",
                    "graph",
                ],
                reason=(
                    "Query asks about an explicit "
                    "relationship between entities."
                ),
            )

        # -------------------------------------------------
        # Lexical
        # -------------------------------------------------

        if self._matches(
            normalized,
            self.LEXICAL_PATTERNS,
        ):
            return RoutingDecision(
                query=query,
                intent="LEXICAL",
                confidence=0.90,
                retrievers=[
                    "bm25",
                ],
                reason=(
                    "Query asks to locate or "
                    "match specific documentation text."
                ),
            )

        # -------------------------------------------------
        # Semantic
        # -------------------------------------------------

        if self._matches(
            normalized,
            self.SEMANTIC_PATTERNS,
        ):
            return RoutingDecision(
                query=query,
                intent="SEMANTIC",
                confidence=0.85,
                retrievers=[
                    "bm25",
                    "graph",
                ],
                reason=(
                    "Query asks for an explanation "
                    "or conceptual understanding."
                ),
            )

        # -------------------------------------------------
        # Fallback
        # -------------------------------------------------

        return RoutingDecision(
            query=query,
            intent="HYBRID",
            confidence=0.50,
            retrievers=[
                "bm25",
                "dense",
                "graph",
            ],
            reason=(
                "No specific intent pattern matched; "
                "use the hybrid retrieval strategy."
            ),
        )

    @staticmethod
    def _matches(
        query: str,
        patterns: list[str],
    ) -> bool:

        return any(
            re.search(
                pattern,
                query,
            )
            for pattern in patterns
        )