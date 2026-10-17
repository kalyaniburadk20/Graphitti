from app.routing.query_planner import (
    QueryPlanner,
)


planner = QueryPlanner()


tests = [
    (
        "What does FastAPI depend on that also uses Pydantic?",
        "MULTI_HOP",
        ["FastAPI", "Pydantic"],
    ),
    (
        "What does FastAPI depend on?",
        "RELATIONAL",
        ["FastAPI"],
    ),
    (
        "Explain FastAPI dependency injection",
        "SEMANTIC",
        ["FastAPI"],
    ),
]


for query, intent, entities in tests:

    plan = planner.plan(
        query=query,
        intent=intent,
        entities=entities,
    )

    print(
        "\n" + "=" * 80
    )

    print(
        f"QUERY: {query}"
    )

    print(
        f"INTENT: {plan.intent}"
    )

    print(
        "STEPS:"
    )

    for step in plan.steps:

        print(
            f"  {step.step_id}. "
            f"operation={step.operation}, "
            f"entity={step.entity}, "
            f"predicate={step.predicate}, "
            f"target={step.target}"
        )