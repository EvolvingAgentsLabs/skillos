"""Parse forge-tier responses into candidate directory trees.

The forge prompt templates instruct Claude to emit files as
``====FILE <relative/path>====`` headers followed by body text.  This
module parses that format, validates the paths (no ``..`` escape, no
absolute paths), and writes the bundle into
``projects/[P]/forge/candidates/<job_id>/``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


_HEADER_RE = re.compile(r"^====FILE\s+(?P<path>.+?)\s*====\s*$", re.MULTILINE)


class ArtifactError(ValueError):
    """Raised when a candidate bundle violates structural rules."""


@dataclass
class ParsedFile:
    path: str          # relative path as emitted by the model
    content: str       # raw body (no trailing newline normalization)


@dataclass
class ParsedBundle:
    files: list[ParsedFile] = field(default_factory=list)
    leading_text: str = ""  # anything before the first ====FILE==== (for debugging)

    def by_name(self, name: str) -> ParsedFile | None:
        for f in self.files:
            if f.path == name:
                return f
        return None


def parse_bundle(text: str) -> ParsedBundle:
    """Parse a model response into a bundle of files.

    The first block of text before any ``====FILE==== `` header is preserved
    as ``leading_text`` — normally empty, but useful for debugging when a
    model ignores the instruction.
    """
    matches = list(_HEADER_RE.finditer(text))
    if not matches:
        return ParsedBundle(leading_text=text)

    bundle = ParsedBundle(leading_text=text[: matches[0].start()].strip())
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end]
        # Remove up to one leading blank line for readability; leave content
        # otherwise unmodified so byte-exact comparisons are possible.
        if body.startswith("\n"):
            body = body[1:]
        bundle.files.append(ParsedFile(path=m.group("path").strip(), content=body))
    return bundle


# --- validation ------------------------------------------------------

def _validate_relative(path: str) -> None:
    if not path:
        raise ArtifactError("empty path in ====FILE==== header")
    p = Path(path)
    if p.is_absolute():
        raise ArtifactError(f"absolute path not allowed: {path}")
    if ".." in p.parts:
        raise ArtifactError(f"parent-escape not allowed: {path}")


def _require_any(bundle: ParsedBundle, names: Iterable[str]) -> None:
    present = {f.path for f in bundle.files}
    if not any(n in present for n in names):
        raise ArtifactError(
            f"bundle missing required file (one of {list(names)})"
        )


def validate_bundle(bundle: ParsedBundle, *, kind: str | None = None) -> None:
    """Structural validation.  ``kind`` narrows the required files:

    * ``markdown-skill`` — manifest.md + skill.md + tests/cases.yaml
    * ``js-skill``       — manifest.md + skill.js + tests/cases.yaml
    * ``cartridge``      — cartridge.yaml + at least one agents/*.md
    * ``None``           — only path-safety checks (use when kind is
      reported by the model in forge_meta.yaml)
    """
    if not bundle.files:
        raise ArtifactError("empty bundle — no ====FILE==== blocks found")
    seen: set[str] = set()
    for f in bundle.files:
        _validate_relative(f.path)
        if f.path in seen:
            raise ArtifactError(f"duplicate file in bundle: {f.path}")
        seen.add(f.path)

    if kind == "markdown-skill":
        _require_any(bundle, ["manifest.md"])
        _require_any(bundle, ["skill.md"])
        _require_any(bundle, ["tests/cases.yaml"])
    elif kind == "js-skill":
        _require_any(bundle, ["manifest.md"])
        _require_any(bundle, ["skill.js"])
        _require_any(bundle, ["tests/cases.yaml"])
    elif kind == "cartridge":
        _require_any(bundle, ["cartridge.yaml"])


# --- materialization -------------------------------------------------

def write_bundle(bundle: ParsedBundle, destination: Path) -> list[Path]:
    """Write the bundle to ``destination/<path>`` for each file.

    Returns the list of absolute paths written.  Creates parent
    directories as needed.  Overwrites existing files — callers that
    need versioning should write into a fresh directory (the job_id
    subdirectory) and archive the old one.
    """
    destination.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for f in bundle.files:
        _validate_relative(f.path)
        target = destination / f.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f.content, encoding="utf-8")
        written.append(target.resolve())
    return written


def materialize(response_text: str, *,
                destination: Path,
                kind: str | None = None) -> list[Path]:
    """Convenience one-shot: parse → validate → write.

    Used by the ``forge`` runtime after a Claude bridge call returns.
    """
    bundle = parse_bundle(response_text)
    validate_bundle(bundle, kind=kind)
    return write_bundle(bundle, destination)
