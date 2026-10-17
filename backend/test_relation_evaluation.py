import json
from pathlib import Path

from app.evaluation.relation_metrics import (
    RelationTriple,
    calculate_metrics,
    normalize_triple,
)

from app.nlp.chunking_models import SemanticChunk
from app.nlp.entity_models import Entity
from app.nlp.relation_extractor import RelationExtractor


PROJECT_ROOT = Path(__file__).resolve().parents[1]

TEST_FILE = (
    PROJECT_ROOT
    / "data"
    / "evaluation"
    / "relation_test.jsonl"
)


def load_test_cases():
    cases = []

    with TEST_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:
            line = line.strip()

            if not line:
                continue

            cases.append(
                json.loads(line)
            )

    return cases


def build_entities(
    case,
    chunk,
):
    """
    Create entities from the gold annotations.
    This isolates relation extraction from
    the current NER weaknesses.
    """

    text = case["text"]

    entity_specs = []

    subject = case.get("subject")
    object_text = case.get("object")

    if subject:
        start = text.find(subject)

        if start >= 0:
            entity_specs.append(
                (
                    subject,
                    start,
                    start + len(subject),
                    "ENTITY",
                    f"subject::{case['id']}",
                )
            )

    if object_text:
        start = text.find(object_text)

        if start >= 0:
            entity_specs.append(
                (
                    object_text,
                    start,
                    start + len(object_text),
                    "ENTITY",
                    f"object::{case['id']}",
                )
            )

    entities = []

    for (
        entity_text,
        start,
        end,
        label,
        entity_id,
    ) in entity_specs:

        entities.append(
            Entity(
                entity_id=entity_id,
                text=entity_text,
                label=label,
                start_char=start,
                end_char=end,
                chunk_id=chunk.chunk_id,
                source_url=chunk.document_url,
                confidence=1.0,
            )
        )

    return entities


def main():

    cases = load_test_cases()

    extractor = RelationExtractor()

    gold = set()
    predicted = set()

    for index, case in enumerate(cases):

        text = case["text"]

        chunk = SemanticChunk(
            chunk_id=f"evaluation_{index}",
            document_url="evaluation://relation_test",
            section_heading="Evaluation",
            section_level=1,
            text=text,
            chunk_index=index,
            token_estimate=len(text.split()),
        )

        gold_relation_exists = (
            case["relation_exists"]
        )

        if gold_relation_exists:
            gold.add(
                normalize_triple(
                    RelationTriple(
                        case["subject"],
                        case["predicate"],
                        case["object"],
                    )
                )
            )

        entities = build_entities(
            case,
            chunk,
        )

        relations = extractor.extract_relations(
            chunk,
            entities,
        )

        for relation in relations:

            predicted.add(
                normalize_triple(
                    RelationTriple(
                        relation.subject_text,
                        relation.predicate,
                        relation.object_text,
                    )
                )
            )

    metrics = calculate_metrics(
        predicted,
        gold,
    )

    print(
        "\n========== ACTUAL RELATION EXTRACTION EVALUATION ==========\n"
    )

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

    print("\n========== GOLD ==========\n")

    for triple in sorted(
        gold,
        key=lambda item: (
            item.subject,
            item.predicate,
            item.object,
        ),
    ):
        print(
            f"{triple.subject} "
            f"--[{triple.predicate}]--> "
            f"{triple.object}"
        )

    print("\n========== PREDICTED ==========\n")

    for triple in sorted(
        predicted,
        key=lambda item: (
            item.subject,
            item.predicate,
            item.object,
        ),
    ):
        print(
            f"{triple.subject} "
            f"--[{triple.predicate}]--> "
            f"{triple.object}"
        )


if __name__ == "__main__":
    main()