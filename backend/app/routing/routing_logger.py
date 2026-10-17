import json
from pathlib import Path


PROJECT_ROOT = (
    Path(__file__).resolve().parents[3]
)

LOG_DIR = (
    PROJECT_ROOT
    / "data"
    / "logs"
)

LOG_FILE = (
    LOG_DIR
    / "routing.jsonl"
)


def log_routing_decision(
    decision,
    entity_candidates,
):

    LOG_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    record = {
        "query": decision.query,
        "intent": decision.intent,
        "confidence": decision.confidence,
        "retrievers": decision.retrievers,
        "reason": decision.reason,
        "entity_candidates": entity_candidates,
    }

    with LOG_FILE.open(
        "a",
        encoding="utf-8",
    ) as file:

        file.write(
            json.dumps(
                record,
                ensure_ascii=False,
            )
            + "\n"
        )