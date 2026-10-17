from app.agents.answer_claim_parser import (
    AnswerClaimParser,
)


parser = AnswerClaimParser()


answers = [
    "FastAPI depends on Pydantic and Starlette.",
    "FastAPI uses Pydantic.",
    "Pydantic validates Python data.",
]


for answer in answers:

    print(
        "\n" + "=" * 80
    )

    print(
        "ANSWER:",
        answer,
    )

    claims = parser.parse(
        answer
    )

    for claim in claims:
        print(
            claim
        )