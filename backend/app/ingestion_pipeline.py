import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from app.extraction.content_extractor import extract_content
from app.extraction.storage import save_structured_documents
from app.nlp.semantic_chunker import SemanticChunker
from app.nlp.chunk_storage import save_chunks
from app.nlp.ner import EntityRecognizer
from app.nlp.entity_storage import save_entities
from app.nlp.relation_extractor import RelationExtractor
from app.nlp.relation_storage import save_relations
from app.nlp.claim_extractor import ClaimExtractor
from app.nlp.claim_storage import save_claims


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"


def process_crawled_pages(
    pages: list[Any],
) -> dict[str, Any]:
    """Process crawled pages and ingest their knowledge into Neo4j."""

    # 1. Extract structured content from crawled HTML.
    documents = []

    for page in pages:
        html = getattr(page, "html", "") or ""
        url = getattr(page, "url", "") or ""

        if not html.strip() or not url:
            continue

        document = extract_content(html, url)

        if document.sections:
            documents.append(document)

    if not documents:
        raise ValueError(
            "No usable page content was found. "
            "Try crawling a documentation or article website."
        )

    save_structured_documents(documents)

    # 2. Convert document sections into semantic chunks.
    chunker = SemanticChunker()
    chunks = []

    for document in documents:
        chunks.extend(chunker.chunk_document(document))

    save_chunks(chunks)

    # 3. Extract entities from each chunk.
    recognizer = EntityRecognizer()
    entities = []

    for chunk in chunks:
        entities.extend(recognizer.extract_entities(chunk))

    # Remove repeated entity records within the same chunk.
    unique_entities = {}
    for entity in entities:
        key = (entity.entity_id, entity.chunk_id)
        unique_entities[key] = entity

    entities = list(unique_entities.values())
    save_entities(entities)

    # 4. Extract relations using entities from each chunk.
    entities_by_chunk = defaultdict(list)

    for entity in entities:
        entities_by_chunk[entity.chunk_id].append(entity)

    relation_extractor = RelationExtractor()
    relations = []

    for chunk in chunks:
        chunk_entities = entities_by_chunk[chunk.chunk_id]

        if len(chunk_entities) >= 2:
            relations.extend(
                relation_extractor.extract_relations(
                    chunk,
                    chunk_entities,
                )
            )

    unique_relations = {
        relation.relation_id: relation
        for relation in relations
    }
    relations = list(unique_relations.values())

    save_relations(relations)

    # 5. Convert extracted relations into claims.
    claim_extractor = ClaimExtractor()
    claims = []

    for relation in relations:
        claims.append(
            claim_extractor.extract_claim(relation)
        )

    unique_claims = {
        claim.claim_id: claim
        for claim in claims
    }
    claims = list(unique_claims.values())

    save_claims(claims)

    # 6. Ingest the generated dataset into Neo4j using
    # the existing graph-ingestion implementation.
    result = subprocess.run(
        [
            sys.executable,
            str(BACKEND_DIR / "sync_graph.py"),
        ],
        cwd=str(BACKEND_DIR),
        capture_output=True,
        text=True,
        timeout=1800,
        check=False,
    )

    if result.returncode != 0:
        details = (result.stderr or result.stdout or "").strip()

        raise RuntimeError(
            "Neo4j graph ingestion failed. "
            f"Details: {details[-4000:]}"
        )

    return {
        "pages_processed": len(documents),
        "chunks_created": len(chunks),
        "entities_extracted": len(entities),
        "relations_extracted": len(relations),
        "claims_generated": len(claims),
        "graph_ingestion": "completed",
    }