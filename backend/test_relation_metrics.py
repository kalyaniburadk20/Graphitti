from app.evaluation.relation_metrics import (
    RelationTriple,
    calculate_metrics,
    normalize_triple,
)


gold = {
    normalize_triple(
        RelationTriple(
            "FastAPI",
            "USES",
            "Pydantic",
        )
    ),

    normalize_triple(
        RelationTriple(
            "FastAPI",
            "BUILT_ON",
            "Starlette",
        )
    ),

    normalize_triple(
        RelationTriple(
            "FastAPI",
            "SUPPORTS",
            "OAuth2",
        )
    ),
}


predicted = {
    normalize_triple(
        RelationTriple(
            "FastAPI",
            "USES",
            "Pydantic",
        )
    ),

    normalize_triple(
        RelationTriple(
            "FastAPI",
            "BUILT_ON",
            "Starlette",
        )
    ),
}


metrics = calculate_metrics(
    predicted,
    gold,
)


print("\n========== RELATION METRICS ==========\n")

for key, value in metrics.items():

    if isinstance(value, float):

        print(
            f"{key:20}: "
            f"{value:.4f}"
        )

    else:

        print(
            f"{key:20}: "
            f"{value}"
        )