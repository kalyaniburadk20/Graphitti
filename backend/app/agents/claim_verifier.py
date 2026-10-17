from dataclasses import dataclass


@dataclass
class ClaimVerification:
    subject: str
    predicate: str
    object: str

    supported: bool
    confidence: float
    supporting_claim_ids: list[str]


class ClaimVerifier:

    predicate_aliases = {
        "depends on": "depends_on",
        "uses": "uses",
        "supports": "supports",
        "provides": "provides",
        "built on": "built_on",
        "compatible with": "compatible_with",
        "validates": "validates",
        "tested with": "tested_with",
        "tested using": "tested_with",
    }

    @staticmethod
    def _normalize(
        value: str | None,
    ) -> str:
        if value is None:
            return ""

        value = value.lower().strip()

        if value in ClaimVerifier.predicate_aliases:
            value = ClaimVerifier.predicate_aliases[value]

        return " ".join(
            value.split()
        )

    def verify(
        self,
        answer_claims: list[dict],
        evidence_claims: list[dict],
    ) -> list[ClaimVerification]:

        results = []

        # -------------------------------------------------
        # Build normalized evidence lookup
        # -------------------------------------------------

        evidence_lookup = {}

        for claim in evidence_claims:

            subject = self._normalize(
                claim.get("subject")
            )

            predicate = self._normalize(
                claim.get("predicate")
            )

            object_text = self._normalize(
                claim.get("object")
            )

            # Don't index incomplete evidence claims.
            if not (
                subject
                and predicate
                and object_text
            ):
                continue

            key = (
                subject,
                predicate,
                object_text,
            )

            evidence_lookup.setdefault(
                key,
                []
            ).append(
                claim
            )

        # -------------------------------------------------
        # Verify every answer claim
        # -------------------------------------------------

        for answer_claim in answer_claims:

            raw_subject = answer_claim.get(
                "subject"
            )

            raw_predicate = answer_claim.get(
                "predicate"
            )

            raw_object = answer_claim.get(
                "object"
            )

            subject = self._normalize(
                raw_subject
            )

            predicate = self._normalize(
                raw_predicate
            )

            object_text = self._normalize(
                raw_object
            )

            # -------------------------------------------------
            # Missing fields = unsupported claim
            # -------------------------------------------------

            if not (
                subject
                and predicate
                and object_text
            ):

                results.append(
                    ClaimVerification(
                        subject=(
                            raw_subject
                            or ""
                        ),
                        predicate=(
                            raw_predicate
                            or ""
                        ),
                        object=(
                            raw_object
                            or ""
                        ),
                        supported=False,
                        confidence=0.0,
                        supporting_claim_ids=[],
                    )
                )

                continue

            key = (
                subject,
                predicate,
                object_text,
            )

            supporting_claims = (
                evidence_lookup.get(
                    key,
                    []
                )
            )

            # -------------------------------------------------
            # Supported
            # -------------------------------------------------

            if supporting_claims:

                confidence = max(
                    float(
                        claim.get(
                            "confidence",
                            0.0,
                        )
                    )
                    for claim
                    in supporting_claims
                )

                results.append(
                    ClaimVerification(
                        subject=(
                            raw_subject
                        ),
                        predicate=(
                            raw_predicate
                        ),
                        object=(
                            raw_object
                        ),
                        supported=True,
                        confidence=confidence,
                        supporting_claim_ids=[
                            claim.get(
                                "claim_id"
                            )
                            for claim
                            in supporting_claims
                            if claim.get(
                                "claim_id"
                            )
                        ],
                    )
                )

            # -------------------------------------------------
            # Unsupported
            # -------------------------------------------------

            else:

                results.append(
                    ClaimVerification(
                        subject=(
                            raw_subject
                        ),
                        predicate=(
                            raw_predicate
                        ),
                        object=(
                            raw_object
                        ),
                        supported=False,
                        confidence=0.0,
                        supporting_claim_ids=[],
                    )
                )

        return results