from dataclasses import dataclass


@dataclass(frozen=True)
class RelationTriple:
    subject: str
    predicate: str
    object: str


def normalize_text(text: str) -> str:
    return " ".join(
        text.lower().strip().split()
    )


def normalize_triple(
    triple: RelationTriple,
) -> RelationTriple:

    return RelationTriple(
        subject=normalize_text(
            triple.subject
        ),
        predicate=normalize_text(
            triple.predicate
        ),
        object=normalize_text(
            triple.object
        ),
    )


def calculate_metrics(
    predicted: set[RelationTriple],
    gold: set[RelationTriple],
):
    true_positive = len(
        predicted & gold
    )

    false_positive = len(
        predicted - gold
    )

    false_negative = len(
        gold - predicted
    )

    precision = (
        true_positive
        / (true_positive + false_positive)
        if (
            true_positive
            + false_positive
        )
        else 0.0
    )

    recall = (
        true_positive
        / (true_positive + false_negative)
        if (
            true_positive
            + false_negative
        )
        else 0.0
    )

    f1 = (
        2 * precision * recall
        / (precision + recall)
        if precision + recall
        else 0.0
    )

    return {
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }