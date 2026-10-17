from app.crawler.simple_crawler import crawl_website
from app.extraction.content_extractor import extract_content
from app.extraction.storage import save_structured_documents


pages = crawl_website(
    "https://fastapi.tiangolo.com/",
    max_depth=0,
    max_pages=1,
)

documents = []

for page in pages:

    document = extract_content(
        html=page.html,
        url=page.url,
    )

    documents.append(document)


path = save_structured_documents(
    documents
)

print(
    f"\nStructured documents: {len(documents)}"
)

print(
    f"Saved to: {path}"
)