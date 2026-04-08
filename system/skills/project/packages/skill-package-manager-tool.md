---
name: skill-package-manager
type: tool
version: v1
status: "[REAL] - Production Ready"
description: >
  apt-like package manager for SkillOS. Installs, updates, searches, lists,
  and removes Skills (agents and tools) from configured sources in sources.list.
tools: Bash, Read, Write, Grep, Glob, WebFetch
extends: project/base
---

# SkillPackageManagerTool

**Component Type**: Tool
**Version**: v1
**Status**: [REAL] - Production Ready
**Claude Tool Mapping**: Bash, Read, Write, Grep, Glob, WebFetch

## Purpose

Provides apt-like package management for SkillOS Skills. Reads `system/sources.list` to discover remote and local skill repositories, and supports install, update, search, list, and remove operations. All installed skills are tracked in `system/packages.lock`.

## Configuration

### sources.list Format

```
# <type>  <uri>  <branch/tag>  [component-path]
github  anthropics/skills       main  skills/
github  huggingface/skills      main  skills/
url     https://example.com/skills/my-agent.md
local   /path/to/local/skills/
```

### packages.lock Format

```yaml
schema_version: 1
last_updated: "2026-03-12T14:00:00Z"
installed:
  - name: example-agent
    version: v1.0
    source: "github:anthropics/skills"
    source_path: skills/ExampleAgent.md
    installed_to: system/agents/ExampleAgent.md
    discovery_path: .claude/agents/ExampleAgent.md
    hash: "md5:abc123def456"
    installed_at: "2026-03-12T14:00:00Z"
    updated_at: null
```

## Operations

### 1. skill install `<name>`

Installs a skill from configured sources.

**Execution Logic**:
1. Read `system/sources.list`, skip comments and blank lines
2. For each source, search for a skill matching `<name>`:
   - **github**: `git clone --depth 1 --branch <branch> <repo>` into temp dir, search `<component-path>` for `<name>.md` or files with `name: <name>` in frontmatter
   - **url**: `WebFetch` the URL, check if filename or frontmatter `name` matches
   - **local**: `Glob` the path for matching `.md` files
3. **If not found in configured sources**: Fall back to GitHub-wide search
   - Run `gh search repos "<name>" --limit 5 --json fullName,description,url`
   - For each match, check repo contents for `.md` skill files
   - If a valid skill is found, download it via `gh api repos/{owner}/{repo}/contents/{path} --jq '.content' | base64 -d`
   - Prompt user to confirm installation from unconfigured source
3. Validate the skill file:
   - Must have YAML frontmatter with `name`, `description`, `tools`
   - Must not conflict with an already-installed skill (unless `--force`)
4. Determine installation target:
   - If frontmatter contains `type: agent` or filename ends with `Agent.md` → `system/agents/`
   - If frontmatter contains `type: tool` or filename ends with `Tool.md` → `system/tools/`
   - Otherwise → `components/agents/` (default)
5. Copy skill file to target directory
6. Copy to `.claude/agents/` for discovery (agents only)
7. Append entry to `system/packages.lock`
8. Optionally register in `system/SmartLibrary.md`

**Parameters**:
```yaml
name: string                # Skill name (kebab-case or filename stem)
source: string              # Optional: specific source to install from (e.g., "github:anthropics/skills")
force: boolean              # Default: false. Overwrite existing skill.
register: boolean           # Default: true. Add to SmartLibrary.
```

**Output**:
```yaml
status: "installed" | "already_exists" | "not_found" | "validation_failed"
skill_name: string
installed_to: string
source: string
version: string
```

### 2. skill search `<query>`

Searches all configured sources for skills matching a query, with GitHub-wide fallback.

**Execution Logic**:
1. **Phase 1 — Configured Sources**: Read `system/sources.list`
   - For each source:
     - **github**: Use `gh api repos/{owner}/{repo}/contents/{component-path}` to list files, filter by query in filenames and frontmatter
     - **url**: `WebFetch` and check content
     - **local**: `Glob` + `Grep` for query
2. **Phase 2 — GitHub-Wide Search** (if Phase 1 yields 0 results, or always as supplementary):
   - Use `gh search repos "<query>" --limit 10 --json fullName,description,url` to find repos across all of GitHub matching the query
   - Also try: `gh search repos "<query> skill" --limit 5 --json fullName,description,url` and `gh search repos "<query> agent" --limit 5 --json fullName,description,url`
   - For each matching repo, check if it contains `.md` files with skill-compatible frontmatter (name, description, tools) using `gh api repos/{owner}/{repo}/contents/ --jq '.[].name'`
   - Mark results as `source: "github-search"` to distinguish from configured sources
