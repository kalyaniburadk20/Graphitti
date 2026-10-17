import json
from pathlib import Path

from app.nlp.claim_extractor import ClaimExtractor
from app.nlp.relation_models import Relation
from app.nlp.claim_storage import save_claims


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data" / "processed"

RELATIONS_FILE = DATA_DIR / "relations.jsonl"


def load_relations() -> list[Relation]:
    if not RELATIONS_FILE.exists():
        raise FileNotFoundError(
            f"Relations file not found: {RELATIONS_FILE}"
        )

    relations = []

    with RELATIONS_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:

        for line_number, line in enumerate(
            file,
            start=1,
        ):

            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)

            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON at line "
                    f"{line_number}: {exc}"
                ) from exc

            relations.append(
                Relation(
                    relation_id=record["relation_id"],
                    subject_entity_id=record[
                        "subject_entity_id"
                    ],
                    subject_text=record[
                        "subject_text"
                    ],
                    subject_type=record[
                        "subject_type"
                    ],
                    predicate=record[
                        "predicate"
                    ],
                    object_entity_id=record[
                        "object_entity_id"
                    ],
                    object_text=record[
                        "object_text"
                    ],
                    object_type=record[
                        "object_type"
                    ],
                    source_sentence=record[
                        "source_sentence"
                    ],
                    chunk_id=record[
                        "chunk_id"
                    ],
                    source_url=record[
                        "source_url"
                    ],
                    confidence=float(
                        record["confidence"]
                    ),
                )
            )

    return relations


def deduplicate_claims(claims):
    """
    Deduplicate claims by claim_id.

    A claim_id is deterministic for the same:
        subject + predicate + object +
        chunk + source_url
    """

    unique = {}
    duplicate_count = 0

    for claim in claims:

        if claim.claim_id in unique:
            duplicate_count += 1
            continue

        unique[claim.claim_id] = claim

    return list(unique.values()), duplicate_count


def main():
    print("=" * 70)
    print("Graphitti — Claim Generation")
    print("=" * 70)

    print(f"Project root : {PROJECT_ROOT}")
    print(f"Relations file: {RELATIONS_FILE}")
    print()

    relations = load_relations()

    print(
        f"Loaded relations: {len(relations)}"
    )

    extractor = ClaimExtractor()

    claims = []

    for relation in relations:

        claim = extractor.extract_claim(
            relation
        )

        claims.append(claim)

    print(
        f"Generated claims: {len(claims)}"
    )

    claims, duplicate_count = (
        deduplicate_claims(claims)
    )

    print(
        f"Duplicate claims removed: "
        f"{duplicate_count}"
    )

    print(
        f"Final claims: {len(claims)}"
    )

    output_path = save_claims(
        claims
    )

    print()
    print("Saved claims to:")
    print(output_path)

    print()
    print("=" * 70)
    print("Claim generation completed successfully.")
    print("=" * 70)


if __name__ == "__main__":
    main()