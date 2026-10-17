from app.crawler.storage import save_pages
from app.crawler.simple_crawler import crawl_website


pages = crawl_website(
    "https://example.com",
    max_depth=1,
    max_pages=5,
)

path = save_pages(
    pages,
    filename="test_crawl.jsonl",
)

print(f"Saved {len(pages)} pages")
print(f"File: {path}")