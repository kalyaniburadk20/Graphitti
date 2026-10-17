from app.agents.answer_synthesizer import (
    AnswerSynthesizer,
)

from app.retrieval.retrieval_models import (
    RetrievalResult,
)


results = [
    RetrievalResult(
        chunk_id="chunk_001",
        text=(
            "FastAPI depends on Pydantic "
            "and Starlette."
        ),
        score=0.92,
        source_url=(
            "https://fastapi.tiangolo.com/"
        ),
        section_heading="Dependencies",
        strategy="graph",
    ),

    RetrievalResult(
        chunk_id="chunk_002",
        text=(
            "FastAPI uses Pydantic for "
            "data validation."
        ),
        score=0.74,
        source_url=(
            "https://fastapi.tiangolo.com/"
        ),
        section_heading="Validation",
        strategy="dense",
    ),

    RetrievalResult(
    chunk_id="chunk_003",
    text="FastAPI depends on Pydantic.",
    score=0.95,
    source_url="https://fastapi.tiangolo.com/",
    section_heading="Dependencies",
    strategy="graph",
    claim_id="claim_001",
    subject="FastAPI",
    predicate="DEPENDS_ON",
    object="Pydantic",
    confidence=0.95,
),
]


synthesizer = AnswerSynthesizer()

result = synthesizer.synthesize(
    query="What does FastAPI depend on?",
    results=results,
)


print(
    "\n========== ANSWER ==========\n"
)

print(
    "Question:",
    result.query,
)

print(
    "\nAnswer:",
    result.answer,
)

print(
    "\nConfidence:",
    result.confidence,
)

print(
    "\nCitations:"
)

print(
    "\nSupporting claims:"
)

for claim in result.supporting_claims:
    print(claim)

for citation in result.citations:

    print(
        f"\nSource: {citation.source_url}"
    )

    print(
        f"Chunk: {citation.chunk_id}"
    )

    print(
        f"Evidence: {citation.source_sentence}"
    )