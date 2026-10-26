"""Build the Library from the real corpus, then read the files it wrote (the build-then-read seam)."""

from __future__ import annotations

from pathlib import Path

from kb_helpers import ProseBuild

PDA = "Macros/Results/Eye Diagram, TDR, etc/PDA (Peak Distortion Analysis)^+DS.mcr"


def test_a_macro_is_copied_with_its_name_and_folders_and_re_encoded_to_utf_8(
    library_build: ProseBuild, corpus_2024: Path
) -> None:
    source = (corpus_2024 / "Library" / PDA).read_bytes()

    copied = (library_build.tree / "library" / PDA).read_bytes()

    assert b"\xb0" in source  # a degree sign in cp1252
    assert copied == source.decode("cp1252").replace("\r\n", "\n").encode("utf-8")
    assert "\N{DEGREE SIGN}".encode() in copied


def test_only_the_text_files_and_the_dialog_bitmaps_are_copied(library_build: ProseBuild) -> None:
    library = library_build.tree / "library"

    suffixes = {p.suffix.lower() for p in library.rglob("*") if p.is_file()}

    assert suffixes == {
        ".mcr",
        ".mcs",
        ".rtp",
        ".bas",
        ".cls",
        ".txt",
        ".lib",
        ".png",
        ".py",
        ".json",
        ".mtd",
    }
    assert sorted(p.name for p in library.iterdir()) == [
        "Includes",
        "Macros",
        "Materials",
        "Python",
        "Result Templates",
    ]
    assert library_build.report["unsupported"][".exe"] == 1
    assert library_build.report["unsupported"][".ppt"] == 7


def test_a_scrambled_macro_is_listed_in_library_md_but_not_copied(library_build: ProseBuild) -> None:
    wizard = "library/Macros/Wizard/5G Post-Processing Wizard^+MWS.mcr"

    library_md = (library_build.tree / "library.md").read_text(encoding="utf-8")

    assert not (library_build.tree / wizard).exists()
    line = next(line for line in library_md.splitlines() if f"`{wizard}`" in line)
    assert (
        "| control macro, scrambled: listed, not copied | Wizard / 5G Post-Processing Wizard | +MWS |" in line
    )
    assert library_build.report["counts"]["skipped"] == 5


def _line(build: ProseBuild, path: str) -> str:
    library_md = (build.tree / "library.md").read_text(encoding="utf-8")
    return next(line for line in library_md.splitlines() if line.startswith(f"| `{path}` |"))


def test_library_md_gives_a_result_templates_kind_menu_path_filter_and_first_comment(
    library_build: ProseBuild,
) -> None:
    line = _line(
        library_build, "library/Result Templates/Farfield and Antenna Properties/Farfield Result^+MWS+DS.rtp"
    )

    assert line.endswith(
        "| Result Template | Farfield and Antenna Properties / Farfield Result | +MWS+DS |  "
        "| Post Processing Template: Farfield Computation |"
    )


def test_library_md_links_variants_that_differ_only_in_their_application_filter(
    library_build: ProseBuild,
) -> None:
    line = _line(library_build, "library/Result Templates/S-Parameters/Y Parameter^+DS.rtp")

    assert "| S-Parameters / Y Parameter | +DS | `Y Parameter^+MWS.rtp` |" in line


def test_library_md_names_the_helpers_of_an_include_found_by_grep_in_it(library_build: ProseBuild) -> None:
    include = "library/Includes/template_conversions.lib"

    line = _line(library_build, include)

    assert line.startswith(f"| `{include}` | Include | template_conversions | ")
    assert ", GetLastResult_LIB, " in line
    assert "This library provides function in particular for the result template" in line
    assert "Main_wcsexample" not in _line(library_build, "library/Includes/coordinate_systems.lib")
    code = (library_build.tree / include).read_text(encoding="utf-8")
    assert "\nFunction GetLastResult_LIB(ByVal sResultName As String," in code


