from app.agents.answer_claim_parser import (
    AnswerClaimParser,
)

from app.agents.claim_verifier import (
    ClaimVerifier,
)


answer = (
    "FastAPI depends on Pydantic. "
    "FastAPI was created in 2018."
)


evidence_claims = [
    {
        "claim_id": "claim_001",
        "subject": "FastAPI",
        "predicate": "DEPENDS_ON",
        "object": "Pydantic",
        "confidence": 0.95,
    }
]


parser = AnswerClaimParser()
verifier = ClaimVerifier()


answer_claims = parser.parse(
    answer
)

results = verifier.verify(
    answer_claims=answer_claims,
    evidence_claims=evidence_claims,
)


print(
    "\n========== ANSWER CLAIMS ==========\n"
)

for claim in answer_claims:
    print(claim)


print(
    "\n========== VERIFICATION ==========\n"
)

for result in results:

    print(
        f"{result.subject} "
        f"--[{result.predicate}]--> "
        f"{result.object}"
    )

    print(
        f"Supported: "
        f"{result.supported}"
    )

    print(
        f"Confidence: "
        f"{result.confidence}"
    )

    print(
        f"Supporting claims: "
        f"{result.supporting_claim_ids}"
    )