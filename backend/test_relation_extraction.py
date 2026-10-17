from app.nlp.chunking_models import SemanticChunk
from app.nlp.entity_models import Entity
from app.nlp.relation_extractor import RelationExtractor


tests = [
    "FastAPI uses Pydantic.",
    "FastAPI is based on Starlette.",
    "FastAPI is built on Starlette.",
    "FastAPI supports OAuth2.",
    "FastAPI is compatible with OpenAPI.",
    "FastAPI depends on Pydantic and Starlette.",
]


extractor = RelationExtractor()


for index, text in enumerate(tests):

    print("\n" + "=" * 70)
    print(f"TEST {index + 1}")
    print(text)

    chunk = SemanticChunk(
        chunk_id=f"test_{index}",
        document_url="https://example.com",
        section_heading="Test",
        section_level=1,
        text=text,
        chunk_index=index,
        token_estimate=len(text.split()),
    )

    # Manually create entities.
    if "Pydantic" in text:
        entities = [
            Entity(
                entity_id="fastapi",
                text="FastAPI",
                label="FRAMEWORK",
                start_char=text.index("FastAPI"),
                end_char=text.index("FastAPI") + len("FastAPI"),
                chunk_id=chunk.chunk_id,
                source_url=chunk.document_url,
                confidence=0.99,
            ),
            Entity(
                entity_id="pydantic",
                text="Pydantic",
                label="LIBRARY",
                start_char=text.index("Pydantic"),
                end_char=text.index("Pydantic") + len("Pydantic"),
                chunk_id=chunk.chunk_id,
                source_url=chunk.document_url,
                confidence=0.99,
            ),
        ]

    elif "OAuth2" in text:
        entities = [
            Entity(
                entity_id="fastapi",
                text="FastAPI",
                label="FRAMEWORK",
                start_char=text.index("FastAPI"),
                end_char=text.index("FastAPI") + len("FastAPI"),
                chunk_id=chunk.chunk_id,
                source_url=chunk.document_url,
                confidence=0.99,
            ),
            Entity(
                entity_id="oauth2",
                text="OAuth2",
                label="PROTOCOL",
                start_char=text.index("OAuth2"),
                end_char=text.index("OAuth2") + len("OAuth2"),
                chunk_id=chunk.chunk_id,
                source_url=chunk.document_url,
                confidence=0.99,
            ),
        ]

    elif "OpenAPI" in text:
        entities = [
            Entity(
                entity_id="fastapi",
                text="FastAPI",
                label="FRAMEWORK",
                start_char=text.index("FastAPI"),
                end_char=text.index("FastAPI") + len("FastAPI"),
                chunk_id=chunk.chunk_id,
                source_url=chunk.document_url,
                confidence=0.99,
            ),
            Entity(
                entity_id="openapi",
                text="OpenAPI",
                label="STANDARD",
                start_char=text.index("OpenAPI"),
                end_char=text.index("OpenAPI") + len("OpenAPI"),
                chunk_id=chunk.chunk_id,
                source_url=chunk.document_url,
                confidence=0.99,
            ),
        ]

    else:
        entities = [
            Entity(
                entity_id="fastapi",
                text="FastAPI",
                label="FRAMEWORK",
                start_char=text.index("FastAPI"),
                end_char=text.index("FastAPI") + len("FastAPI"),
                chunk_id=chunk.chunk_id,
                source_url=chunk.document_url,
                confidence=0.99,
            ),
            Entity(
                entity_id="starlette",
                text="Starlette",
                label="LIBRARY",
                start_char=text.index("Starlette"),
                end_char=text.index("Starlette") + len("Starlette"),
                chunk_id=chunk.chunk_id,
                source_url=chunk.document_url,
                confidence=0.99,
            ),
        ]

    relations = extractor.extract_relations(
        chunk,
        entities,
    )

    if relations:
        for relation in relations:
            print(
                f"✅ "
                f"{relation.subject_text} "
                f"--[{relation.predicate}]--> "
                f"{relation.object_text}"
            )
    else:
        print("❌ No relation extracted")