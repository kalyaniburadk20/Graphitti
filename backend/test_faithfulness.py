from app.agents.answer_models import AnswerCitation
from app.agents.faithfulness_checker import (
    FaithfulnessChecker,
)


checker = FaithfulnessChecker()


evidence = [
    AnswerCitation(
        source_url="https://fastapi.tiangolo.com/",
        source_sentence=(
            "FastAPI depends on Pydantic and Starlette."
        ),
        chunk_id="991c6c230b90aef0",
    )
]


answers = [
    (
        "FastAPI depends on Pydantic and Starlette."
    ),
    (
        "FastAPI depends on Pydantic and Starlette "
        "and was created in 2018."
    ),
]


for answer in answers:

    result = checker.verify(
        answer=answer,
        evidence=evidence,
    )

    print(
        "\n" + "=" * 80
    )

    print(
        "ANSWER:",
        answer,
    )

    print(
        "FAITHFUL:",
        result.faithful,
    )

    print(
        "CONFIDENCE:",
        result.confidence,
    )

    print(
        "SUPPORTED:",
        result.supported_claims,
    )

    print(
        "UNSUPPORTED:",
        result.unsupported_claims,
    )

    print(
        "REASON:",
        result.reason,
    )