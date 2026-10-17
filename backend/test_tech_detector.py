from app.nlp.tech_entity_detector import (
    TechnicalEntityDetector,
)


text = """
FastAPI is built on Starlette and Pydantic.
It supports OpenAPI, Swagger, OAuth2 and WebSockets.
HTTPX can be used for testing.
"""


detector = TechnicalEntityDetector()

entities = detector.detect(
    text=text,
    chunk_id="test_chunk",
    source_url="https://example.com",
)

print("\nTECHNICAL ENTITIES:\n")

for entity in entities:
    print(
        f"{entity.text:20} "
        f"{entity.label:25} "
        f"{entity.start_char}-{entity.end_char} "
        f"confidence={entity.confidence}"
    )