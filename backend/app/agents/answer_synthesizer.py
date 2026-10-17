from .answer_models import (
    AnswerCitation,
    SynthesizedAnswer,
)


class AnswerSynthesizer:

    def synthesize(
        self,
        query: str,
        results: list,
    ) -> SynthesizedAnswer:

        if not results:

            return SynthesizedAnswer(
                query=query,
                answer=(
                    "I could not find enough "
                    "evidence to answer this query."
                ),
                confidence=0.0,
            )

                # -------------------------------------------------
        # Remove duplicate retrieval records while
        # preserving distinct graph claims from one chunk.
        # -------------------------------------------------

        unique_results = []
        seen_result_keys = set()

        for result in results:

            claim_id = getattr(
                result,
                "claim_id",
                None,
            )

            if claim_id:
                result_key = (
                    "claim",
                    claim_id,
                )
            else:
                result_key = (
                    "chunk",
                    result.chunk_id,
                )

            if result_key in seen_result_keys:
                continue

            seen_result_keys.add(
                result_key
            )

            unique_results.append(
                result
            )

        # -------------------------------------------------
        # Strongest evidence first
        # -------------------------------------------------

        query_lower = query.lower()

        is_dependency_query = any(
            phrase in query_lower
            for phrase in (
                "dependency",
                "dependencies",
                "depend on",
                "depends on",
                "require",
                "requires",
            )
        )

        is_usage_query = any(
            phrase in query_lower
            for phrase in (
                " use",
                " uses",
                " using",
                " utilize",
                " utilizes",
            )
        )

        # Preserve the existing multi-hop behavior.
        is_multi_hop_query = (
            "that also" in query_lower
            or (
                is_dependency_query
                and is_usage_query
            )
        )

        requested_predicate = None

        if not is_multi_hop_query:
            if is_dependency_query:
                requested_predicate = "DEPENDS_ON"
            elif is_usage_query:
                requested_predicate = "USES"

        def evidence_priority(result):
            strategy = getattr(
                result,
                "strategy",
                "",
            )

            predicate = str(
                getattr(result, "predicate", "") or ""
            ).strip().upper()

            subject = str(
                getattr(result, "subject", "") or ""
            ).lower().strip()

            matching_relationship = (
                requested_predicate is not None
                and strategy == "graph"
                and predicate == requested_predicate
                and bool(subject)
                and subject in query_lower
            )

            return (
                1 if matching_relationship else 0,
                float(result.score),
            )

        unique_results.sort(
            key=evidence_priority,
            reverse=True,
        )

        citation_results = unique_results


        if requested_predicate:
            matching_relationships = [
                result
                for result in unique_results
                if (
                    getattr(result, "strategy", "") == "graph"
                    and str(
                        getattr(result, "predicate", "") or ""
                    ).strip().upper() == requested_predicate
                    and str(
                        getattr(result, "subject", "") or ""
                    ).strip().lower() in query_lower
                )
            ]

            if matching_relationships:
                citation_results = matching_relationships

        best = unique_results[0]

        answer = best.text.strip()

        predicate_phrases = {
            "DEPENDS_ON": "depends on",
            "USES": "uses",
            "BUILT_ON": "is built on",
            "SUPPORTS": "supports",
            "PROVIDES": "provides",
            "VALIDATES": "validates",
            "COMPATIBLE_WITH": "is compatible with",
            "TESTED_WITH": "is tested with",
        }

        # Generate multi-hop answers from the actual
        # structured graph path, not from source text.
        if is_multi_hop_query:

            path_results = [
                result
                for result in citation_results
                if (
                    getattr(result, "strategy", "")
                    == "graph_multi_hop"
                    and getattr(result, "subject", None)
                    and getattr(result, "predicate", None)
                    and getattr(result, "object", None)
                )
            ]

            path_results.sort(
                key=lambda result: str(result.chunk_id)
            )

            statements = []
            seen_triples = set()

            for result in path_results:
                subject = str(result.subject).strip()
                predicate = str(result.predicate).strip().upper()
                object_text = str(result.object).strip()

                phrase = predicate_phrases.get(predicate)

                if not subject or not object_text or not phrase:
                    continue

                triple = (
                    subject.lower(),
                    predicate,
                    object_text.lower(),
                )

                if triple in seen_triples:
                    continue

                seen_triples.add(triple)

                statements.append(
                    f"{subject} {phrase} {object_text}."
                )

            if statements:
                answer = " ".join(statements)

        # Generate direct relational answers from
        # matching graph claims.
        elif requested_predicate and citation_results:

            structured_sentences = []
            seen_triples = set()

            for result in citation_results:
                subject = str(
                    getattr(result, "subject", "") or ""
                ).strip()

                predicate = str(
                    getattr(result, "predicate", "") or ""
                ).strip().upper()

                object_text = str(
                    getattr(result, "object", "") or ""
                ).strip()

                if (
                    not subject
                    or not object_text
                    or predicate != requested_predicate
                ):
                    continue

                phrase = predicate_phrases.get(predicate)

                if not phrase:
                    continue

                triple = (
                    subject.lower(),
                    predicate,
                    object_text.lower(),
                )

                if triple in seen_triples:
                    continue

                seen_triples.add(triple)

                structured_sentences.append(
                    f"{subject} {phrase} {object_text}."
                )

            if structured_sentences:
                answer = " ".join(structured_sentences)

        citations = []
        supporting_claims = []


        # -------------------------------------------------
        # Preserve provenance and claim metadata
        # -------------------------------------------------

        for result in citation_results[:5]:

            claim_id = getattr(
                result,
                "claim_id",
                None,
            )

            subject = getattr(
                result,
                "subject",
                None,
            )

            predicate = getattr(
                result,
                "predicate",
                None,
            )

            object_text = getattr(
                result,
                "object",
                None,
            )

            confidence = getattr(
                result,
                "confidence",
                result.score,
            )

            citations.append(
                AnswerCitation(
                    source_url=result.source_url,
                    source_sentence=result.text,
                    chunk_id=result.chunk_id,

                    claim_id=claim_id,

                    subject=subject,
                    predicate=predicate,
                    object=object_text,

                    confidence=float(
                        confidence
                    ),
                )
            )

            # Only Graph/claim-aware results
            # become structured supporting claims.
            if (
                subject
                and predicate
                and object_text
            ):

                supporting_claims.append(
                    {
                        "claim_id": claim_id,
                        "subject": subject,
                        "predicate": predicate,
                        "object": object_text,
                        "confidence": float(
                            confidence
                        ),
                    }
                )

        return SynthesizedAnswer(
            query=query,
            answer=answer,

            confidence=min(
                float(best.score),
                1.0,
            ),

            citations=citations,

            supporting_claims=(
                supporting_claims
            ),
        )