3. **Phase 3 — GitHub Topic Search** (supplementary):
   - Use `gh api search/repositories?q=topic:skillos+<query>` to find repos tagged with the `skillos` topic
   - Also search for topics: `llmunix-skill`, `claude-skill`, `ai-agent-skill`
4. Deduplicate results, prioritize configured sources over GitHub-wide matches
5. Return matching skill names with source attribution

**Install from GitHub Search Results**:
When a user wants to install a skill found via GitHub-wide search:
- Use `gh api repos/{owner}/{repo}/contents/` to locate the `.md` skill file(s)
- Download via `gh api repos/{owner}/{repo}/contents/{path} --jq '.content' | base64 -d`
- Validate frontmatter, install as usual
- Record `source: "github:{owner}/{repo}"` in packages.lock
- Optionally prompt user to add the repo to `sources.list` for future discovery

**Output**:
```yaml
results:
  - name: string
    description: string
    source: string          # "github:org/repo", "github-search:owner/repo", "local:/path", "url:..."
    repo_url: string        # Full GitHub URL (for github-search results)
    version: string
    installed: boolean      # Whether already installed locally
```

### 3. skill update

Refreshes source indexes and updates installed skills to latest versions.

**Execution Logic**:
1. Read `system/packages.lock` to get installed skills
2. For each installed skill from a remote source:
   - Fetch the latest version from the original source
   - Compare hash with installed version
   - If changed: overwrite local file, update hash and `updated_at` in lock file
   - If unchanged: skip
3. Re-run `setup_agents.sh` to refresh `.claude/agents/`

**Output**:
```yaml
updated: []                 # List of skills that were updated
unchanged: []               # List of skills already at latest
failed: []                  # List of skills that failed to update
```

### 4. skill list

Shows all installed skills with source attribution.

**Execution Logic**:
1. Read `system/packages.lock`
2. For each entry, display: name, version, source, installed path, install date

**Output Format**:
```
Name                  Version  Source                        Installed
example-agent         v1.0     github:anthropics/skills      2026-03-12
custom-tool           v2.1     local:/path/to/skills/        2026-03-11
```

### 5. skill remove `<name>`

Uninstalls a skill and removes it from tracking.

**Execution Logic**:
1. Find the skill in `system/packages.lock`
2. Delete the installed file from its target directory
3. Delete the discovery copy from `.claude/agents/` if it exists
4. Remove the entry from `system/packages.lock`
5. Optionally remove the SmartLibrary entry

**Parameters**:
```yaml
name: string
deregister: boolean         # Default: true. Remove from SmartLibrary.
```

## Source Cache

To avoid repeated cloning, GitHub sources are cached:

```yaml
cache:
  directory: ".skillos-cache/"
  ttl_hours: 24             # Re-clone after 24 hours
  max_size_mb: 500          # Evict oldest caches if exceeded
```

Cache is in `.skillos-cache/` (gitignored). Each source gets a directory named by its hash.

## Error Handling

| Error | Cause | Recovery |
|---|---|---|
| SOURCE_UNREACHABLE | Network issue or invalid URL | Skip source, try next. Warn user. |
| CLONE_FAILED | Git auth or branch not found | Log error, skip source. |
| VALIDATION_FAILED | Missing frontmatter keys | Reject skill, report which keys missing. |
| CONFLICT | Skill name already installed | Skip unless `--force`. |
| HASH_MISMATCH | Lock file hash doesn't match disk | Warn user, offer reinstall. |

## Claude Tool Mapping

- **Bash**: `git clone`, `md5`, `rm`, directory operations, cache management, `gh search repos`, `gh api search/repositories`
- **Read**: Parse `sources.list`, `packages.lock`, skill file frontmatter
- **Write**: Update `packages.lock`, copy skill files, register in SmartLibrary
- **Grep**: Search skill files by name/content within repos
- **Glob**: Discover `.md` files in local sources and cloned repos
- **WebFetch**: Fetch individual skill files from URL sources

## Integration with SystemAgent

SystemAgent can invoke SkillPackageManagerTool when a capability gap is identified:

1. SystemAgent detects missing capability during planning
2. Calls `skill search <capability-keyword>`
3. If match found: `skill install <name>`
4. New skill immediately available for delegation

This enables **on-demand skill acquisition** — the system can grow its capabilities at runtime by installing skills from configured sources.

## Usage Examples

```bash
# Install a skill
skillos execute: "skill install research-assistant-agent"

# Search for skills
skillos execute: "skill search quantum"

# Update all installed skills
skillos execute: "skill update"

# List installed skills
skillos execute: "skill list"

# Remove a skill
skillos execute: "skill remove outdated-agent"

# Add a new source
# Edit system/sources.list and add:
# github  myorg/my-skills  main  agents/
```
