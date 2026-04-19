"""Gallery JS Skill loader — parses SKILL.md files and builds a registry.

Mirrors the CartridgeRegistry pattern: scan a directory of Gallery-format
skill folders, parse YAML frontmatter from SKILL.md, and expose a typed
registry for discovery and lookup.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    import yaml
except ImportError:
    yaml = None


@dataclass
class SkillDefinition:
    """A parsed Gallery JS skill."""
    name: str
    description: str
    instructions: str                  # markdown body after frontmatter
    require_secret: bool = False
    require_secret_description: str = ""
    homepage: str = ""
    skill_dir: str = ""                # absolute path to skill directory
    script_path: str = ""              # path to index.html (or index.js)
    js_path: str = ""                  # path to index.js (for Node.js runner)
    runtime: str = "node"              # "node" (default) or "browser" (needs Playwright)


def _parse_skill_md(content: str) -> tuple[dict, str]:
    """Split SKILL.md into YAML frontmatter dict and markdown body."""
    match = re.match(r"^---\n(.*?\n)---\n?(.*)", content, re.DOTALL)
    if not match:
        return {}, content
    fm_raw = match.group(1)
    body = match.group(2).strip()
    if yaml is not None:
        fm = yaml.safe_load(fm_raw) or {}
    else:
        # Minimal fallback: extract name and description via regex
        fm = {}
        for key in ("name", "description"):
            m = re.search(rf"^{key}:\s*(.+)$", fm_raw, re.MULTILINE)
            if m:
                fm[key] = m.group(1).strip()
    return fm, body


def load_skill(skill_dir: str | Path) -> Optional[SkillDefinition]:
    """Load a single Gallery skill from its directory."""
    skill_dir = Path(skill_dir).resolve()
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return None

    content = skill_md.read_text(encoding="utf-8")
    fm, body = _parse_skill_md(content)
    metadata = fm.get("metadata", {}) or {}

    # Resolve script paths
    scripts_dir = skill_dir / "scripts"
    script_path = ""
    js_path = ""
    if scripts_dir.exists():
        index_html = scripts_dir / "index.html"
        index_js = scripts_dir / "index.js"
        if index_html.exists():
            script_path = str(index_html)
        if index_js.exists():
            js_path = str(index_js)
        elif index_html.exists():
            # Some skills inline JS in index.html — runner.js handles this
            js_path = str(index_html)

    return SkillDefinition(
        name=fm.get("name", skill_dir.name),
        description=fm.get("description", ""),
        instructions=body,
        require_secret=bool(metadata.get("require-secret", False)),
        require_secret_description=metadata.get("require-secret-description", ""),
        homepage=metadata.get("homepage", ""),
        skill_dir=str(skill_dir),
        script_path=script_path,
        js_path=js_path,
        runtime=metadata.get("runtime", "node"),
    )


class SkillRegistry:
    """Registry of Gallery JS skills, scanned from one or more directories.

    Usage:
        registry = SkillRegistry("../gallery/skills/built-in",
                                 "../gallery/skills/featured")
        for skill in registry.list():
            print(skill.name, skill.description)

        defn = registry.get("calculate-hash")
    """

    def __init__(self, *skill_dirs: str | Path):
        self._skills: dict[str, SkillDefinition] = {}
        for d in skill_dirs:
            self._scan(Path(d))

    def _scan(self, root: Path) -> None:
        if not root.exists():
            return
        for entry in sorted(root.iterdir()):
            if not entry.is_dir():
                continue
            skill = load_skill(entry)
            if skill is not None:
                self._skills[skill.name] = skill

    def list(self) -> list[SkillDefinition]:
        return list(self._skills.values())

    def names(self) -> list[str]:
        return list(self._skills.keys())

    def get(self, name: str) -> Optional[SkillDefinition]:
        return self._skills.get(name)

    def has(self, name: str) -> bool:
        return name in self._skills

    def descriptions(self) -> str:
        """One-line-per-skill summary for LLM context injection."""
        lines = []
        for s in self._skills.values():
            secret_tag = " [requires API key]" if s.require_secret else ""
            lines.append(f"- **{s.name}**: {s.description}{secret_tag}")
        return "\n".join(lines)

    def __len__(self) -> int:
        return len(self._skills)

    def __repr__(self) -> str:
        return f"SkillRegistry({len(self._skills)} skills: {', '.join(self.names())})"


if __name__ == "__main__":
    import sys
    dirs = sys.argv[1:] or [
        str(Path(__file__).resolve().parent.parent.parent.parent / "gallery" / "skills" / "built-in"),
        str(Path(__file__).resolve().parent.parent.parent.parent / "gallery" / "skills" / "featured"),
    ]
    registry = SkillRegistry(*dirs)
    print(registry)
    print()
    print(registry.descriptions())
