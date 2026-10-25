"""Reader for the Library: CST's Macros, Result Templates, Includes and Python apps, copied into the
tree as files (ADR 0014).

Text files keep their names and folders under ``library/``, re-encoded from cp1252 to UTF-8 with
LF line endings, so agents grep them like any code. Each gets one line in ``library.md``: its kind,
menu path and Display Name, Application Filter, Variants and first comment line, and for an
Include its public procedures, the Helpers. Scrambled Macros are listed but not copied, and never
descrambled. Dialog bitmaps become PNG beside the Macros that load them.

Of ``Python/``, only the Python apps are copied: each app's descriptor, its entry module, and the
modules that drive CST: they import the ``cst`` package, call VBA objects or hold VBA in a string
literal. The rest of the ``cstapps``
framework and the wheels stay out; the modules left out are reported. Nothing else is copied:
executables, Office files, projects and presets stay out. Nothing from the Library is executed.
"""

from __future__ import annotations

import ast
import json
import re
import warnings
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
# The Python apps' folder, which a release folder may lack, and the package root inside it.
PYTHON_FOLDER = "Python"
_PYTHON_ROOT = "lib"
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
# A line of VBA in a Python string literal: the With blocks that add_to_history and
# execute_vba_code are sent, and the procedures some of them define.
_VBA_LINE = re.compile(r"^[ \t]*(?:With[ \t]+\w|End[ \t]+(?:With|Sub|Function)\b)", re.MULTILINE)
# A VBA object's name or member, as Python code calls it on a CST object: cmds.Block.Reset().
_VBA_NAME = re.compile(r"[A-Z]\w*$")


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
    python_left_out: list[str] = field(default_factory=list)  # modules not copied, by source path

    @property
    def copied(self) -> list[LibraryFile]:
        return [f for f in self.files if f.text is not None]

    def extend(self, other: Library) -> None:
        self.files.extend(other.files)
        self.bitmaps.extend(other.bitmaps)
        self.failures.extend(other.failures)
        self.unsupported.update(other.unsupported)
        self.python_left_out.extend(other.python_left_out)


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
    if (release / SOURCE_FOLDER / PYTHON_FOLDER).is_dir():
        library.extend(_read_python(release, selected))
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


@dataclass(frozen=True)
class _Module:
    rel: str  # its source path
    path: str  # its path below Python/lib, as library.md names it
    text: str
    tree: ast.Module
    package: str  # the package its relative imports start from


@dataclass(frozen=True)
class _App:
    rel: str  # its descriptor's source path
    text: str  # the descriptor
    menu_path: str  # "EDA / Multilayer PCB Setup"
    module: str  # the entry module's dotted name
    restricted_to: str  # the product the descriptor restricts it to, such as "PCBS", or ""


def _read_python(release: Path, selected: Callable[[str], bool]) -> Library:
    """The Python apps: their descriptors, entry modules and the modules that drive CST."""
    library = Library()
    root = release / SOURCE_FOLDER / PYTHON_FOLDER / _PYTHON_ROOT
    modules: dict[str, _Module] = {}
    apps: list[_App] = []
    for path in sorted(p for p in (release / SOURCE_FOLDER / PYTHON_FOLDER).rglob("*") if p.is_file()):
        rel = path.relative_to(release).as_posix()
        if not selected(rel):
            continue
        suffix = path.suffix.lower()
        if not path.is_relative_to(root) or suffix not in (".py", ".json"):
            library.unsupported[suffix] += 1
            continue
        try:
            text = path.read_bytes().decode("utf-8-sig").replace("\r\n", "\n")
            if suffix == ".py":
                name, module = _module(path, root, rel, text)
                modules[name] = module
            elif app := _app(rel, text):
                apps.append(app)
            else:
                library.unsupported[suffix] += 1
        except (UnicodeDecodeError, SyntaxError, ValueError) as e:
            library.failures.append((rel, f"{type(e).__name__}: {e}"))
    entries = {app.module for app in apps}
    copied = {name for name, m in modules.items() if name in entries or _drives_cst(m.tree)}
    for app in apps:
        entry = modules.get(app.module)
        used = sorted(modules[name].path for name in _reachable(app.module, modules) if name in copied)
        line = LibraryLine(
            locator=library_locator(app.rel),
            kind="Python app",
            display_name=app.menu_path,
            application_filter="",
            variants=[],
            description=_docstring(entry.tree) if entry else "",
            helpers=[],
            modules=([entry.path] if entry else []) + used,
            restricted_to=app.restricted_to,
        )
        library.files.append(LibraryFile(line, app.text))
    for name, module in sorted(modules.items()):
        if name not in copied:
            library.python_left_out.append(module.rel)
            continue
        line = LibraryLine(
            locator=library_locator(module.rel),
            kind="Python module",
            display_name=name,
            application_filter="",
            variants=[],
            description=_docstring(module.tree),
            helpers=[],
        )
        library.files.append(LibraryFile(line, module.text))
    return library


