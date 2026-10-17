import json
from datetime import datetime, timezone
from pathlib import Path


# =========================================================
# GRAPHITTI PROJECT ROOT
# =========================================================

# agent_logger.py
#   -> agents
#   -> app
#   -> backend
#   -> graphitti
#
# parents[3] = graphitti

PROJECT_ROOT = Path(__file__).resolve().parents[3]

LOG_PATH = (
    PROJECT_ROOT
    / "data"
    / "logs"
    / "agent_trace.jsonl"
)


def log_trace(state):
    """
    Persist complete agent trace and latency metrics
    into:

        graphitti/data/logs/agent_trace.jsonl
    """

    # -----------------------------------------------------
    # Create logs directory automatically
    # -----------------------------------------------------

    LOG_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # -----------------------------------------------------
    # Build JSON payload
    # -----------------------------------------------------

    payload = {
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),

        "query": state.query,

        "status": state.status,

        "intent": state.intent,

        "intent_confidence": (
            state.intent_confidence
        ),

        "attempts": state.attempts,

        "entity_candidates": (
            state.entity_candidates
        ),

        "confidence": state.confidence,

        "termination_reason": (
            state.termination_reason
        ),

        # =================================================
        # AGENT TRACE
        # =================================================

        "trace": [
            {
                "attempt": trace.attempt,
                "status": trace.status,
                "intent": trace.intent,
                "strategies": trace.strategies,
                "result_count": trace.result_count,
                "confidence": trace.confidence,
                "message": trace.message,
            }
            for trace in state.trace
        ],

        # =================================================
        # LATENCY METRICS
        # =================================================

        "metrics": {
            "total_ms": (
                state.metrics.total_ms
            ),

            "stages": [
                {
                    "stage": timing.stage,
                    "duration_ms": timing.duration_ms,
                }
                for timing in state.metrics.stages
            ],
        },
    }

    # -----------------------------------------------------
    # Append one complete run as one JSONL record
    # -----------------------------------------------------

    with LOG_PATH.open(
        "a",
        encoding="utf-8",
    ) as file:

        file.write(
            json.dumps(
                payload,
                ensure_ascii=False,
            )
            + "\n"
        )

    # -----------------------------------------------------
    # Debug confirmation
    # -----------------------------------------------------

    print(
        f"[TRACE LOGGED] {LOG_PATH}"
    )