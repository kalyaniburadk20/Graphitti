from app.nlp.entity_linker import EntityLinker
from app.nlp.entity_models import Entity


linker = EntityLinker()

entities = [
    Entity(
        entity_id="1",
        text="FastAPI",
        label="FRAMEWORK",
        start_char=0,
        end_char=7,
        chunk_id="chunk_1",
        source_url="https://example.com/1",
        confidence=0.8,
    ),
    Entity(
        entity_id="2",
        text="fastapi",
        label="FRAMEWORK",
        start_char=0,
        end_char=7,
        chunk_id="chunk_2",
        source_url="https://example.com/2",
        confidence=0.8,
    ),
    Entity(
        entity_id="3",
        text="Fast API",
        label="FRAMEWORK",
        start_char=0,
        end_char=8,
        chunk_id="chunk_3",
        source_url="https://example.com/3",
        confidence=0.8,
    ),
]


for entity in entities:

    canonical = linker.link(entity)

    print(
        f"{entity.text:15}"
        f"→ "
        f"{canonical.canonical_name:15}"
        f" ({canonical.entity_type})"
    )