from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .document_models import Section, StructuredDocument


def extract_content(
    html: str,
    url: str,
) -> StructuredDocument:
    """
    Convert raw HTML into a structured document.
    """

    soup = BeautifulSoup(html, "html.parser")

    # Remove elements that do not contribute useful page content.
    for tag in soup(
        [
            "script",
            "style",
            "noscript",
            "svg",
            "nav",
            "footer",
            "header",
        ]
    ):
        tag.decompose()

    # Title
    title = ""

    if soup.title:
        title = soup.title.get_text(
            " ",
            strip=True,
        )

    # Meta description
    description = ""

    meta_description = soup.find(
        "meta",
        attrs={"name": "description"},
    )

    if meta_description:
        description = meta_description.get(
            "content",
            "",
        ).strip()

    # Find the main content area when possible.
    main = (
        soup.find("main")
        or soup.find("article")
        or soup.body
        or soup
    )

    sections: list[Section] = []
    current_heading = "Introduction"
    current_level = 0
    current_content: list[str] = []

    def save_current_section():
        text = " ".join(
            part.strip()
            for part in current_content
            if part.strip()
        ).strip()

        if text:
            sections.append(
                Section(
                    heading=current_heading,
                    level=current_level,
                    content=text,
                )
            )

    for element in main.find_all(
        [
            "h1",
            "h2",
            "h3",
            "h4",
            "p",
            "li",
        ]
    ):

        tag_name = element.name

        # Heading
        if tag_name in {
            "h1",
            "h2",
            "h3",
            "h4",
        }:
            save_current_section()

            current_heading = element.get_text(
                " ",
                strip=True,
            )

            current_level = int(
                tag_name[1]
            )

            current_content = []

        # Paragraph/list item
        else:
            text = element.get_text(
                " ",
                strip=True,
            )

            if text:
                current_content.append(text)

    save_current_section()

    # Extract code blocks separately.
    code_blocks = []

    for code in main.find_all(
        ["pre", "code"]
    ):
        text = code.get_text(
            "\n",
            strip=True,
        )

        if text and text not in code_blocks:
            code_blocks.append(text)

    # Extract links.
    links = []

    for anchor in main.find_all(
        "a",
        href=True,
    ):
        absolute_url = urljoin(
            url,
            anchor["href"],
        )

        if absolute_url.startswith(
            ("http://", "https://")
        ):
            links.append(absolute_url)

    # Remove duplicate links while preserving order.
    links = list(dict.fromkeys(links))

    return StructuredDocument(
        url=url,
        title=title,
        description=description,
        sections=sections,
        code_blocks=code_blocks,
        links=links,
    )