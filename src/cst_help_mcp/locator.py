"""The Locator rule (ADR 0011) and anchor generation."""

from __future__ import annotations

import re

_DROPPED_PREFIXES = ("online help", "mergedprojects")
_OUTSIDE_ALPHABET = re.compile(r"[^a-z0-9._+^-]+")
_OUTSIDE_ANCHOR_ALPHABET = re.compile(r"[^a-z0-9_-]+")
# Source ids are kept as anchors only when they are usable as link fragments.
_SOURCE_ID = re.compile(r"[A-Za-z][A-Za-z0-9_.:-]*")


def locator_for(source_path: str) -> str:
    """Map a source path, relative to its release folder, to its Locator.

    Drops the ``Online Help/`` and ``mergedProjects/`` prefixes, lowercases every
    segment, collapses each run of characters outside ``a-z 0-9 . _ - + ^`` to one
    ``-``, trims ``-`` at segment ends, and appends ``.md`` to the full file name.
    """
    segments = [s for s in re.split(r"[\\/]", source_path) if s]
    while segments and segments[0].lower() in _DROPPED_PREFIXES:
        segments = segments[1:]
    cleaned = [_OUTSIDE_ALPHABET.sub("-", s.lower()).strip("-") for s in segments]
    return "/".join(cleaned) + ".md"


def anchor_for(name: str) -> str:
    """Generate an anchor from a member, procedure or heading name."""
    return _OUTSIDE_ANCHOR_ALPHABET.sub("-", name.lower()).strip("-")


def document_part(locator: str) -> str:
    """A Locator without its anchor: the Locator of its Document."""
    return locator.partition("#")[0]


def is_usable_source_id(source_id: str) -> bool:
    """Whether a source's own id or name is kept as an anchor: it must be usable as a link fragment."""
    return _SOURCE_ID.fullmatch(source_id) is not None


def page_anchor(page: int) -> str:
    """The anchor of a PDF's physical page."""
    return f"page-{page}"
