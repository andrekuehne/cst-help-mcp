"""Reader for the Library: CST's Macros, Result Templates and Includes, copied into the tree as files
(ADR 0014).

Text files keep their names and folders under ``library/``, re-encoded from cp1252 to UTF-8 with
LF line endings, so agents grep them like any code. Each gets one line in ``library.md``: its kind,
menu path and Display Name, Application Filter, Variants and first comment line, and for an
Include its public procedures, the Helpers. Scrambled Macros are listed but not copied, and never
descrambled. Dialog bitmaps become PNG beside the Macros that load them. Nothing else is copied:
executables, Office files, projects and presets stay out. Nothing from the Library is executed.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from pathlib import Path, PurePosixPath

from PIL import Image

from cst_help_mcp.errors import BuildError
from cst_help_mcp.layout import LibraryLine

SOURCE_FOLDER = "Library"
TREE_FOLDER = "library"
# The Library folders the cst-release Source reads, relative to the Library.
FOLDERS = ("Macros", "Result Templates", "Includes")
_KINDS = {
    ".mcr": "control macro",
    ".mcs": "structure macro",
    ".rtp": "Result Template",
    ".lib": "Include",
    ".bas": "helper script",
    ".cls": "helper script",
    ".txt": "text",  # or a helper script, when it holds procedures
}
_BITMAP = ".bmp"
_SCRAMBLED = re.compile(r'\s*Scrambled "')
_PROCEDURE = re.compile(r"^[ \t]*(?:Public[ \t]+)?(?:Function|Sub)[ \t]+(\w+)", re.MULTILINE | re.IGNORECASE)
_GUARD = "Do not change the line above"
_DESCRIPTION_LENGTH = 160


@dataclass(frozen=True)
class LibraryFile:
    line: LibraryLine
    text: str | None  # None for a scrambled Macro, which is listed but not copied


@dataclass(frozen=True)
class Bitmap:
    source: Path
    locator: str  # the PNG's path in the tree


@dataclass
class Library:
    """What a Source's Library holds for the tree, and what could not be read of it."""

    files: list[LibraryFile] = field(default_factory=list)
    bitmaps: list[Bitmap] = field(default_factory=list)
    failures: list[tuple[str, str]] = field(default_factory=list)  # source path, error
    unsupported: Counter[str] = field(default_factory=Counter)  # files left out, by extension

    @property
    def copied(self) -> list[LibraryFile]:
        return [f for f in self.files if f.text is not None]

    def extend(self, other: Library) -> None:
        self.files.extend(other.files)
        self.bitmaps.extend(other.bitmaps)
        self.failures.extend(other.failures)
        self.unsupported.update(other.unsupported)


def library_locator(source_path: str) -> str:
    """``Library/Macros/A^+MWS.mcr`` → ``library/Macros/A^+MWS.mcr``: copied files keep their names."""
    return f"{TREE_FOLDER}/{source_path.removeprefix(f'{SOURCE_FOLDER}/')}"


def read_library(release: Path, selected: Callable[[str], bool]) -> Library:
    """The Library files of a release folder that ``selected`` takes, by source path."""
    library = Library()
    for folder in FOLDERS:
        if not (release / SOURCE_FOLDER / folder).is_dir():
            raise BuildError(
                f"The structure of {release} is not recognised as a CST release folder: "
                f"it has no '{SOURCE_FOLDER}/{folder}' folder"
            )
    for folder in FOLDERS:
        for path in sorted(p for p in (release / SOURCE_FOLDER / folder).rglob("*") if p.is_file()):
            rel = path.relative_to(release).as_posix()
            if not selected(rel):
                continue
            suffix = path.suffix.lower()
            if suffix == _BITMAP:
                library.bitmaps.append(Bitmap(path, library_locator(rel)[: -len(suffix)] + ".png"))
            elif suffix in _KINDS:
                try:
                    library.files.append(_read_file(path, rel))
                except UnicodeDecodeError as e:
                    library.failures.append((rel, f"{type(e).__name__}: {e}"))
            else:
                library.unsupported[suffix] += 1
    library.files = _with_variants(library.files)
    _check_paths(library)
    return library


