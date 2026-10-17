from app.nlp.claim_extractor import ClaimExtractor
from app.nlp.relation_models import Relation


relation = Relation(
    relation_id="relation_001",

    subject_entity_id="fastapi::framework",
    subject_text="FastAPI",
    subject_type="FRAMEWORK",

    predicate="DEPENDS_ON",

    object_entity_id="pydantic::library",
    object_text="Pydantic",
    object_type="LIBRARY",

    chunk_id="chunk_001",
    source_url="https://fastapi.tiangolo.com/",
    source_sentence="FastAPI depends on Pydantic and Starlette.",

    confidence=0.80,
)


extractor = ClaimExtractor()

claim = extractor.extract_claim(
    relation
)


print("\n========== CLAIM ==========\n")

print("Claim ID:", claim.claim_id)
print("Subject:", claim.subject_text)
print("Predicate:", claim.predicate)
print("Object:", claim.object_text)
print("Source sentence:", claim.source_sentence)
print("Source URL:", claim.source_url)
print("Chunk:", claim.chunk_id)
print("Confidence:", claim.confidence)
print("Extracted at:", claim.extracted_at)