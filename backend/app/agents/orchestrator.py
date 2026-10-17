import time

from app.retrieval.routing_service import (
    RoutingService,
)

from app.routing.query_planner import (
    QueryPlanner,
)

from app.retrieval.retrieval_models import (
    RetrievalResult,
)

from .agent_state import AgentState
from .evidence_checker import EvidenceChecker
from .answer_synthesizer import AnswerSynthesizer
from .faithfulness_checker import FaithfulnessChecker
from .trace_models import AgentTrace
from .agent_logger import log_trace


class GraphittiOrchestrator:

    def __init__(self):

        self.retrieval = RoutingService()

        self.planner = QueryPlanner()

        self.checker = EvidenceChecker()

        self.synthesizer = AnswerSynthesizer()

        self.faithfulness = FaithfulnessChecker()

    # =========================================================
    # TRACE RECORDING
    # =========================================================

    def _record_trace(
        self,
        state: AgentState,
        status: str,
        strategies: list[str] | None = None,
        message: str = "",
    ):
        state.trace.append(
            AgentTrace(
                attempt=state.attempts,
                status=status,
                intent=state.intent,
                strategies=(
                    strategies
                    if strategies is not None
                    else []
                ),
                result_count=len(state.results),
                confidence=state.confidence,
                message=message,
            )
        )

    # =========================================================
    # TIMING HELPER
    # =========================================================

    def _timed(
        self,
        state: AgentState,
        stage: str,
        fn,
    ):
        """
        Execute a function and record its latency.
        """

        start = time.perf_counter()

        result = fn()

        duration_ms = (
            time.perf_counter() - start
        ) * 1000

        state.metrics.add_stage(
            stage=stage,
            duration_ms=duration_ms,
        )

        return result

    # =========================================================
    # RETRIEVAL STRATEGY SELECTION
    # =========================================================

    def _get_strategies(
        self,
        state: AgentState,
    ) -> list[str]:

        # -----------------------------------------------------
        # First attempt follows the router.
        # -----------------------------------------------------

        if state.attempts == 1:

            if state.intent == "RELATIONAL":
                return [
                    "bm25",
                    "graph",
                ]

            if state.intent == "LEXICAL":
                return [
                    "bm25",
                ]

            if state.intent == "SEMANTIC":
                return [
                    "dense",
                    "bm25",
                ]

            if state.intent == "MULTI_HOP":
                return [
                    "graph",
                ]

        # -----------------------------------------------------
        # Later attempts follow the replanned target.
        # -----------------------------------------------------

        if not state.plan:
            return [
                "bm25",
                "dense",
                "graph",
            ]

        if not state.plan.steps:
            return [
                "bm25",
                "dense",
                "graph",
            ]

        target = state.plan.steps[0].target

        if target == "bm25":
            return [
                "bm25",
            ]

        if target == "dense":
            return [
                "dense",
            ]

        if target == "graph":
            return [
                "graph",
            ]

        if target == "bm25+graph":
           return [
        "bm25",
        "graph",
    ]

        if target == "dense+bm25":
            return [
                "dense",
                "bm25",
            ]

        if target == "bm25+dense":
            return [
                "bm25",
                "dense",
            ]

        if target == "bm25+dense+graph":
            return [
                "bm25",
                "dense",
                "graph",
            ]

        return [
            "bm25",
            "dense",
            "graph",
        ]

    # =========================================================
    # MULTI-HOP EXECUTION
    # =========================================================

    def _execute_multi_hop_plan(
        self,
        state: AgentState,
    ) -> list[RetrievalResult]:

        if not state.plan:
            return []

        steps = state.plan.steps

        if len(steps) < 2:
            return []

        first_step = steps[0]
        second_step = steps[1]

        if (
            first_step.operation != "TRAVERSE"
            or second_step.operation != "FILTER_PATH"
        ):
            return []

        if not first_step.entity:
            return []

        if not first_step.predicate:
            return []

        if not second_step.predicate:
            return []

        # -----------------------------------------------------
        # Run graph multi-hop retrieval.
        # -----------------------------------------------------

        raw_results = (
            self.retrieval.graph.multi_hop_search(
                source_entity=first_step.entity,
                first_predicate=(
                    first_step.predicate
                ),
                second_predicate=(
                    second_step.predicate
                ),
                target_entity=(
                    second_step.target
                ),
                max_hops=2,
            )
        )

        results = []

        for index, item in enumerate(
            raw_results
        ):

            evidence_parts = []

            first_evidence = item.get(
                "first_evidence"
            )

            second_evidence = item.get(
                "second_evidence"
            )

            if first_evidence:
                evidence_parts.append(
                    first_evidence
                )

            if second_evidence:
                evidence_parts.append(
                    second_evidence
                )

            evidence_text = " ".join(
                evidence_parts
            ).strip()

            first_confidence = float(
                item.get(
                    "first_confidence",
                    0.0,
                )
                or 0.0
            )

            second_confidence = float(
                item.get(
                    "second_confidence",
                    0.0,
                )
                or 0.0
            )

            # Conservative path confidence:
            # weakest hop determines path confidence.
            path_confidence = min(
                first_confidence,
                second_confidence,
            )

            source_url = (
                item.get(
                    "first_source",
                    "",
                )
                or item.get(
                    "second_source",
                    "",
                )
                or ""
            )

            source = item.get("source") or first_step.entity
            middle = item.get("middle")
            target = item.get("target")

            results.append(
                RetrievalResult(
                    chunk_id=(
                        f"multi-hop-{state.attempts}-{index}-hop-1"
                    ),
                    text=(
                        first_evidence
                        or f"{source} {first_step.predicate} {middle}"
                    ).strip(),
                    score=path_confidence,
                    source_url=item.get("first_source") or "",
                    section_heading="multi_hop",
                    strategy="graph_multi_hop",
                    claim_id=item.get("first_claim_id"),
                    subject=source,
                    predicate=first_step.predicate,
                    object=middle,
                    confidence=first_confidence,
                )
            )

            results.append(
                RetrievalResult(
                    chunk_id=(
                        f"multi-hop-{state.attempts}-{index}-hop-2"
                    ),
                    text=(
                        second_evidence
                        or f"{middle} {second_step.predicate} {target}"
                    ).strip(),
                    score=path_confidence,
                    source_url=item.get("second_source") or "",
                    section_heading="multi_hop",
                    strategy="graph_multi_hop",
                    claim_id=item.get("second_claim_id"),
                    subject=middle,
                    predicate=second_step.predicate,
                    object=target,
                    confidence=second_confidence,
                )
            )

        return results

    # =========================================================
    # MAIN RUN
    # =========================================================

    def run(
        self,
        query: str,
    ) -> AgentState:

        # -----------------------------------------------------
        # Create state.
        # -----------------------------------------------------


        state = AgentState(
            query=query
        )

        # -----------------------------------------------------
        # Start total latency timer.
        # -----------------------------------------------------

        run_start = time.perf_counter()

        # =====================================================
        # STEP 1 — ROUTING
        # =====================================================

        state.status = "ROUTING"

        routing_result = self._timed(
            state,
            "routing",
            lambda: (
                self.retrieval.router.classify(
                    query
                )
            ),
        )

        state.intent = (
            routing_result.intent
        )

        state.intent_confidence = (
            routing_result.confidence
        )

        self._record_trace(
            state=state,
            status="ROUTING",
            message=(
                f"Query classified as "
                f"{state.intent}."
            ),
        )

        # =====================================================
        # STEP 2 — ENTITY DETECTION
        # =====================================================

        state.status = (
            "ENTITY_DETECTION"
        )

        entities = self._timed(
            state,
            "entity_detection",
            lambda: (
                self.retrieval
                ._extract_entity_candidates(
                    query
                )
            ),
        )

        state.entity_candidates = entities

        self._record_trace(
            state=state,
            status="ENTITY_DETECTION",
            message=(
                f"Detected entities: "
                f"{entities}"
            ),
        )

        # =====================================================
        # STEP 3 — INITIAL PLAN
        # =====================================================

        state.status = "PLANNING"

        state.plan = self._timed(
            state,
            "planning",
            lambda: (
                self.planner.plan(
                    query=query,
                    intent=state.intent,
                    entities=entities,
                )
            ),
        )

        self._record_trace(
            state=state,
            status="PLANNING",
            message=(
                f"Created plan with "
                f"{len(state.plan.steps)} "
                f"step(s)."
            ),
        )

        # =====================================================
        # STEP 4 — BOUNDED RETRIEVAL / REPLANNING LOOP
        # =====================================================

        while (
            state.attempts
            < state.max_attempts
        ):

            state.attempts += 1

            state.status = (
                f"RETRIEVING_ATTEMPT_"
                f"{state.attempts}"
            )

            # =================================================
            # MULTI-HOP RETRIEVAL
            # =================================================

            if state.intent == "MULTI_HOP":

                state.results = self._timed(
                    state,
                    (
                        "multi_hop_retrieval_"
                        f"attempt_{state.attempts}"
                    ),
                    lambda: (
                        self._execute_multi_hop_plan(
                            state
                        )
                    ),
                )

                self._record_trace(
                    state=state,
                    status=(
                        f"RETRIEVING_ATTEMPT_"
                        f"{state.attempts}"
                    ),
                    strategies=[
                        "graph_multi_hop"
                    ],
                    message=(
                        "Executed multi-hop "
                        "graph plan."
                    ),
                )

            # =================================================
            # NORMAL RETRIEVAL
            # =================================================

            else:

                strategies = (
                    self._get_strategies(
                        state
                    )
                )

                entity_name = (
                    entities[0]
                    if entities
                    else None
                )

                state.results = self._timed(
                    state,
                    (
                        "retrieval_attempt_"
                        f"{state.attempts}"
                    ),
                    lambda: (
                        self.retrieval
                        .search_with_strategies(
                            query=query,
                            strategies=strategies,
                            entity_name=(
                                entity_name
                            ),
                            top_k=5,
                        )
                    ),
                )

                self._record_trace(
                    state=state,
                    status=(
                        f"RETRIEVING_ATTEMPT_"
                        f"{state.attempts}"
                    ),
                    strategies=strategies,
                    message=(
                        "Retrieved evidence "
                        "using "
                        f"{', '.join(strategies)}."
                    ),
                )

            # =================================================
            # STEP 5 — EVIDENCE CHECK
            # =================================================

            state.status = (
                "CHECKING_EVIDENCE"
            )

            evidence_result = self._timed(
                state,
                "evidence_check",
                lambda: (
                    self.checker.evaluate(
                        state.results
                    )
                ),
            )

            state.confidence = (
                evidence_result.score
            )

            self._record_trace(
                state=state,
                status="CHECKING_EVIDENCE",
                message=(
                    evidence_result.reason
                ),
            )

            # -------------------------------------------------
            # Evidence insufficient
            # -------------------------------------------------

            if not evidence_result.sufficient:

                if (
                    state.attempts
                    >= state.max_attempts
                ):

                    state.status = (
                        "TERMINATED"
                    )

                    state.termination_reason = (
                        "Maximum retrieval "
                        "attempts reached "
                        "without sufficient "
                        "evidence."
                    )

                    self._record_trace(
                        state=state,
                        status="TERMINATED",
                        message=(
                            state.termination_reason
                        ),
                    )

                    break

                state.status = (
                    "REPLANNING"
                )

                state.plan = (
                    self.planner.replan(
                        state,
                        verification_failed=False,
                    )
                )

                self._record_trace(
                    state=state,
                    status="REPLANNING",
                    message=(
                        "Evidence was "
                        "insufficient. "
                        "Created a new "
                        "retrieval plan."
                    ),
                )

                continue

            # =================================================
            # STEP 6 — ANSWER SYNTHESIS
            # =================================================

            state.status = (
                "SYNTHESIZING"
            )

            synthesized = self._timed(
                state,
                "synthesis",
                lambda: (
                    self.synthesizer.synthesize(
                        query=query,
                        results=state.results,
                    )
                ),
            )

            state.answer = (
                synthesized.answer
            )

            state.evidence = (
                synthesized.citations
            )

            state.confidence = min(
                state.confidence,
                synthesized.confidence,
            )

            self._record_trace(
                state=state,
                status="SYNTHESIZING",
                message=(
                    "Generated answer "
                    "from retrieved "
                    "evidence."
                ),
            )

            # =================================================
            # STEP 7 — FAITHFULNESS VERIFICATION
            # =================================================

            state.status = "VERIFYING"

            # -------------------------------------------------
            # Relational / Multi-hop queries:
            # perform claim-level verification.
            # -------------------------------------------------

            if state.intent in {
                "RELATIONAL",
                "MULTI_HOP",
            }:

                verification = self._timed(
                    state,
                    "faithfulness",
                    lambda: (
                        self.faithfulness.verify(
                            answer=state.answer,
                            evidence=state.evidence,
                        )
                    ),
                )

                state.confidence = min(
                    state.confidence,
                    verification.confidence,
                )

                self._record_trace(
                    state=state,
                    status="VERIFYING",
                    message=(
                        "Faithfulness result: "
                        f"{verification.faithful}. "
                        f"{verification.reason}"
                    ),
                )

                # ---------------------------------------------
                # Verification passed
                # ---------------------------------------------

                if verification.faithful:

                    state.status = (
                        "COMPLETED"
                    )

                    state.termination_reason = (
                        "Answer passed "
                        "evidence and "
                        "claim-level "
                        "faithfulness "
                        "verification."
                    )

                    self._record_trace(
                        state=state,
                        status="COMPLETED",
                        message=(
                            "Answer passed "
                            "faithfulness "
                            "verification."
                        ),
                    )

                    break

                # ---------------------------------------------
                # Verification failed at maximum attempt
                # ---------------------------------------------

                if (
                    state.attempts
                    >= state.max_attempts
                ):

                    state.status = (
                        "TERMINATED"
                    )

                    state.termination_reason = (
                        "Maximum "
                        "verification "
                        "attempts reached "
                        "without a "
                        "faithful answer."
                    )

                    self._record_trace(
                        state=state,
                        status="TERMINATED",
                        message=(
                            state.termination_reason
                        ),
                    )

                    break

                # ---------------------------------------------
                # Replan after verification failure
                # ---------------------------------------------

                state.status = (
                    "REPLANNING"
                )

                state.plan = (
                    self.planner.replan(
                        state,
                        verification_failed=True,
                    )
                )

                self._record_trace(
                    state=state,
                    status="REPLANNING",
                    message=(
                        "Faithfulness "
                        "verification "
                        "failed. Created "
                        "a new plan."
                    ),
                )

                continue

            # =================================================
            # LEXICAL / SEMANTIC QUERIES
            # =================================================

            else:

                state.status = (
                    "COMPLETED"
                )

                state.termination_reason = (
                    "Answer grounded in "
                    "sufficient retrieved "
                    "evidence."
                )

                self._record_trace(
                    state=state,
                    status="COMPLETED",
                    message=(
                        "Answer grounded "
                        "in retrieved "
                        "evidence."
                    ),
                )

                break

        # =====================================================
        # TOTAL LATENCY
        # =====================================================

        state.metrics.total_ms = round(
            (
                time.perf_counter()
                - run_start
            ) * 1000,
            2,
        )

        # =====================================================
        # PERSIST TRACE + METRICS
        # =====================================================

        try:
            log_trace(state)

        except Exception as exc:
            # Logging must never break the
            # actual Graphitti answer pipeline.
            print(
                "Warning: failed to persist "
                f"agent trace: {exc}"
            )

        return state

    # =========================================================
    # RESOURCE CLEANUP
    # =========================================================

    def close(self):

        self.retrieval.graph.close()