import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

RELATIONS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "relations.jsonl"
)


def main():

    print("=" * 80)
    print("RELATION EXTRACTION AUDIT")
    print("=" * 80)

    if not RELATIONS_PATH.exists():

        print(
            f"File not found:\n{RELATIONS_PATH}"
        )
        return

    fastapi_relations = []

    with RELATIONS_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            relation = json.loads(line)

            subject = relation.get(
                "subject_text",
                "",
            )

            if subject.lower() != "fastapi":
                continue

            fastapi_relations.append(
                relation
            )

    print()

    if not fastapi_relations:

        print(
            "No relations found where "
            "subject_text == FastAPI."
        )

    else:

        for index, relation in enumerate(
            fastapi_relations,
            start=1,
        ):

            print(
                f"[{index}] "
                f"FastAPI "
                f"--{relation.get('predicate')}--> "
                f"{relation.get('object_text')}"
            )

            print(
                "    Subject type:",
                relation.get(
                    "subject_type"
                ),
            )

            print(
                "    Object type:",
                relation.get(
                    "object_type"
                ),
            )

            print(
                "    Confidence:",
                relation.get(
                    "confidence"
                ),
            )

            print(
                "    Chunk:",
                relation.get(
                    "chunk_id"
                ),
            )

            print(
                "    Evidence:",
                relation.get(
                    "source_sentence"
                ),
            )

            print()

    print("=" * 80)

    print(
        "TOTAL FASTAPI RELATIONS:",
        len(fastapi_relations),
    )

    print("=" * 80)


if __name__ == "__main__":
    main()