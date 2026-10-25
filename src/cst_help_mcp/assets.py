"""Assets: the images Documents show, read from the release folder when a Collection is built.

Images are deduplicated by content hash. PNG and JPEG files are kept as they are; any other format,
such as BMP, SVG or GIF, is converted to PNG, so every client can display it (an animated GIF keeps
its first frame). An image longer than CLIENT_EDGE pixels on its long edge also gets a copy scaled
to that size, which the server returns instead.

    <tree>/assets/<id>.png|jpg          the Asset
    <tree>/assets/<id>.1568.png|jpg     its copy scaled for clients, where it needs one
    <tree>/assets/assets.json           every Asset's kind, caption, size, sources and Documents
"""

from __future__ import annotations

import hashlib
import io
import re
from dataclasses import asdict
from pathlib import Path, PurePosixPath

import resvg_py
from PIL import Image

from cst_help_mcp import layout
from cst_help_mcp.links import ReleaseFiles, SourceLink
from cst_help_mcp.model import Asset, AssetKind, Document, ImageRef

CLIENT_EDGE = 1568  # the longest edge of an image the server returns
FOLDER = layout.ASSETS_DIR
_ICON_EDGE = 32  # an image no longer than this on either edge is an icon
_ID_LENGTH = 12  # hex digits of the content hash
_EQUATION = re.compile(r"formula|formel|equation|corrformular", re.IGNORECASE)
_KEPT_FORMATS = {"PNG": "png", "JPEG": "jpg"}


def write_assets(
    tree: Path, docs: list[Document], files: ReleaseFiles
) -> tuple[list[Asset], list[SourceLink]]:
    """Write the Asset of every image the Documents show into the tree, and point their images at them.

    Returns the Assets, and the images whose file is missing or unreadable.
    """
    folder = tree / FOLDER
    folder.mkdir(parents=True, exist_ok=True)
    by_path: dict[str, Asset | None] = {}  # each source path's Asset, None where it can't be read
    by_hash: dict[str, Asset] = {}
    missing: list[SourceLink] = []
    for doc in docs:
        for image in doc.images:
            key = image.src.lower()
            if key not in by_path:
                by_path[key] = _asset(folder, image.src, files, by_hash)
            asset = by_path[key]
            if asset is None:
                missing.append(SourceLink(doc.source_path, image.src))
                continue
            if image.src not in asset.sources:
                asset.sources.append(image.src)
            if doc.locator not in asset.documents:
                asset.documents.append(doc.locator)
            if not asset.caption:
                asset.caption = image.alt
    assets = list(by_hash.values())
    for asset in assets:
        if not asset.caption and asset.kind == "icon":
            asset.caption = _icon_name(asset.sources[0])
    for doc in docs:
        for image in doc.images:
            asset = by_path[image.src.lower()]
            if asset is not None:
                _attach_asset(image, asset)
    layout.write_json(tree / layout.ASSETS_INDEX, [asdict(asset) for asset in assets])
    return assets, missing


def _attach_asset(image: ImageRef, asset: Asset) -> None:
    image.asset = asset.id
    image.kind = asset.kind
    image.file = asset.file
    image.caption = asset.caption


def _asset(folder: Path, src: str, files: ReleaseFiles, by_hash: dict[str, Asset]) -> Asset | None:
    """The Asset of an image file, written on first sight of its content; None if it can't be read."""
    path = files.find(src)
    if path is None:
        return None
    data = path.read_bytes()
    asset_id = hashlib.sha256(data).hexdigest()[:_ID_LENGTH]
    if asset_id in by_hash:
        return by_hash[asset_id]
    try:
        asset = _convert(folder, asset_id, src, path, data)
    except (OSError, ValueError, Image.DecompressionBombError):
        return None
    by_hash[asset_id] = asset
    return asset


def _convert(folder: Path, asset_id: str, src: str, path: Path, data: bytes) -> Asset:
    svg = path.suffix.lower() == ".svg"
    if svg:
        data = resvg_py.svg_to_bytes(svg_path=str(path))
    with Image.open(io.BytesIO(data)) as image:
        image.load()
        kept = None if svg else _KEPT_FORMATS.get(image.format or "")
        ext = kept or "png"
        file = f"{FOLDER}/{asset_id}.{ext}"
        if kept:
            (folder.parent / file).write_bytes(data)
        else:
            _save(image, folder.parent / file)
        width, height = image.size
        served, served_size = file, image.size
        if max(width, height) > CLIENT_EDGE:
            scaled = image.copy()
            scaled.thumbnail((CLIENT_EDGE, CLIENT_EDGE), Image.Resampling.LANCZOS)
            served = f"{FOLDER}/{asset_id}.{CLIENT_EDGE}.{ext}"
            _save(scaled, folder.parent / served)
            served_size = scaled.size
    return Asset(asset_id, _kind(src, width, height), "", width, height, file, served, *served_size)


def _save(image: Image.Image, path: Path) -> None:
    if path.suffix == ".jpg":
        image.convert("RGB").save(path, "JPEG", quality=90)
    else:
        if image.mode not in ("1", "L", "LA", "P", "RGB", "RGBA", "I", "I;16"):
            image = image.convert("RGBA")
        image.save(path, "PNG")


def _kind(src: str, width: int, height: int) -> AssetKind:
    """An icon folder's images are icons (``solver_integralequation_16.png`` too); otherwise an
    equation is told by its file's name, so small inline symbols count, and an icon by its size."""
    if "/icon_images/" in f"/{src.lower()}":
        return "icon"
    if _EQUATION.search(PurePosixPath(src).stem):
        return "equation"
    return "icon" if max(width, height) <= _ICON_EDGE else "figure"


def _icon_name(src: str) -> str:
    """``solver_transient_16.png`` → ``solver transient icon``."""
    stem = re.sub(r"_\d+$", "", PurePosixPath(src).stem)
    name = " ".join(re.split(r"[\s_-]+", stem)).strip()
    return f"{name} icon" if name else "icon"
