from collections import deque
from datetime import datetime
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .models import CrawledPage


USER_AGENT = "Graphitti/0.1"


def normalize_url(url: str) -> str:
    """
    Normalize a URL so duplicate links are easier to detect.
    """
    parsed = urlparse(url)

    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    path = parsed.path or "/"

    if path != "/" and path.endswith("/"):
        path = path[:-1]

    return f"{scheme}://{netloc}{path}"


def is_same_domain(base_url: str, candidate_url: str) -> bool:
    """
    Allow crawling only within the same domain.
    """
    base_domain = urlparse(base_url).netloc.lower()
    candidate_domain = urlparse(candidate_url).netloc.lower()

    return base_domain == candidate_domain


def extract_page(url: str, parent_url: str | None, depth: int) -> CrawledPage:
    """
    Download and clean a single web page.
    """
    response = requests.get(
        url,
        timeout=10,
        headers={"User-Agent": USER_AGENT},
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove non-content elements
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    title = soup.title.get_text(strip=True) if soup.title else ""

    content = soup.get_text(
        separator=" ",
        strip=True,
    )

    return CrawledPage(
        url=url,
        title=title,
        content=content,
        parent_url=parent_url,
        depth=depth,
        crawled_at=datetime.utcnow(),
    )


def extract_links(url: str, html: str) -> list[str]:
    """
    Extract absolute links from a page.
    """
    soup = BeautifulSoup(html, "html.parser")

    links = []

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]

        # Ignore fragments, javascript, mailto, etc.
        if href.startswith("#"):
            continue

        if href.startswith(("javascript:", "mailto:", "tel:")):
            continue

        absolute_url = urljoin(url, href)
        normalized = normalize_url(absolute_url)

        parsed = urlparse(normalized)

        if parsed.scheme in {"http", "https"}:
            links.append(normalized)

    return list(dict.fromkeys(links))


def crawl_website(
    start_url: str,
    max_depth: int = 2,
    max_pages: int = 20,
) -> list[CrawledPage]:
    """
    Crawl pages on the same domain using BFS.
    """

    start_url = normalize_url(start_url)

    queue = deque()
    queue.append((start_url, None, 0))

    visited = set()
    pages: list[CrawledPage] = []

    while queue and len(pages) < max_pages:
        current_url, parent_url, depth = queue.popleft()

        if current_url in visited:
            continue

        if depth > max_depth:
            continue

        visited.add(current_url)

        try:
            response = requests.get(
                current_url,
                timeout=10,
                headers={"User-Agent": USER_AGENT},
            )

            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            for tag in soup(["script", "style", "noscript", "svg"]):
                tag.decompose()

            title = soup.title.get_text(strip=True) if soup.title else ""

            content = soup.get_text(
                separator=" ",
                strip=True,
            )

            page = CrawledPage(
    url=current_url,
    title=title,
    content=content,
    html=response.text,
    parent_url=parent_url,
    depth=depth,
    crawled_at=datetime.utcnow(),
)

            pages.append(page)

            print(f"[CRAWLED] depth={depth} url={current_url}")

            # Don't discover more links at max depth.
            if depth == max_depth:
                continue

            # Discover links from original HTML response.
            links = extract_links(
                current_url,
                response.text,
            )

            for link in links:

                if link in visited:
                    continue

                if not is_same_domain(start_url, link):
                    continue

                queue.append(
                    (link, current_url, depth + 1)
                )

        except requests.RequestException as error:
            print(
                f"[ERROR] Could not crawl {current_url}: {error}"
            )

    return pages