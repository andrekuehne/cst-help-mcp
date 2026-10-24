"""A Locator collision stops the build. Synthetic fixture: imitates structure only (ADR 0001)."""

from __future__ import annotations

from pathlib import Path

import pytest
from kb_helpers import write_config

from cst_help_mcp.build import build_collection
from cst_help_mcp.errors import BuildError

TOPIC = """<?xml version="1.0" encoding="utf-8"?>
<html><head><title>Widget Object</title>
<script type="text/javascript" src="../whtopic.js"></script></head>
<body>
<p class="VBA-Heading-Object">Widget Object</p>
<p class="VBA-Heading-Method">Spin ( int turns )</p>
<p class="VBA-Text-Indent">Spins the widget.</p>
</body></html>
"""


def test_two_sources_with_the_same_locator_stop_the_build(tmp_path: Path) -> None:
    project = tmp_path / "release" / "Online Help" / "mergedProjects" / "VBA_3D" / "widgets"
    project.mkdir(parents=True)
    (project / "Widget Object.htm").write_text(TOPIC, encoding="utf-8")
    (project / "widget-object.htm").write_text(TOPIC, encoding="utf-8")
    config = write_config(tmp_path / "cst-help.toml", tmp_path / "kb", tmp_path / "release", [])

    with pytest.raises(BuildError) as error:
        build_collection(config, "cst-2024")

    message = str(error.value)
    assert "Locator collision" in message
    assert "Widget Object.htm" in message
    assert "widget-object.htm" in message
    assert "vba_3d/widgets/widget-object.htm.md" in message
    assert not (tmp_path / "kb" / "cst-2024").exists()
