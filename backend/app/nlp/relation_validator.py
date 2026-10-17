from .relation_models import Relation


def validate_relation(
    relation: Relation,
) -> bool:

    # Subject and object must be different.
    if (
        relation.subject_entity_id
        == relation.object_entity_id
    ):
        return False

    if not relation.subject_text.strip():
        return False

    if not relation.object_text.strip():
        return False

    if not relation.predicate.strip():
        return False

    # Reject extremely weak/generic entities.
    blocked_text = {
        "first",
        "second",
        "third",
        "one",
        "two",
        "three",
        "automatic",
        "execute",
        "convert",
    }

    if (
        relation.subject_text.lower()
        in blocked_text
    ):
        return False

    if (
        relation.object_text.lower()
        in blocked_text
    ):
        return False

    return True