def _module(path: Path, root: Path, rel: str, text: str) -> tuple[str, _Module]:
    """A Python module's dotted name and its parsed source."""
    parts = path.relative_to(root).with_suffix("").parts
    package = ".".join(parts[:-1])
    if parts[-1] == "__init__":
        parts = parts[:-1]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)  # invalid escapes in non-raw strings
        tree = ast.parse(text, filename=rel)
    return ".".join(parts), _Module(rel, path.relative_to(root).as_posix(), text, tree, package)


def _app(rel: str, text: str) -> _App | None:
    """A Python app's descriptor: its menu path and the module ``-m`` runs; None for other JSON."""
    descriptor = json.loads(text)
    if not isinstance(descriptor, dict) or not isinstance(descriptor.get("name"), str):
        return None
    args = descriptor.get("args")
    if not isinstance(args, list) or "-m" not in args[:-1]:
        return None
    module = str(args[args.index("-m") + 1])
    menu_path = " / ".join(part.strip() for part in descriptor["name"].split("/"))
    return _App(rel, text, menu_path, module, str(descriptor.get("restrict_to", "")))


def _drives_cst(tree: ast.Module) -> bool:
    """Whether a module imports the ``cst`` package, calls a VBA object's member on a CST object
    (``cmds.Block.Reset()``), or holds VBA in a string literal."""
    for node in ast.walk(tree):
        if _calls_vba_object(node):
            return True
        if isinstance(node, ast.Import) and any(a.name.split(".")[0] == "cst" for a in node.names):
            return True
        if isinstance(node, ast.ImportFrom) and not node.level and (node.module or "").split(".")[0] == "cst":
            return True
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and _VBA_LINE.search(node.value):
            return True
    return False


def _calls_vba_object(node: ast.AST) -> bool:
    """``x.Object.Member(…)``: a member of a VBA object, on a CST object held in a variable."""
    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
        return False
    owner = node.func.value
    return (
        bool(_VBA_NAME.match(node.func.attr))
        and isinstance(owner, ast.Attribute)
        and bool(_VBA_NAME.match(owner.attr))
        and isinstance(owner.value, ast.Name)
        and owner.value.id[:1].islower()
    )


def _reachable(start: str, modules: dict[str, _Module]) -> list[str]:
    """The modules that ``start`` imports, directly or through others."""
    seen = {start}
    todo = [start]
    while todo:
        module = modules.get(todo.pop())
        if module is None:
            continue
        for name in _imports(module):
            if name in modules and name not in seen:
                seen.add(name)
                todo.append(name)
    return sorted(seen - {start})


def _imports(module: _Module) -> set[str]:
    """The dotted names a module imports anywhere in it, relative imports resolved. A name imported
    from a package may be a submodule, so both the package and the name are given."""
    names: set[str] = set()
    for node in ast.walk(module.tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                package = module.package.split(".")
                package = package[: len(package) - node.level + 1]
                base = ".".join([*package, *([node.module] if node.module else [])])
            names.add(base)
            names.update(f"{base}.{a.name}" for a in node.names)
    return names


def _docstring(tree: ast.Module) -> str:
    """The first line of a module's docstring that says something."""
    for line in (ast.get_docstring(tree) or "").splitlines():
        if re.search(r"[A-Za-z]", line):
            return " ".join(line.split())[:_DESCRIPTION_LENGTH]
    return ""


def _check_paths(library: Library) -> None:
    """No two files share a path in the tree, compared without regard to case as Windows does."""
    seen: dict[str, str] = {}
    for path in [f.line.locator for f in library.copied] + [b.locator for b in library.bitmaps]:
        if path.lower() in seen:
            raise BuildError(f"Locator collision in the Library: '{seen[path.lower()]}' and '{path}'")
        seen[path.lower()] = path
