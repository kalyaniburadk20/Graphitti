import os
from typing import Any

from dotenv import load_dotenv
from neo4j import GraphDatabase

from app.retrieval.retrieval_models import RetrievalResult

load_dotenv()

class GraphRetriever:

    def __init__(
        self,
        uri: str | None = None,
        username: str | None = None,
        password: str | None = None,
    ):
        self.uri = uri or os.getenv(
            "NEO4J_URI",
            "bolt://localhost:7687",
        )

        self.username = username or os.getenv(
            "NEO4J_USERNAME",
            "neo4j",
        )

        self.password = password or os.getenv(
            "NEO4J_PASSWORD",
            "",
        )

        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(
                self.username,
                self.password,
            ),
        )

    # =========================================================
    # ENTITY LOOKUP
    # =========================================================

    def find_entity(
        self,
        entity_name: str,
    ):

        query = """
        MATCH (e:Entity)
        WHERE toLower(e.name) = toLower($name)
        RETURN
            e.entity_id AS entity_id,
            e.name AS name,
            e.type AS type
        LIMIT 10
        """

        with self.driver.session() as session:

            result = session.run(
                query,
                name=entity_name,
            )

            return [
                record.data()
                for record in result
            ]

    # =========================================================
    # NEIGHBOR LOOKUP
    # =========================================================

    def get_neighbors(
        self,
        entity_id: str,
        max_hops: int = 1,
    ):

        if max_hops < 1:
            return []

        # -----------------------------------------------------
        # Keep Cypher bounded.
        # -----------------------------------------------------

        hops = min(
            int(max_hops),
            3,
        )

        query = f"""
        MATCH path =
            (source:Entity)-[*1..{hops}]-(target:Entity)

        WHERE source.entity_id = $entity_id

        RETURN
            source.name AS source,
            target.name AS target,
            length(path) AS hops,
            [r IN relationships(path) | type(r)] AS predicates
        LIMIT 100
        """

        with self.driver.session() as session:

            result = session.run(
                query,
                entity_id=entity_id,
            )

            return [
                record.data()
                for record in result
            ]

    # =========================================================
    # CLAIMS FOR ENTITY
    # =========================================================

    def get_claims_for_entity(
        self,
        entity_id: str,
    ):

        query = """
        MATCH (claim:Claim)
        MATCH (claim)-[:ABOUT_SUBJECT]->(subject:Entity)
        MATCH (claim)-[:ABOUT_OBJECT]->(object:Entity)
        MATCH (claim)-[:EXTRACTED_FROM]->(chunk:Chunk)

        WHERE
            subject.entity_id = $entity_id
            OR object.entity_id = $entity_id

        RETURN
            claim.claim_id AS claim_id,

            subject.name AS subject,
            subject.type AS subject_type,

            claim.predicate AS predicate,

            object.name AS object,
            object.type AS object_type,

            claim.confidence AS confidence,
            claim.source_sentence AS evidence,
            claim.source_url AS source_url,

            chunk.chunk_id AS chunk_id,
            chunk.text AS chunk_text,
            chunk.section_heading AS section_heading

        ORDER BY claim.confidence DESC

        LIMIT 100
        """

        with self.driver.session() as session:

            result = session.run(
                query,
                entity_id=entity_id,
            )

            return [
                record.data()
                for record in result
            ]

    # =========================================================
    # QUERY NORMALIZATION
    # =========================================================

    @staticmethod
    def _normalize(
        text: Any,
    ) -> str:

        if text is None:
            return ""

        return " ".join(
            str(text)
            .lower()
            .replace(
                "_",
                " ",
            )
            .replace(
                "-",
                " ",
            )
            .split()
        )

    # =========================================================
    # PREDICATE ALIASES
    # =========================================================

    PREDICATE_ALIASES = {

        "DEPENDS_ON": {
            "depend",
            "depends",
            "dependency",
            "dependencies",
            "require",
            "requires",
            "based on",
        },

        "USES": {
            "use",
            "uses",
            "using",
            "utilize",
            "utilizes",
            "with",
        },

        "BUILT_ON": {
            "built",
            "built on",
            "based",
            "based on",
            "powered",
        },

        "SUPPORTS": {
            "support",
            "supports",
            "compatible",
        },

        "VALIDATES": {
            "validate",
            "validates",
            "validation",
            "verify",
            "verifies",
        },

        "PROVIDES": {
            "provide",
            "provides",
            "offers",
            "offer",
        },

        "COMPATIBLE_WITH": {
            "compatible",
            "compatibility",
        },

        "TESTED_WITH": {
            "test",
            "tested",
            "testing",
        },
    }

    # =========================================================
    # QUERY → PREDICATE HINTS
    # =========================================================

    def _predicate_hints(
        self,
        query: str,
    ) -> set[str]:

        normalized = self._normalize(
            query
        )

        hints = set()

        # -----------------------------------------------------
        # Dependency language
        # -----------------------------------------------------

        dependency_terms = {
            "depend",
            "depends",
            "dependency",
            "dependencies",
            "require",
            "requires",
        }

        if any(
            term in normalized
            for term in dependency_terms
        ):

            hints.add(
                "DEPENDS_ON"
            )

        # -----------------------------------------------------
        # Usage language
        # -----------------------------------------------------

        usage_terms = {
            "use",
            "uses",
            "using",
            "utilize",
            "utilizes",
        }

        if any(
            term in normalized
            for term in usage_terms
        ):

            hints.add(
                "USES"
            )

        # -----------------------------------------------------
        # Built-on language
        # -----------------------------------------------------

        if (
            "built on" in normalized
            or "based on" in normalized
            or "built upon" in normalized
        ):

            hints.add(
                "BUILT_ON"
            )

        # -----------------------------------------------------
        # Validation language
        # -----------------------------------------------------

        validation_terms = {
            "validation",
            "validate",
            "validates",
            "validating",
        }

        if any(
            term in normalized
            for term in validation_terms
        ):

            hints.add(
                "VALIDATES"
            )

        # -----------------------------------------------------
        # Support language
        # -----------------------------------------------------

        if (
            "support" in normalized
            or "supports" in normalized
        ):

            hints.add(
                "SUPPORTS"
            )

        return hints

    # =========================================================
    # OBJECT HINTS
    # =========================================================

    def _object_hints(
        self,
        query: str,
    ) -> set[str]:

        normalized = self._normalize(
            query
        )

        candidates = {
            "Pydantic",
            "Starlette",
            "OpenAPI",
            "Swagger",
            "OAuth2",
            "WebSockets",
            "HTTPX",
            "Uvicorn",
            "ORJSONResponse",
            "orjson",
        }

        return {
            candidate
            for candidate in candidates
            if self._normalize(candidate)
            in normalized
        }

    # =========================================================
    # CLAIM SCORING
    # =========================================================

    def _score_claim(
        self,
        claim: dict,
        query: str,
        entity_name: str,
    ) -> float:
        query_normalized = self._normalize(query)

        subject = self._normalize(
            claim.get("subject")
        )

        object_name = self._normalize(
            claim.get("object")
        )

        predicate = self._normalize(
            claim.get("predicate")
        )

        evidence = self._normalize(
            claim.get("evidence")
            or claim.get("chunk_text")
            or ""
        )

        confidence = float(
            claim.get(
                "confidence",
                0.0,
            )
            or 0.0
        )

        score = 0.0

        # =====================================================
        # 1. SUBJECT MATCH
        # =====================================================

        normalized_entity = self._normalize(
            entity_name
        )

        if subject == normalized_entity:
            score += 0.20

        # =====================================================
        # 2. DIRECT OBJECT MATCH
        # =====================================================

        object_hints = self._object_hints(query)

        normalized_object_hints = {
            self._normalize(item)
            for item in object_hints
        }

        if (
            object_name
            and object_name in normalized_object_hints
        ):
            score += 0.35

        # =====================================================
        # 3. PREDICATE MATCH
        # =====================================================

        predicate_hints = self._predicate_hints(query)

        normalized_predicates = {
            self._normalize(item)
            for item in predicate_hints
        }

        if predicate in normalized_predicates:
            score += 0.20

        # =====================================================
        # 4. QUERY / EVIDENCE TOKEN OVERLAP
        # =====================================================

        query_tokens = {
            token
            for token in query_normalized.split()
            if len(token) >= 3
        }

        evidence_tokens = set(
            evidence.split()
        )

        if query_tokens and evidence_tokens:
            overlap = (
                len(query_tokens & evidence_tokens)
                / len(query_tokens)
            )

            score += 0.15 * min(overlap, 1.0)

        # =====================================================
        # 5. SEMANTIC CONCEPT BOOSTS
        # =====================================================

        concept_groups = {
            "validation": {
                "validation",
                "validate",
                "validates",
                "validating",
                "data validation",
                "data",
                "pydantic",
            },
            "server": {
                "server",
                "serve",
                "serves",
                "serving",
                "uvicorn",
            },
            "web": {
                "web",
                "asgi",
                "web parts",
                "starlette",
            },
            "documentation": {
                "documentation",
                "document",
                "docs",
                "openapi",
                "swagger",
            },
            "websockets": {
                "websocket",
                "websockets",
            },
            "oauth": {
                "oauth",
                "oauth2",
            },
            "performance": {
                "performance",
                "fast",
                "high performance",
            },
        }

        query_concepts = set()

        for concept, terms in concept_groups.items():
            if any(
                term in query_normalized
                for term in terms
            ):
                query_concepts.add(concept)

        evidence_concepts = set()

        for concept, terms in concept_groups.items():
            if any(
                term in evidence
                for term in terms
            ):
                evidence_concepts.add(concept)

        concept_overlap = (
            query_concepts & evidence_concepts
        )

        if concept_overlap:
            score += 0.10 * len(concept_overlap)

        # =====================================================
        # 6. CONFIDENCE
        # =====================================================

        confidence_factor = (
            0.75
            + 0.25
            * max(
                0.0,
                min(
                    confidence,
                    1.0,
                ),
            )
        )

        score *= confidence_factor

        return score

    # =========================================================
    # GRAPH SEARCH
    # =========================================================

    def search(
        self,
        entity_name: str,
        top_k: int = 5,
        query: str = "",
    ) -> list[RetrievalResult]:

        if not entity_name:
            return []

        entities = self.find_entity(
            entity_name
        )

        if not entities:
            return []

        all_claims = []

        # -----------------------------------------------------
        # Collect claims for all matching entities.
        # -----------------------------------------------------

        for entity in entities:

            entity_id = entity.get(
                "entity_id"
            )

            if not entity_id:
                continue

            claims = (
                self.get_claims_for_entity(
                    entity_id
                )
            )

            all_claims.extend(
                claims
            )

        # -----------------------------------------------------
        # Remove duplicate claims.
        # -----------------------------------------------------

        unique_claims = {}

        for claim in all_claims:

            claim_id = claim.get(
                "claim_id"
            )

            if claim_id:

                unique_claims[
                    claim_id
                ] = claim

        claims = list(
            unique_claims.values()
        )

        # -----------------------------------------------------
        # Rank claims when a query is provided.
        # -----------------------------------------------------

        if query:

            scored_claims = []

            for claim in claims:

                score = self._score_claim(
                    claim=claim,
                    query=query,
                    entity_name=entity_name,
                )

                scored_claims.append(
                    (
                        score,
                        claim,
                    )
                )

            scored_claims.sort(
                key=lambda item: (
                    item[0],
                    float(
                        item[1].get(
                            "confidence",
                            0.0,
                        )
                        or 0.0
                    ),
                ),
                reverse=True,
            )

        else:

            scored_claims = [
                (
                    float(
                        claim.get(
                            "confidence",
                            0.0,
                        )
                        or 0.0
                    ),
                    claim,
                )
                for claim in claims
            ]

            scored_claims.sort(
                key=lambda item: item[0],
                reverse=True,
            )

        # -----------------------------------------------------
        # Convert claims to RetrievalResult.
        # -----------------------------------------------------

        results = []

        seen_claims = set()

        for score, claim in scored_claims:

            chunk_id = claim.get(
                "chunk_id"
            )

            if not chunk_id:
                continue

            # -------------------------------------------------
            # Prefer one strongest claim per chunk.
            # -------------------------------------------------

            claim_id = claim.get("claim_id")

            if claim_id and claim_id in seen_claims:
             continue

            if claim_id:
              seen_claims.add(claim_id)

            evidence = (
                claim.get(
                    "evidence"
                )
                or claim.get(
                    "chunk_text"
                )
                or ""
            )

            results.append(
                RetrievalResult(
                    chunk_id=chunk_id,
                    text=evidence,
                    score=float(score),
                    source_url=(
                        claim.get(
                            "source_url"
                        )
                        or ""
                    ),
                    section_heading=(
                        claim.get(
                            "section_heading"
                        )
                        or ""
                    ),
                    strategy="graph",
                    claim_id=(
                        claim.get(
                            "claim_id"
                        )
                    ),
                    subject=(
                        claim.get(
                            "subject"
                        )
                    ),
                    predicate=(
                        claim.get(
                            "predicate"
                        )
                    ),
                    object=(
                        claim.get(
                            "object"
                        )
                    ),
                    confidence=float(
                        claim.get(
                            "confidence",
                            0.0,
                        )
                        or 0.0
                    ),
                )
            )

            if len(results) >= top_k:
                break

        return results

    # =========================================================
    # MULTI-HOP SEARCH
    # =========================================================

    def multi_hop_search(
        self,
        source_entity: str,
        first_predicate: str,
        second_predicate: str,
        target_entity: str | None = None,
        max_hops: int = 2,
    ):

        if max_hops < 2:
            return []

        query = """
        MATCH
            (source:Entity)
            -[r1]->
            (middle:Entity)
            -[r2]->
            (target:Entity)

        WHERE
            toLower(source.name)
                = toLower($source_entity)

            AND type(r1)
                = $first_predicate

            AND type(r2)
                = $second_predicate

            AND (
                $target_entity IS NULL
                OR
                toLower(target.name)
                    = toLower($target_entity)
            )

        OPTIONAL MATCH
            (claim1:Claim {
                claim_id: r1.claim_id
            })

        OPTIONAL MATCH
            (claim2:Claim {
                claim_id: r2.claim_id
            })

        RETURN
            source.name AS source,

            type(r1) AS first_predicate,

            middle.name AS middle,

            type(r2) AS second_predicate,

            target.name AS target,

            claim1.claim_id AS first_claim_id,
            claim2.claim_id AS second_claim_id,

            claim1.source_sentence AS first_evidence,
            claim2.source_sentence AS second_evidence,

            claim1.source_url AS first_source,
            claim2.source_url AS second_source,

            claim1.confidence AS first_confidence,
            claim2.confidence AS second_confidence

        LIMIT 50
        """

        with self.driver.session() as session:

            result = session.run(
                query,
                source_entity=source_entity,
                first_predicate=first_predicate,
                second_predicate=second_predicate,
                target_entity=target_entity,
            )

            return [
                record.data()
                for record in result
            ]

    # =========================================================
    # CLOSE
    # =========================================================

    def close(self):

        self.driver.close()