from app.crawler.simple_crawler import crawl_website
from app.extraction.content_extractor import extract_content

from app.nlp.semantic_chunker import SemanticChunker
from app.nlp.ner import EntityRecognizer
from app.nlp.entity_storage import save_entities
from app.nlp.entity_linker import EntityLinker

from app.nlp.entity_filter import filter_entities

from app.nlp.relation_extractor import RelationExtractor
from app.nlp.relation_storage import save_relations

from app.nlp.claim_extractor import ClaimExtractor
from app.nlp.claim_storage import save_claims


# ---------------------------------------------------------
# 1. Crawl
# ---------------------------------------------------------

pages = crawl_website(
    "https://fastapi.tiangolo.com/",
    max_depth=0,
    max_pages=1,
)


# ---------------------------------------------------------
# 2. Initialize pipeline
# ---------------------------------------------------------

chunker = SemanticChunker()
recognizer = EntityRecognizer()
linker = EntityLinker()
relation_extractor = RelationExtractor()
claim_extractor = ClaimExtractor()

all_entities = []
all_relations = []
all_claims = []


# ---------------------------------------------------------
# 3. Process every page
# ---------------------------------------------------------

for page in pages:

    document = extract_content(
        html=page.html,
        url=page.url,
    )

    chunks = chunker.chunk_document(
        document
    )

    print(
        f"\nProcessing {len(chunks)} chunks..."
    )

    # -----------------------------------------------------
    # 4. Process every chunk
    # -----------------------------------------------------

    for chunk_index, chunk in enumerate(chunks):

        entities = recognizer.extract_entities(
            chunk
        )

        # Remove obvious noise
        entities = filter_entities(
            entities
        )

        # Keep ALL entities globally
        all_entities.extend(
            entities
        )

        # ---------------------------------------------
        # Entity linking
        # ---------------------------------------------

        for entity in entities:

            canonical = linker.link(
                entity
            )

            print(
                f"mention={entity.text!r} "
                f"→ "
                f"canonical="
                f"{canonical.canonical_name!r} "
                f"type="
                f"{canonical.entity_type}"
            )

        # ---------------------------------------------
        # Relation extraction
        # ---------------------------------------------

        relations = (
            relation_extractor.extract_relations(
                chunk,
                entities,
            )
        )

        all_relations.extend(
            relations
        )

        for relation in relations:

            claim = claim_extractor.extract_claim(
                relation
            )

            all_claims.append(claim)



# ---------------------------------------------------------
# 5. Save entities
# ---------------------------------------------------------

entity_path = save_entities(
    all_entities
)


# ---------------------------------------------------------
# 6. Save relations
# ---------------------------------------------------------

relation_path = save_relations(
    all_relations
)

claim_path = save_claims(
    all_claims
)

# ---------------------------------------------------------
# 7. Summary
# ---------------------------------------------------------

print(
    "\n========== FINAL SUMMARY =========="
)

print(
    f"Total entities: "
    f"{len(all_entities)}"
)

print(
    f"Total relations: "
    f"{len(all_relations)}"
)

print(
    f"\nEntities saved to:\n"
    f"{entity_path}"
)

print(
    f"\nRelations saved to:\n"
    f"{relation_path}"
)

print(
    f"Total claims: "
    f"{len(all_claims)}"
)

print(
    f"\nClaims saved to:\n"
    f"{claim_path}"
)
# ---------------------------------------------------------
# 8. Sample entities
# ---------------------------------------------------------

print(
    "\n========== SAMPLE ENTITIES ==========\n"
)

for entity in all_entities[:30]:

    print(
        f"{entity.text:30}"
        f"{entity.label:25}"
        f"{entity.source_url}"
    )


# ---------------------------------------------------------
# 9. Sample relations
# ---------------------------------------------------------

print(
    "\n========== SAMPLE RELATIONS ==========\n"
)

for relation in all_relations[:30]:

    print(
        f"{relation.subject_text} "
        f"--[{relation.predicate}]--> "
        f"{relation.object_text}"
    )