def test_a_dialog_bitmap_becomes_a_png_beside_the_macro_that_loads_it(library_build: ProseBuild) -> None:
    calculate = library_build.tree / "library" / "Macros" / "Calculate"

    png = calculate / "Calculate analytical Line Impedance_coax.png"

    assert png.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert not list(calculate.glob("*.bmp"))
    assert (calculate / "Calculate analytical Line Impedance^-EMS-DS.mcr").is_file()


def test_agents_md_names_the_library_and_its_recipes(library_build: ProseBuild) -> None:
    agents = (library_build.tree / "AGENTS.md").read_text(encoding="utf-8")

    copied = library_build.report["counts"]["converted"]
    assert f"| `library/` | {copied:,} | CST's Library" in agents
    assert "- `library.md`: every Library file on one line" in agents
    recipe = " ".join(agents.partition("**Working code**")[2].partition("\n\n")[0].split())
    assert "grep `library/`" in recipe
    assert '`\'#include "X"` is the file `library/Includes/X`' in recipe
    assert "a Helper, not a documented CST API Entry" in recipe
    assert "`.png`" in recipe
    rules = agents.partition("## Rules")[2].partition("\n## ")[0]
    assert "uses but no page documents is an Undocumented Member" in rules


def test_library_files_are_counted_as_converted_documents_and_never_as_aliases(
    library_build: ProseBuild,
) -> None:
    counts = library_build.report["counts"]

    copied = sum(
        1 for p in (library_build.tree / "library").rglob("*") if p.suffix.lower() != ".png" and p.is_file()
    )
    assert counts["converted"] == copied
    assert counts["aliases"] == 0


APPS = "library/Python/lib/cstapps/apps"


def test_library_md_lists_each_python_app_by_its_menu_name_with_its_modules(
    library_build: ProseBuild,
) -> None:
    line = _line(library_build, f"{APPS}/pleos.json")

    assert line.startswith(
        f"| `{APPS}/pleos.json` | Python app | EDA / Place Lumped Elements on Schematic | "
    )
    modules = line.split(" | ")[4]
    assert modules.startswith("`cstapps/apps/place_lumped_elements_on_schematic.py`, ")
    assert "`cstapps/_impl/eda/place_lumped_elements_on_schematic.py`" in modules
    assert (library_build.tree / APPS / "pleos.json").is_file()
    assert (library_build.tree / APPS / "place_lumped_elements_on_schematic.py").is_file()
    assert "| PCBS |" in _line(library_build, f"{APPS}/demo_pcbs_app.json")


def test_only_python_modules_that_drive_cst_are_copied_and_the_rest_are_reported(
    library_build: ProseBuild,
) -> None:
    python = library_build.tree / "library" / "Python"
    emag = "lib/cstapps/_impl/eda/emag/_impl"

    copied = {p.relative_to(python).as_posix() for p in python.rglob("*.py")}

    assert f"{emag}/vba_snippets.py" in copied  # VBA in string literals, no import of cst
    assert f"{emag}/mws.py" in copied  # import cst.interface
    # Calls the schematic's VBA objects from Python: cmds.Block.Reset()
    assert "lib/cstapps/_impl/circuits/drivers/design_studio/read.py" in copied
    left_out = library_build.report["library_left_out"]
    assert "Library/Python/lib/cstapps/__git_sha__.py" in left_out
    assert "Library/Python/lib/cstapps/_impl/gui/table_widget.py" in left_out
    assert len(copied) + len(left_out) == 82
    assert library_build.report["counts"]["library_left_out"] == len(left_out)
    assert not list(python.rglob("*.whl"))
    assert library_build.report["unsupported"][".whl"] == 14
    assert "End With" in (python / f"{emag}/vba_snippets.py").read_text(encoding="utf-8")


def test_agents_md_says_vba_sent_from_python_is_found_in_the_string_literals(
    library_build: ProseBuild,
) -> None:
    agents = (library_build.tree / "AGENTS.md").read_text(encoding="utf-8")

    recipe = " ".join(agents.partition("**VBA sent from Python**")[2].partition("\n\n")[0].split())
    assert "`add_to_history` or `execute_vba_code`" in recipe
    assert "grep the string literals in `library/Python/`" in recipe
    assert "a Python app's modules" in agents.partition("- `library.md`:")[2].partition("\n")[0]
