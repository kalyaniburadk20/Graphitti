import json
from pathlib import Path

from .models import CrawledPage


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def save_pages(
    pages: list[CrawledPage],
    filename: str = "crawl_pages.jsonl",
) -> Path:
    """
    Save crawled pages as JSON Lines.
    Each line represents one page.
    """

    RAW_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = RAW_DATA_DIR / filename

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:

        for page in pages:
            record = {
                "url": page.url,
                "title": page.title,
                "content": page.content,
                "parent_url": page.parent_url,
                "depth": page.depth,
                "crawled_at": page.crawled_at.isoformat(),
            }

            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )

    return output_path