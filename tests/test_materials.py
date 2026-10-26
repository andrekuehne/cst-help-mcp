"""Build the Library's Material Definitions from the real corpus, then read the files the build wrote
(the build-then-read seam)."""

from __future__ import annotations

import re
from pathlib import Path

from kb_helpers import ProseBuild

MATERIALS = "library/Materials"


def test_every_material_definition_is_copied_in_both_file_formats(
    library_build: ProseBuild, corpus_2024: Path
) -> None:
    sources = sorted((corpus_2024 / "Library" / "Materials").glob("*.mtd"), key=lambda p: p.name)
    copied = library_build.tree / MATERIALS

    assert len(sources) == 779
    assert sorted(p.name for p in copied.iterdir()) == [p.name for p in sources]
    older = (copied / "Rogers RO4350B (lossy).mtd").read_bytes()
    newer = (copied / "Air (CHT).mtd").read_bytes()
    assert b'.SetMaterialUnit "' in older
    assert b'.MaterialUnit "Frequency"' in newer
    for name in ("Rogers RO4350B (lossy).mtd", "Air (CHT).mtd"):
        source = (corpus_2024 / "Library" / "Materials" / name).read_bytes()
        assert (copied / name).read_bytes() == source.replace(b"\r\n", b"\n")


def _materials_md(build: ProseBuild) -> list[str]:
    return (build.tree / "materials.md").read_text(encoding="utf-8").splitlines()


def _line(build: ProseBuild, name: str) -> str:
    return next(line for line in _materials_md(build) if line.startswith(f"| `{MATERIALS}/{name}.mtd` |"))


def test_materials_md_gives_each_exact_name_and_its_base_name_after_a_vendor_prefix_or_loss_qualifier(
    library_build: ProseBuild,
) -> None:
    lines = _materials_md(library_build)

    assert "| Path | Name | Base name | Variants | Same definition as | Description |" in lines
    assert _line(library_build, "Rogers RO4350B (lossy)").startswith(
        f"| `{MATERIALS}/Rogers RO4350B (lossy).mtd` | Rogers RO4350B (lossy) | RO4350B | "
    )
    assert _line(library_build, "FR-4 (loss free)").startswith(
        f"| `{MATERIALS}/FR-4 (loss free).mtd` | FR-4 (loss free) | FR-4 | "
    )
    # A name with neither keeps its base name cell empty, and other qualifiers stay in it.
    assert _line(library_build, "Air").startswith(f"| `{MATERIALS}/Air.mtd` | Air |  | ")
    assert "| Air (CHT) |  | " in _line(library_build, "Air (CHT)")
    assert "| ECCOSORB AN-72 (back) | AN-72 (back) | " in _line(library_build, "ECCOSORB AN-72 (back)")
    rows = [line for line in lines if line.startswith(f"| `{MATERIALS}/")]
    assert len(rows) == 779
    assert {line for line in rows if re.search("ro4350b", line, re.IGNORECASE)} == {
        _line(library_build, f"Rogers RO4350B{lopro} ({loss})")
        for lopro in ("", " LoPro")
        for loss in ("lossy", "loss free")
    }
    assert {line for line in rows if re.search("fr-?4", line, re.IGNORECASE)} >= {
        _line(library_build, f"FR-4 ({qualifier})")
        for qualifier in ("lossy", "loss free", "lossy - thermal anisotropic")
    }


def test_variants_differ_only_in_their_loss_qualifier(library_build: ProseBuild) -> None:
    line = _line(library_build, "FR-4 (lossy)")

    variants = line.split(" | ")[3]
    assert variants == "`FR-4 (loss free).mtd`, `FR-4 (lossy - thermal anisotropic).mtd`"
    assert "| `Rogers RO4350B (loss free).mtd` |" in _line(library_build, "Rogers RO4350B (lossy)")
    assert "LoPro" not in _line(library_build, "Rogers RO4350B (lossy)").split(" | ")[3]
    cem3 = "Panasonic CEM-3 Laminate R-1786 Thickness(800um) Cloth style(7628)"
    assert f"`{cem3} (loss free).mtd`" in _line(library_build, cem3).split(" | ")[3]
    assert _line(library_build, "Air").split(" | ")[3] == ""


def test_byte_identical_files_are_both_listed_and_linked_as_the_same_definition(
    library_build: ProseBuild,
) -> None:
    rogers = _line(library_build, "Rogers RO3003 (loss free)")
    taconic = _line(library_build, "Taconic NF-30 (loss free)")

    assert f"| [Taconic NF-30 (loss free)](<{MATERIALS}/Taconic NF-30 (loss free).mtd>) |" in rogers
    assert f"| [Rogers RO3003 (loss free)](<{MATERIALS}/Rogers RO3003 (loss free).mtd>) |" in taconic
    assert _line(library_build, "Air").split(" | ")[4] == ""
    rows = [line for line in _materials_md(library_build) if line.startswith(f"| `{MATERIALS}/")]
    linked = [line for line in rows if line.split(" | ")[4]]
    assert len(linked) == 148  # 74 byte-identical pairs


def test_agents_md_says_the_name_cst_expects_is_the_file_name_and_cht_fluids_are_not_hf_materials(
    library_build: ProseBuild,
) -> None:
    agents = (library_build.tree / "AGENTS.md").read_text(encoding="utf-8")

    assert "- `materials.md`: every Material Definition on one line" in agents
    assert "Material Definitions" in next(
        line for line in agents.splitlines() if line.startswith("| `library/`")
    )
    recipe = " ".join(agents.partition("**A material**")[2].partition("\n\n")[0].split())
    assert "The name CST expects is the file name without `.mtd`, exactly" in recipe
    assert "`(CHT)` materials are fluids for conjugate heat transfer, not high-frequency materials" in recipe
