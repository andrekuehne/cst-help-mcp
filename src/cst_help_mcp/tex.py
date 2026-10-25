"""TeX on the help pages that load MathJax, found the way MathJax 3 finds it.

Only pages that load MathJax have TeX, and each says in its own configuration which delimiters
it uses, so a literal ``$`` elsewhere (WinWrap's ``Left$``) is never math. MathJax looks for math
in each run of text between two tags, so a formula never spans a tag; a delimiter without its
partner in its run stays text, and is reported.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

from cst_help_mcp.model import UnpairedMath
from cst_help_mcp.navigation import decode_js_string

_LOADER = re.compile(r"<script\b[^>]*\bsrc\s*=\s*[\"'][^\"']*mathjax[^\"']*[\"']", re.IGNORECASE)
_STRING = r"'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\""
_PAIR = re.compile(rf"\[\s*({_STRING})\s*,\s*({_STRING})\s*\]")
_ENVIRONMENT = r"\\begin\{(?P<env>[^}]*)\}"
_ESCAPE = r"(?P<escape>\\\$)"  # a dollar that is text (MathJax's processEscapes, on by default)
# The tags MathJax skips by default.
_SKIPPED_TAGS = frozenset(
    ["script", "noscript", "style", "textarea", "pre", "code", "annotation", "annotation-xml"]
)


@dataclass(frozen=True)
class MathConfig:
    """What a page's MathJax configuration sets; unset options keep MathJax 3's defaults.

    ``ignore_class`` and ``process_class`` are patterns for class names: math is not looked for in
    an element of an ignored class, unless the element or one inside it has a processed class.
    """

    inline: tuple[tuple[str, str], ...] = (("\\(", "\\)"),)
    display: tuple[tuple[str, str], ...] = (("$$", "$$"), ("\\[", "\\]"))
    ignore_class: str = "tex2jax_ignore"
    process_class: str = "tex2jax_process"

    def processes(self, elements: Iterable[tuple[str, str]]) -> bool:
        """Whether MathJax looks for math in text inside these elements, given outermost first as
        tag name and class attribute."""
        ignored = _class_pattern(self.ignore_class)
        processed = _class_pattern(self.process_class)
        ignore = False
        for tag, classes in elements:
            process = bool(processed.search(classes))
            if tag in _SKIPPED_TAGS and not process:
                return False
            ignore = (ignore or bool(ignored.search(classes))) and not process
        return not ignore


def _class_pattern(pattern: str) -> re.Pattern[str]:
    """A class pattern matched against whole class names, as MathJax matches it."""
    return re.compile(f"(?:^| )(?:{pattern})(?: |$)")


@dataclass(frozen=True)
class Math:
    """A formula found in a run of text: inline, or displayed on a line of its own."""

    tex: str  # as written, with an environment's \begin and \end but without other delimiters
    display: bool


def math_config(html: str) -> MathConfig | None:
    """The page's MathJax configuration, or None when the page doesn't load MathJax."""
    if not _LOADER.search(html):
        return None
    default = MathConfig()
    return MathConfig(
        inline=_delimiters(html, "inlineMath", default.inline),
        display=_delimiters(html, "displayMath", default.display),
        ignore_class=_option(html, "ignoreHtmlClass", default.ignore_class),
        process_class=_option(html, "processHtmlClass", default.process_class),
    )


def _delimiters(html: str, name: str, default: tuple[tuple[str, str], ...]) -> tuple[tuple[str, str], ...]:
    pairs = re.search(rf"\b{name}\s*:\s*\[((?:[^\[\]]|\[[^\[\]]*\])*)\]", html)
    if not pairs:
        return default
    return tuple((_js_string(m[1]), _js_string(m[2])) for m in _PAIR.finditer(pairs[1]))


def _option(html: str, name: str, default: str) -> str:
    value = re.search(rf"\b{name}\s*:\s*({_STRING})", html)
    return _js_string(value[1]) if value else default


def _js_string(literal: str) -> str:
    return decode_js_string(literal[1:-1])


def find_math(text: str, config: MathConfig) -> tuple[list[str | Math], list[UnpairedMath]]:
    """One run of text split into text and math, and the delimiters that found no partner."""
    delimiters = sorted(
        [(o, c, False) for o, c in config.inline] + [(o, c, True) for o, c in config.display],
        key=lambda d: -len(d[0]),
    )
    closers = {o: (c, display) for o, c, display in reversed(delimiters)}
    opener = re.compile("|".join([_ESCAPE, _ENVIRONMENT, *(re.escape(o) for o, _, _ in delimiters)]))
    pieces: list[str | Math] = []
    unpaired: list[UnpairedMath] = []
    done = start = 0
    while match := opener.search(text, start):
        if match["escape"]:
            start = match.end()
            continue
        if match["env"] is not None:
            close, display, inner = f"\\end{{{match['env']}}}", True, match.start()
        else:
            (close, display), inner = closers[match[0]], match.end()
        end = _end(text, match.end(), close)
        if end is None:
            unpaired.append(UnpairedMath(match[0], _context(text, match.start())))
            start = match.end()
            continue
        if match.start() > done:
            pieces.append(text[done : match.start()])
        tex = text[inner : end + len(close)] if match["env"] is not None else text[inner:end]
        pieces.append(Math(tex, display))
        done = start = end + len(close)
    if done < len(text):
        pieces.append(text[done:])
    return pieces, unpaired


def _end(text: str, start: int, close: str) -> int | None:
    """Where the closing delimiter starts: outside braces, and not escaped by a backslash."""
    braces = 0
    i = start
    while i < len(text):
        if braces == 0 and text.startswith(close, i):
            return i
        char = text[i]
        if char == "\\":
            i += 2
            continue
        if char == "{":
            braces += 1
        elif char == "}" and braces:
            braces -= 1
        i += 1
    return None


def _context(text: str, at: int) -> str:
    return " ".join(text[max(0, at - 40) : at + 40].split())
