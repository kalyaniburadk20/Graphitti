from dataclasses import dataclass
from datetime import datetime


@dataclass
class CrawledPage:
    url: str
    title: str
    content: str
    html: str
    parent_url: str | None
    depth: int
    crawled_at: datetime