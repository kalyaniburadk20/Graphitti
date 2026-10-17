import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

CHUNKS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "semantic_chunks.jsonl"
)


IDS = {
    "691b148b4a40f836",
    "07228f3795c0ac4f",
    "949c8f6c2f173256",
    "a837779346657301",
    "b928a1368e7b8337",
    "896ba232af10ee15",
    "a1d1896704f930b6",
    "7d914cec5b44fe1e",
    "8994342c54b94ba3",
    "93ad4012b94b667f",
    "e8dca72a83fde7ca",
    "aef36ca0de77c0b3",
    "23c79451438c410b",
    "da3ce38adb57f120",
    "d3e0535cae5aa502",
    "664b81f0374c5348",
    "60a87b48bd2c375a",
    "69a95b69ea9d5a84",
    "5dfe233de710dbb3",
    "991c6c230b90aef0",
    "ac1af90342ff8e17",
    "6e4c96e352fe03e9",
    "5be74db2a63bd029",
    "e7f95bc77d7d0594",
    "be1e432c97db3077",
    "51d7efe76a0bb7a5",
    "05f61145ce2df1b7",
    "de05de89af21155b",
    "32af250da9293efd",
    "81c23644c4d382d1",
    "3591c6964f30bff3",
}


def main():

    found = set()

    with CHUNKS_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            chunk = json.loads(line)

            chunk_id = chunk.get("chunk_id")

            if chunk_id in IDS:

                found.add(chunk_id)

                print("\n" + "=" * 80)
                print(f"CHUNK ID: {chunk_id}")
                print("=" * 80)
                print(chunk.get("text", ""))

    print("\n" + "=" * 80)
    print(f"FOUND {len(found)} / {len(IDS)} CHUNKS")
    print("=" * 80)


if __name__ == "__main__":
    main()