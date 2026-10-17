from app.agents.orchestrator import (
    GraphittiOrchestrator,
)


orchestrator = GraphittiOrchestrator()


queries = [
    "What does FastAPI depend on?",
    "Which page mentions ORJSONResponse?",
    "Explain FastAPI dependency injection",
    "What does FastAPI depend on that also uses HTTPX?",
]


try:

    for query in queries:

        print(
            "\n" + "=" * 90
        )

        state = orchestrator.run(
            query
        )

        print(
            f"PLAN INTENT: "
            f"{state.plan.intent}"
        )

        print(
            "PLAN STEPS:"
        )

        for step in state.plan.steps:

            print(
                f"  step={step.step_id} "
                f"operation={step.operation} "
                f"target={step.target}"
            )

        print(
            f"QUERY: {state.query}"
        )

        print(
            f"INTENT: {state.intent}"
        )

        print(
            f"INTENT CONFIDENCE: "
            f"{state.intent_confidence:.2f}"
        )

        print(
            f"ENTITIES: "
            f"{state.entity_candidates}"
        )

        print(
            f"ATTEMPTS: "
            f"{state.attempts}"
        )

        print(
            f"STATUS: "
            f"{state.status}"
        )

        print(
            f"EVIDENCE CONFIDENCE: "
            f"{state.confidence:.4f}"
        )

        print(
            f"TERMINATION: "
            f"{state.termination_reason}"
        )

        print(
            "\nRESULTS:"
        )

        for result in state.results[:5]:

            print(
                f"\n[{result.strategy}] "
                f"{result.score:.6f}"
            )

            print(
                result.text[:300]
            )

        print(
            "\n========== AGENT TRACE ==========\n"
        )

        for event in state.trace:

            print(
                f"\nAttempt: {event.attempt}"
            )

            print(
                f"Status: {event.status}"
            )

            print(
                f"Intent: {event.intent}"
            )

            if event.strategies:
                print(
                    f"Strategies: "
                    f"{event.strategies}"
                )

            print(
                f"Results: "
                f"{event.result_count}"
            )

            print(
                f"Confidence: "
                f"{event.confidence:.4f}"
            )

            print(
                f"Message: "
                f"{event.message}"
            )

finally:

    orchestrator.close()