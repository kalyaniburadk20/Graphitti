import re

from .answer_claim_parser import AnswerClaimParser
from .claim_verifier import ClaimVerifier
from .verification_models import VerificationResult


class FaithfulnessChecker:

    def __init__(self):

        self.claim_parser = AnswerClaimParser()
        self.claim_verifier = ClaimVerifier()

    def verify(
        self,
        answer: str,
        evidence: list,
    ) -> VerificationResult:

        if not answer or not answer.strip():

            return VerificationResult(
                faithful=False,
                confidence=0.0,
                supported_claims=0,
                unsupported_claims=1,
                reason="Answer is empty.",
            )

        if not evidence:

            return VerificationResult(
                faithful=False,
                confidence=0.0,
                supported_claims=0,
                unsupported_claims=1,
                reason="No evidence was provided.",
            )

        # -------------------------------------------------
        # Parse claims from generated answer
        # -------------------------------------------------

        answer_claims = self.claim_parser.parse(
            answer
        )

        if not answer_claims:

            return VerificationResult(
                faithful=False,
                confidence=0.0,
                supported_claims=0,
                unsupported_claims=1,
                reason=(
                    "No verifiable claims could "
                    "be extracted from the answer."
                ),
            )

        # -------------------------------------------------
        # Try structured claim verification first
        # -------------------------------------------------

        evidence_claims = []

        for citation in evidence:

            # Structured AnswerCitation
            subject = getattr(
                citation,
                "subject",
                None,
            )

            predicate = getattr(
                citation,
                "predicate",
                None,
            )

            object_text = getattr(
                citation,
                "object",
                None,
            )

            if (
                subject
                and predicate
                and object_text
            ):

                evidence_claims.append(
                    {
                        "claim_id": getattr(
                            citation,
                            "claim_id",
                            None,
                        ),
                        "subject": subject,
                        "predicate": predicate,
                        "object": object_text,
                        "confidence": getattr(
                            citation,
                            "confidence",
                            0.0,
                        ),
                    }
                )

            # Dictionary evidence
            elif isinstance(
                citation,
                dict,
            ):

                if (
                    citation.get("subject")
                    and citation.get("predicate")
                    and citation.get("object")
                ):

                    evidence_claims.append(
                        citation
                    )

        if evidence_claims:

            verification_results = (
                self.claim_verifier.verify(
                    answer_claims=answer_claims,
                    evidence_claims=evidence_claims,
                )
            )

            return self._build_result(
                verification_results
            )

        # -------------------------------------------------
        # No structured claims available.
        #
        # Use source-sentence verification.
        # -------------------------------------------------

        evidence_sentences = []

        for citation in evidence:

            sentence = ""

            if hasattr(
                citation,
                "source_sentence",
            ):

                sentence = (
                    citation.source_sentence
                )

            elif isinstance(
                citation,
                dict,
            ):

                sentence = (
                    citation.get(
                        "source_sentence",
                        citation.get(
                            "evidence",
                            "",
                        ),
                    )
                )

            if sentence and sentence.strip():
                evidence_sentences.append(
                    sentence.strip()
                )

        if not evidence_sentences:

            return VerificationResult(
                faithful=False,
                confidence=0.0,
                supported_claims=0,
                unsupported_claims=len(
                    answer_claims
                ),
                reason=(
                    "Evidence contains neither "
                    "structured claims nor source sentences."
                ),
            )

        return self._verify_against_sentences(
            answer_claims=answer_claims,
            evidence_sentences=evidence_sentences,
        )

    # =========================================================
    # Sentence-level claim verification
    # =========================================================

    def _verify_against_sentences(
        self,
        answer_claims: list[dict],
        evidence_sentences: list[str],
    ) -> VerificationResult:

        supported = 0
        unsupported = 0

        for claim in answer_claims:

            claim_supported = False

            answer_subject = self._normalize_entity(
                claim.get("subject")
            )

            answer_predicate = self._normalize_predicate(
                claim.get("predicate")
            )

            answer_object = self._normalize_entity(
                claim.get("object")
            )

            if not (
                answer_subject
                and answer_predicate
                and answer_object
            ):

                unsupported += 1
                continue

            for sentence in evidence_sentences:

                evidence_claims = (
                    self.claim_parser.parse(
                        sentence
                    )
                )

                for evidence_claim in (
                    evidence_claims
                ):

                    evidence_subject = (
                        self._normalize_entity(
                            evidence_claim.get(
                                "subject"
                            )
                        )
                    )

                    evidence_predicate = (
                        self._normalize_predicate(
                            evidence_claim.get(
                                "predicate"
                            )
                        )
                    )

                    evidence_object = (
                        self._normalize_entity(
                            evidence_claim.get(
                                "object"
                            )
                        )
                    )

                    if (
                        answer_subject
                        == evidence_subject
                        and
                        answer_predicate
                        == evidence_predicate
                        and
                        answer_object
                        == evidence_object
                    ):

                        claim_supported = True
                        break

                if claim_supported:
                    break

            if claim_supported:
                supported += 1
            else:
                unsupported += 1

        total = (
            supported
            + unsupported
        )

        confidence = (
            supported / total
            if total
            else 0.0
        )

        faithful = (
            total > 0
            and unsupported == 0
        )

        if faithful:

            reason = (
                "Every answer claim is supported "
                "by at least one retrieved source sentence."
            )

        else:

            reason = (
                "One or more answer claims are not "
                "supported by the retrieved source sentences."
            )

        return VerificationResult(
            faithful=faithful,
            confidence=confidence,
            supported_claims=supported,
            unsupported_claims=unsupported,
            reason=reason,
        )

    # =========================================================
    # Normalize entity
    # =========================================================

    @staticmethod
    def _normalize_entity(
        value: str | None,
    ) -> str:

        if value is None:
            return ""

        value = value.lower().strip()

        value = re.sub(
            r"^[\s,:;.-]+|[\s,:;.-]+$",
            "",
            value,
        )

        return " ".join(
            value.split()
        )

    # =========================================================
    # Normalize predicate
    # =========================================================

    @staticmethod
    def _normalize_predicate(
        value: str | None,
    ) -> str:

        if value is None:
            return ""

        value = value.lower().strip()

        aliases = {
            "uses": "uses",
            "use": "uses",

            "depends_on": "depends on",
            "depends on": "depends on",
            "depend on": "depends on",

            "built_on": "built on",
            "built on": "built on",
            "based on": "built on",

            "supports": "supports",
            "support": "supports",

            "provides": "provides",
            "provide": "provides",

            "validates": "validates",
            "validate": "validates",

            "compatible_with": "compatible with",
            "compatible with": "compatible with",

            "tested_with": "tested with",
            "tested with": "tested with",

            "tested_using": "tested with",
            "tested using": "tested with",
        }

        return aliases.get(
            value,
            value,
        )

    # =========================================================
    # Build final verification result
    # =========================================================

    @staticmethod
    def _build_result(
        verification_results,
    ) -> VerificationResult:

        supported = sum(
            1
            for result in verification_results
            if result.supported
        )

        unsupported = sum(
            1
            for result in verification_results
            if not result.supported
        )

        total = (
            supported
            + unsupported
        )

        confidence = (
            supported / total
            if total
            else 0.0
        )

        faithful = (
            total > 0
            and unsupported == 0
        )

        if faithful:

            reason = (
                "Every answer claim is supported "
                "by a retrieved knowledge-graph claim."
            )

        else:

            reason = (
                "One or more answer claims are not "
                "supported by retrieved knowledge-graph claims."
            )

        return VerificationResult(
            faithful=faithful,
            confidence=confidence,
            supported_claims=supported,
            unsupported_claims=unsupported,
            reason=reason,
        )