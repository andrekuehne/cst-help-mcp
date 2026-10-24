"""The Document model (ADR 0007).

Readers parse each Source into Documents of typed blocks. The model is persisted
next to each rendered Markdown file, and both the Markdown and the search records
are rendered from it, never from raw source markup.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

BlockKind = Literal["heading", "paragraph", "list", "code", "table", "api_signature"]


@dataclass
class Block:
    kind: BlockKind
    text: str = ""
    level: int = 0
    items: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    language: str = ""

    def plain_text(self) -> str:
        """The block's text without markup, for indexing."""
        if self.kind == "list":
            return "\n".join(self.items)
        if self.kind == "table":
            return "\n".join(" ".join(row) for row in self.rows)
        return self.text


@dataclass
class Section:
    anchors: list[str]
    heading_path: list[str]
    blocks: list[Block] = field(default_factory=list)

    @property
    def anchor(self) -> str | None:
        return self.anchors[0] if self.anchors else None


@dataclass
class ApiEntry:
    """A documented object or member, identified by its Area plus qualified name."""

    qualified_name: str
    object_name: str | None
    member_name: str | None
    signature: str
    description: str
    anchor: str


@dataclass
class Document:
    kind: str
    release: str
    area: str
    locator: str
    source_path: str
    title: str
    sections: list[Section] = field(default_factory=list)
    api_entries: list[ApiEntry] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Document:
        sections = [
            Section(
                anchors=s["anchors"],
                heading_path=s["heading_path"],
                blocks=[Block(**b) for b in s["blocks"]],
            )
            for s in data["sections"]
        ]
        entries = [ApiEntry(**e) for e in data["api_entries"]]
        fields = {k: v for k, v in data.items() if k not in ("sections", "api_entries")}
        return cls(**fields, sections=sections, api_entries=entries)
