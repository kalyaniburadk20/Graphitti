from app.crawler.simple_crawler import crawl_page


page = crawl_page(
    "https://example.com"
)

print("URL:", page.url)
print("TITLE:", page.title)
print("CONTENT:", page.content[:500])