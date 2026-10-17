from dataclasses import dataclass, field


@dataclass
class Section:
    heading: str
    level: int
    content: str


@dataclass
class StructuredDocument:
    url: str
    title: str
    description: str
    sections: list[Section] = field(default_factory=list)
    code_blocks: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)