from .entity_models import Entity


BLOCKED_TYPES = {
    "CARDINAL",
    "ORDINAL",
    "PERCENT",
    "DATE",
    "TIME",
    "MONEY",
    "QUANTITY",
    "WORK_OF_ART",
    "get",
    "post",
    "put",
    "patch",
    "delete",
    "head",
    "options",
    "trace",
}

BLOCKED_ENTITY_TEXT = set()


def filter_entities(
    entities: list[Entity],
) -> list[Entity]:

    filtered = []

    for entity in entities:
        if entity.text.lower() in BLOCKED_ENTITY_TEXT:
            continue

        # Remove obvious numeric/date/noise entities.
        if entity.label in BLOCKED_TYPES:
            continue

        text = entity.text.strip()

        if not text:
            continue

        # Very short generic words are usually noise.
        if len(text) < 2:
            continue

        filtered.append(entity)

    return filtered