def write_library(tree: Path, library: Library) -> list[tuple[str, str]]:
    """Write the copied files and the bitmaps' PNGs into the tree; returns the bitmaps that failed."""
    for file in library.copied:
        assert file.text is not None
        path = tree / file.line.locator
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(file.text.encode("utf-8"))
    failures = []
    for bitmap in library.bitmaps:
        path = tree / bitmap.locator
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with Image.open(bitmap.source) as image:
                image.save(path, "PNG")
        except (OSError, ValueError, Image.DecompressionBombError) as e:
            failures.append((bitmap.source.as_posix(), f"{type(e).__name__}: {e}"))
    return failures


def _read_file(path: Path, rel: str) -> LibraryFile:
    text = path.read_bytes().decode("cp1252").replace("\r\n", "\n")
    scrambled = bool(_SCRAMBLED.match(text))
    kind = _KINDS[path.suffix.lower()]
    if kind == "text" and _PROCEDURE.search(text):
        kind = "helper script"
    if scrambled:
        kind = f"{kind}, scrambled: listed, not copied"
    folders = PurePosixPath(rel).parts[2:-1]  # below Library/<folder>/
    name, _, application_filter = path.stem.partition("^")
    helpers = _helpers(text) if kind == "Include" else []
    line = LibraryLine(
        locator=library_locator(rel),
        kind=kind,
        display_name=" / ".join([*folders, name.strip()]),
        application_filter=application_filter.strip(),
        variants=[],
        description="" if scrambled else _description(text),
        helpers=helpers,
    )
    return LibraryFile(line, None if scrambled else text)


def _helpers(text: str) -> list[str]:
    """An Include's public procedures, in the order it defines them, without its debug entry points
    (``Main2``, ``Main_wcsexample``), which no Library code calls."""
    names = dict.fromkeys(_PROCEDURE.findall(text))
    return [name for name in names if not name.lower().startswith("main")]


def _description(text: str) -> str:
    """The first comment line that says something: not a ``'#`` directive, a rule of dashes, or
    the menu-title guard and the line it guards."""
    lines = text.splitlines()
    for n, line in enumerate(lines):
        body = line.strip()
        if not body.startswith("'"):
            continue
        body = body.lstrip("'").strip()
        guarded = n + 1 < len(lines) and _GUARD in lines[n + 1]
        if body.startswith("#") or _GUARD in body or guarded or not re.search(r"[A-Za-z]", body):
            continue
        return " ".join(body.split())[:_DESCRIPTION_LENGTH]
    return ""


def _with_variants(files: list[LibraryFile]) -> list[LibraryFile]:
    """Files of one folder with the same Display Name and extension are each other's Variants."""
    groups: defaultdict[tuple[str, str, str], list[str]] = defaultdict(list)
    for file in files:
        groups[_variant_key(file)].append(file.line.locator)
    return [
        replace(
            file,
            line=replace(
                file.line,
                variants=[
                    PurePosixPath(o).name for o in groups[_variant_key(file)] if o != file.line.locator
                ],
            ),
        )
        for file in files
    ]


def _variant_key(file: LibraryFile) -> tuple[str, str, str]:
    path = PurePosixPath(file.line.locator)
    return str(path.parent), file.line.display_name.lower(), path.suffix.lower()


def _check_paths(library: Library) -> None:
    """No two files share a path in the tree, compared without regard to case as Windows does."""
    seen: dict[str, str] = {}
    for path in [f.line.locator for f in library.copied] + [b.locator for b in library.bitmaps]:
        if path.lower() in seen:
            raise BuildError(f"Locator collision in the Library: '{seen[path.lower()]}' and '{path}'")
        seen[path.lower()] = path
