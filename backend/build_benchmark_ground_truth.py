import json
from pathlib import Path


# =========================================================
# PATHS
# =========================================================

BACKEND_ROOT = Path(__file__).resolve().parent

PROJECT_ROOT = BACKEND_ROOT.parent

CHUNKS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "semantic_chunks.jsonl"
)

BENCHMARK_PATH = (
    PROJECT_ROOT
    / "data"
    / "benchmark"
    / "benchmark_queries.json"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "benchmark"
    / "benchmark_ground_truth.json"
)


# =========================================================
# LOAD CHUNKS
# =========================================================

def load_chunks():

    chunks = []

    with CHUNKS_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            chunks.append(
                json.loads(line)
            )

    return chunks


# =========================================================
# NORMALIZATION
# =========================================================

def normalize(text):

    return " ".join(
        text.lower()
        .split()
    )


# =========================================================
# FIND RELEVANT CHUNKS
# =========================================================

def find_relevant_chunks(
    chunks,
    phrases,
):

    normalized_phrases = [
        normalize(phrase)
        for phrase in phrases
    ]

    matches = []

    for chunk in chunks:

        text = normalize(
            chunk.get("text", "")
        )

        matched_phrases = []

        for phrase in normalized_phrases:

            if phrase in text:
                matched_phrases.append(
                    phrase
                )

        if matched_phrases:

            matches.append(
                {
                    "chunk_id": chunk.get(
                        "chunk_id"
                    ),
                    "text": chunk.get(
                        "text",
                        "",
                    ),
                    "matched_phrases": (
                        matched_phrases
                    ),
                }
            )

    return matches


# =========================================================
# MAIN
# =========================================================

def main():

    print("=" * 70)
    print("BUILDING BENCHMARK GROUND TRUTH")
    print("=" * 70)

    chunks = load_chunks()

    print(
        f"Loaded {len(chunks)} chunks."
    )

    with BENCHMARK_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:

        queries = json.load(file)

    benchmark = []

    for item in queries:

        matches = find_relevant_chunks(
            chunks=chunks,
            phrases=item[
                "relevant_phrases"
            ],
        )

        print()
        print(
            f"{item['id']}: "
            f"{item['query']}"
        )

        print(
            f"Matches: {len(matches)}"
        )

        for match in matches[:5]:

            print(
                "  -",
                match["chunk_id"],
                ":",
                match["text"][:120],
            )

        benchmark_entry = {
            "id": item["id"],
            "query": item["query"],
            "intent": item["intent"],
            "relevant_chunk_ids": [
                match["chunk_id"]
                for match in matches
            ],
            "relevant_phrases": item["relevant_phrases"],
        }

        benchmark.append(benchmark_entry)

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            benchmark,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print()
    print("=" * 70)
    print("GROUND TRUTH CREATED")
    print("=" * 70)

    print(
        f"Output: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()