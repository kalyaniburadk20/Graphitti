import logging
import json
from pathlib import Path
from app.graph.neo4j_client import Neo4jClient
from contextlib import asynccontextmanager
from dataclasses import asdict
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.agents.orchestrator import GraphittiOrchestrator
from app.crawler.simple_crawler import crawl_website
from app.crawler.storage import save_pages


logger = logging.getLogger(__name__)

_orchestrator: GraphittiOrchestrator | None = None


def get_orchestrator() -> GraphittiOrchestrator:
    """Create the orchestrator on the first query and reuse it."""
    global _orchestrator

    if _orchestrator is None:
        _orchestrator = GraphittiOrchestrator()

    return _orchestrator


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Release Neo4j resources when the API shuts down."""
    yield

    global _orchestrator

    if _orchestrator is not None:
        _orchestrator.close()
        _orchestrator = None


app = FastAPI(
    title="Graphitti",
    description="Graph-Native Web Intelligence",
    version="0.1.0",
    lifespan=lifespan,
)

# Allow the local Vite frontend to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class CrawlRequest(BaseModel):
    url: str
    max_depth: int = 2
    max_pages: int = 20


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)


@app.get("/")
def root():
    return {
        "project": "Graphitti",
        "status": "running",
        "version": "0.1.0",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }

GRAPH_RELATION_TYPES = [
    "USES",
    "DEPENDS_ON",
    "BUILT_ON",
    "SUPPORTS",
    "REQUIRES",
    "PROVIDES",
    "INCLUDES",
    "IMPLEMENTS",
    "REPLACES",
    "COMPATIBLE_WITH",
    "INTEGRATES_WITH",
    "VALIDATES",
    "TESTED_WITH",
]


@app.get("/graph")
def graph_snapshot():
    """Return actual Neo4j entities, semantic edges and graph counts."""

    client = Neo4jClient()

    try:
        with client.driver.session(
            database=client.database
        ) as session:

            stats_record = session.run(
                """
                CALL {
                    MATCH (n:Page)
                    RETURN count(n) AS pages
                }
                CALL {
                    MATCH (n:Chunk)
                    RETURN count(n) AS chunks
                }
                CALL {
                    MATCH (n:Entity)
                    RETURN count(n) AS entities
                }
                CALL {
                    MATCH (n:Claim)
                    RETURN count(n) AS claims
                }
                CALL {
                    MATCH (source:Entity)-[r]->(target:Entity)
                    WHERE type(r) IN $semantic_types
                    RETURN count(r) AS relations
                }
                RETURN pages, chunks, entities, claims, relations
                """,
                semantic_types=GRAPH_RELATION_TYPES,
            ).single()

            nodes = session.run(
                """
                MATCH (e:Entity)
                RETURN
                    e.entity_id AS id,
                    e.name AS name,
                    e.type AS entity_type
                ORDER BY name
                """
            ).data()

            edges = session.run(
                """
                MATCH (source:Entity)-[r]->(target:Entity)
                WHERE type(r) IN $semantic_types
                RETURN
                    source.entity_id AS source_id,
                    source.name AS source,
                    type(r) AS predicate,
                    target.entity_id AS target_id,
                    target.name AS target,
                    r.confidence AS confidence,
                    r.claim_id AS claim_id,
                    r.source_url AS source_url
                ORDER BY source, predicate, target
                """,
                semantic_types=GRAPH_RELATION_TYPES,
            ).data()

            return {
                "status": "ok",
                "counts": {
                    "pages": stats_record["pages"],
                    "chunks": stats_record["chunks"],
                    "entities": stats_record["entities"],
                    "claims": stats_record["claims"],
                    "relations": stats_record["relations"],
                },
                "nodes": nodes,
                "edges": edges,
            }

    except Exception as exc:
        logger.exception("Failed to fetch Neo4j graph data")

        raise HTTPException(
            status_code=500,
            detail="Unable to fetch graph data. Check backend logs.",
        ) from exc

    finally:
        client.close()

@app.get("/benchmark")
def benchmark_snapshot():
    """Return the latest saved retrieval benchmark summaries."""

    benchmark_path = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "benchmark"
        / "benchmark_results.json"
    )

    if not benchmark_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Benchmark results file was not found.",
        )

    try:
        with benchmark_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

    except (OSError, json.JSONDecodeError) as exc:
        logger.exception("Failed to read benchmark results")

        raise HTTPException(
            status_code=500,
            detail="Unable to read benchmark results.",
        ) from exc

    strategies = {}

    for name in ("bm25", "dense", "graph", "hybrid_rrf"):
        result = data.get(name, {})
        summary = result.get("summary", {})

        if summary:
            strategies[name] = summary

    multi_hop_result = data.get("multi_hop", {})
    multi_hop_summary = multi_hop_result.get("summary")

    if not multi_hop_summary:
        multi_hop_summary = {
            key: value
            for key, value in multi_hop_result.items()
            if key != "queries"
        }

    return {
        "status": "ok",
        "strategies": strategies,
        "multi_hop": multi_hop_summary,
    }


@app.post("/query")
def query_graph(request: QueryRequest):
    """Run a question through the Graphitti agent pipeline."""

    query_text = request.query.strip()

    if not query_text:
        raise HTTPException(
            status_code=422,
            detail="Query must not be empty.",
        )

    try:
        orchestrator = get_orchestrator()
        state = orchestrator.run(query_text)

        plan = None

        if state.plan is not None:
            plan = {
                "intent": state.plan.intent,
                "termination_reason": (
                    getattr(
                        state.plan,
                        "termination_reason",
                        None,
                    )
                ),
                "steps": [
                    {
                        "step_id": step.step_id,
                        "operation": step.operation,
                        "target": step.target,
                        "entity": step.entity,
                        "predicate": step.predicate,
                    }
                    for step in state.plan.steps
                ],
            }

        return {
            "query": state.query,
            "answer": state.answer,
            "intent": state.intent,
            "intent_confidence": state.intent_confidence,
            "entities": state.entity_candidates,
            "status": state.status,
            "confidence": state.confidence,
            "attempts": state.attempts,
            "termination_reason": state.termination_reason,
            "latency_ms": state.metrics.total_ms,
            "plan": plan,
            "results": [
                asdict(result)
                for result in state.results
            ],
            "citations": [
                asdict(citation)
                for citation in state.evidence
            ],
            "trace": [
                asdict(event)
                for event in state.trace
            ],
        }

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception("Graphitti query failed")

        raise HTTPException(
            status_code=500,
            detail="The query pipeline failed. Check the backend logs.",
        ) from exc


@app.post("/crawl")
def crawl(request: CrawlRequest):
    try:
        pages = crawl_website(
            start_url=request.url,
            max_depth=request.max_depth,
            max_pages=request.max_pages,
        )

        output_path = save_pages(
            pages,
            filename="crawl_pages.jsonl",
        )

        return {
            "start_url": request.url,
            "pages_crawled": len(pages),
            "dataset": str(output_path),
            "pages": [
                {
                    "url": page.url,
                    "title": page.title,
                    "depth": page.depth,
                    "parent_url": page.parent_url,
                    "content_preview": page.content[:500],
                    "crawled_at": page.crawled_at,
                }
                for page in pages
            ],
        }

    except Exception as exc:
        logger.exception("Website crawling failed")

        raise HTTPException(
            status_code=500,
            detail="Website crawling failed. Check the backend logs.",
        ) from exc