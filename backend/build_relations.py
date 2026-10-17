import json
from pathlib import Path
from collections import defaultdict

from app.nlp.chunking_models import SemanticChunk
from app.nlp.entity_models import Entity
from app.nlp.relation_extractor import RelationExtractor
from app.nlp.relation_storage import save_relations


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data" / "processed"

CHUNKS_FILE = DATA_DIR / "semantic_chunks.jsonl"
ENTITIES_FILE = DATA_DIR / "entities.jsonl"


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    records = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON in {path} at line {line_number}: {exc}"
                ) from exc

    return records


def load_chunks() -> list[SemanticChunk]:
    records = load_jsonl(CHUNKS_FILE)

    chunks = []

    for record in records:
        chunks.append(
            SemanticChunk(
                chunk_id=record["chunk_id"],
                document_url=record["document_url"],
                section_heading=record.get("section_heading"),
                section_level=record.get("section_level"),
                text=record["text"],
                chunk_index=record["chunk_index"],
                token_estimate=record["token_estimate"],
            )
        )

    return chunks


def load_entities() -> dict[str, list[Entity]]:
    records = load_jsonl(ENTITIES_FILE)

    entities_by_chunk = defaultdict(list)

    for record in records:
        entity = Entity(
            entity_id=record["entity_id"],
            text=record["text"],
            label=record["label"],
            start_char=record["start_char"],
            end_char=record["end_char"],
            chunk_id=record["chunk_id"],
            source_url=record["source_url"],
            confidence=record["confidence"],
        )

        entities_by_chunk[entity.chunk_id].append(entity)

    return dict(entities_by_chunk)


def deduplicate_relations(relations):
    """
    Remove exact semantic duplicates.

    Two relations are considered duplicates when they have the same:

        subject_entity_id
        predicate
        object_entity_id
        chunk_id
    """

    unique = {}
    duplicate_count = 0

    for relation in relations:
        key = (
            relation.subject_entity_id,
            relation.predicate,
            relation.object_entity_id,
            relation.chunk_id,
        )

        if key in unique:
            duplicate_count += 1
            continue

        unique[key] = relation

    return list(unique.values()), duplicate_count


def main():
    print("=" * 70)
    print("Graphitti — Relation Generation")
    print("=" * 70)

    print(f"Project root : {PROJECT_ROOT}")
    print(f"Chunks file  : {CHUNKS_FILE}")
    print(f"Entities file: {ENTITIES_FILE}")
    print()

    chunks = load_chunks()
    entities_by_chunk = load_entities()

    print(f"Loaded chunks : {len(chunks)}")
    print(f"Loaded entity-bearing chunks: {len(entities_by_chunk)}")
    print()

    extractor = RelationExtractor()

    all_relations = []

    processed_chunks = 0
    skipped_chunks = 0

    for chunk in chunks:
        chunk_entities = entities_by_chunk.get(chunk.chunk_id, [])

        if not chunk_entities:
            skipped_chunks += 1
            continue

        relations = extractor.extract_relations(
            chunk=chunk,
            entities=chunk_entities,
        )

        all_relations.extend(relations)

        processed_chunks += 1

    print(f"Processed chunks: {processed_chunks}")
    print(f"Skipped chunks  : {skipped_chunks}")
    print(f"Raw relations   : {len(all_relations)}")

    unique_relations, duplicate_count = deduplicate_relations(
        all_relations
    )

    print(f"Duplicates removed: {duplicate_count}")
    print(f"Final relations   : {len(unique_relations)}")
    print()

    output_path = save_relations(unique_relations)

    print(f"Saved relations to:")
    print(output_path)
    print()

    # Useful summary for debugging / reproducibility.
    predicate_counts = defaultdict(int)

    for relation in unique_relations:
        predicate_counts[relation.predicate] += 1

    print("Predicate distribution:")
    for predicate, count in sorted(predicate_counts.items()):
        print(f"  {predicate:20s} {count}")

    print()
    print("=" * 70)
    print("Relation generation completed successfully.")
    print("=" * 70)


if __name__ == "__main__":
    main()