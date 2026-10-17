from app.crawler.simple_crawler import crawl_website
from app.extraction.content_extractor import extract_content
from app.nlp.semantic_chunker import SemanticChunker
from app.nlp.chunk_storage import save_chunks


pages = crawl_website(
    "https://fastapi.tiangolo.com/",
    max_depth=0,
    max_pages=1,
)

page = pages[0]

document = extract_content(
    html=page.html,
    url=page.url,
)

chunker = SemanticChunker()

chunks = chunker.chunk_document(
    document
)

print(
    f"\nGenerated {len(chunks)} chunks\n"
)

for chunk in chunks[:10]:

    print("=" * 80)

    print(
        f"ID: {chunk.chunk_id}"
    )

    print(
        f"Section: {chunk.section_heading}"
    )

    print(
        f"Words: {chunk.token_estimate}"
    )

    print(
        f"\n{chunk.text[:500]}\n"
    )

    path = save_chunks(chunks)

print(
    f"\nSaved chunks to: {path}"
)