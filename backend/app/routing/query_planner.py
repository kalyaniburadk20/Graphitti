from .query_plan import (
    QueryPlan,
    QueryStep,
)


class QueryPlanner:

    def plan(
        self,
        query: str,
        intent: str,
        entities: list[str],
    ) -> QueryPlan:

        # =====================================================
        # MULTI-HOP
        # =====================================================

        if intent == "MULTI_HOP":
            return self._plan_multi_hop(
                query,
                entities,
            )

        # =====================================================
        # RELATIONAL
        # =====================================================

        if intent == "RELATIONAL":

            entity = (
                entities[0]
                if entities
                else None
            )

            return QueryPlan(
                original_query=query,
                intent=intent,
                steps=[
                    QueryStep(
                        step_id=1,
                        operation="RETRIEVE",
                        target="bm25+graph",
                        entity=entity,
                    )
                ],
            )

        # =====================================================
        # LEXICAL
        # =====================================================

        if intent == "LEXICAL":

            return QueryPlan(
                original_query=query,
                intent=intent,
                steps=[
                    QueryStep(
                        step_id=1,
                        operation="RETRIEVE",
                        target="bm25",
                    )
                ],
            )

        # =====================================================
        # SEMANTIC
        # =====================================================

        if intent == "SEMANTIC":

            return QueryPlan(
                original_query=query,
                intent=intent,
                steps=[
                    QueryStep(
                        step_id=1,
                        operation="RETRIEVE",
                        target="dense+bm25",
                    )
                ],
            )

        # =====================================================
        # FALLBACK / HYBRID
        # =====================================================

        return QueryPlan(
            original_query=query,
            intent="HYBRID",
            steps=[
                QueryStep(
                    step_id=1,
                    operation="RETRIEVE",
                    target="bm25+dense+graph",
                )
            ],
        )

    # =========================================================
    # MULTI-HOP PLANNING
    # =========================================================

    def _plan_multi_hop(
        self,
        query: str,
        entities: list[str],
    ) -> QueryPlan:

        source_entity = (
            entities[0]
            if entities
            else None
        )

        target_entity = (
            entities[1]
            if len(entities) > 1
            else None
        )

        query_lower = query.lower()

        steps = []

        # -----------------------------------------------------
        # Explicit DEPENDS_ON -> USES path
        # -----------------------------------------------------

        if (
            "depend on" in query_lower
            and "uses" in query_lower
        ):

            steps.append(
                QueryStep(
                    step_id=1,
                    operation="TRAVERSE",
                    entity=source_entity,
                    predicate="DEPENDS_ON",
                )
            )

            steps.append(
                QueryStep(
                    step_id=2,
                    operation="FILTER_PATH",
                    predicate="USES",
                    target=target_entity,
                )
            )

        else:

            # -------------------------------------------------
            # Generic bounded graph traversal
            # -------------------------------------------------

            steps.append(
                QueryStep(
                    step_id=1,
                    operation="TRAVERSE",
                    entity=source_entity,
                )
            )

        return QueryPlan(
            original_query=query,
            intent="MULTI_HOP",
            steps=steps,
        )

    # =========================================================
    # REPLANNING
    # =========================================================

    def replan(
        self,
        state,
        verification_failed: bool = False,
    ):

        attempt = state.attempts

        # -----------------------------------------------------
        # Attempt 1
        #
        # Use lexical + dense retrieval.
        # -----------------------------------------------------

        if attempt == 1:

            return QueryPlan(
                original_query=state.query,
                intent="HYBRID",
                steps=[
                    QueryStep(
                        step_id=1,
                        operation="RETRIEVE",
                        target="bm25+dense",
                    )
                ],
            )

        # -----------------------------------------------------
        # Attempt 2
        #
        # Add graph retrieval.
        # -----------------------------------------------------

        if attempt == 2:

            return QueryPlan(
                original_query=state.query,
                intent="HYBRID",
                steps=[
                    QueryStep(
                        step_id=1,
                        operation="RETRIEVE",
                        target="bm25+dense+graph",
                    )
                ],
            )

        # -----------------------------------------------------
        # Final attempt
        #
        # Full retrieval remains bounded and deterministic.
        # -----------------------------------------------------

        return QueryPlan(
            original_query=state.query,
            intent="FINAL_ATTEMPT",
            steps=[
                QueryStep(
                    step_id=1,
                    operation="RETRIEVE",
                    target="bm25+dense+graph",
                )
            ],
            termination_reason=(
                "Maximum replanning depth reached."
            ),
        )