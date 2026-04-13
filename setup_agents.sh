#!/bin/bash
# SkillOS Agent Setup Script for Claude Code v3.0
# Copies agent markdown files to .claude/agents/ for Claude Code discovery.
# Processes 4 tiers:
#   Tier 1: system/skills/ tree (hierarchical — agents discovered via manifest files)
#   Tier 2: system/agents/ (backward-compat stubs — skipped if full spec already copied)
#   Tier 3: projects/*/components/agents/ (project-specific agents with project prefix)
#   Tier 4: components/agents/ (shared agents, no prefix)
#   Tier 5: Remote sources from sources.list (optional, --install-sources flag)
#
# Usage:
#   ./setup_agents.sh              # Normal setup
#   ./setup_agents.sh --validate-only  # Validate without copying

set -euo pipefail

AGENTS_DIR=".claude/agents"
VALIDATE_ONLY=false
SUCCESS_COUNT=0
WARNING_COUNT=0
ERROR_COUNT=0
SKIP_COUNT=0

INSTALL_SOURCES=false
CACHE_DIR=".skillos-cache"

# Parse flags
for arg in "$@"; do
    case "$arg" in
        --validate-only)
            VALIDATE_ONLY=true
            echo "Running in validation-only mode..."
            ;;
        --install-sources)
            INSTALL_SOURCES=true
            echo "Will install skills from sources.list..."
            ;;
    esac
done

# Create destination directory
mkdir -p "$AGENTS_DIR"

# Remove any redirect stubs that may be lingering in .claude/agents/ from old setup runs.
# Full specs from system/skills/ tree supersede them.
for stale in "$AGENTS_DIR"/*.md; do
    [[ -f "$stale" ]] || continue
    if grep -q "^redirect:" "$stale" 2>/dev/null; then
        echo "  CLEANUP: Removing redirect stub: $(basename "$stale")"
        rm "$stale"
    fi
done

# Validate YAML frontmatter in an agent file
# Returns: 0 = valid, 1 = warning (incomplete), 2 = error (missing)
validate_frontmatter() {
    local file="$1"

    # Check for frontmatter delimiters
    if ! head -1 "$file" | grep -q "^---"; then
        echo "  ERROR: No YAML frontmatter found: $file"
        ERROR_COUNT=$((ERROR_COUNT + 1))
        return 2
    fi

    local has_name=false
    local has_description=false
    local has_tools=false
    local has_redirect=false

    # Parse frontmatter (between first and second ---)
    local in_frontmatter=false
    while IFS= read -r line; do
        if [[ "$line" == "---" ]]; then
            if $in_frontmatter; then
                break
            else
                in_frontmatter=true
                continue
            fi
        fi
        if $in_frontmatter; then
            [[ "$line" =~ ^name: ]] && has_name=true
            [[ "$line" =~ ^description: ]] && has_description=true
            [[ "$line" =~ ^tools: ]] && has_tools=true
            [[ "$line" =~ ^redirect: ]] && has_redirect=true
        fi
    done < "$file"

    # Backward-compat redirect stubs — skip silently (full spec already in skill tree)
    if $has_redirect; then
        return 3
    fi

    if ! $has_name || ! $has_description; then
        echo "  ERROR: Missing required frontmatter keys (name/description): $file"
        ERROR_COUNT=$((ERROR_COUNT + 1))
        return 2
    fi

    if ! $has_tools; then
        echo "  WARNING: Missing 'tools' key in frontmatter (uses tools_required or extends): $file"
        WARNING_COUNT=$((WARNING_COUNT + 1))
        return 1
    fi

    return 0
}

# Copy agent file if content has changed (idempotent)
copy_if_changed() {
    local source="$1"
    local dest="$2"

    if [[ -f "$dest" ]]; then
        # Compare file hashes for idempotency
        local src_hash dest_hash
        src_hash=$(md5 -q "$source" 2>/dev/null || md5sum "$source" | cut -d' ' -f1)
        dest_hash=$(md5 -q "$dest" 2>/dev/null || md5sum "$dest" | cut -d' ' -f1)

        if [[ "$src_hash" == "$dest_hash" ]]; then
            echo "  SKIP (unchanged): $(basename "$dest")"
            SKIP_COUNT=$((SKIP_COUNT + 1))
            return 0
        fi
    fi

    if ! $VALIDATE_ONLY; then
        cp "$source" "$dest"
        echo "  COPIED: $(basename "$source") -> $(basename "$dest")"
    else
        echo "  WOULD COPY: $(basename "$source") -> $(basename "$dest")"
    fi
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    return 0
}

# Process a single agent file
process_agent() {
    local source_path="$1"
    local dest_path="$2"

    validate_frontmatter "$source_path" && local fm_status=0 || local fm_status=$?

    # Return code 3 = redirect stub — skip silently
    [[ $fm_status -eq 3 ]] && return 0

    # Only copy if frontmatter exists (even if incomplete)
    if head -1 "$source_path" | grep -q "^---"; then
        copy_if_changed "$source_path" "$dest_path"
    fi
}

echo "=========================================="
echo "SkillOS Agent Setup v3.0"
echo "=========================================="
echo ""

# --- Tier 1: Hierarchical Skill Tree Agents (system/skills/) ---
echo "--- Tier 1: Hierarchical Skill Tree Agents (system/skills/) ---"
SKILL_TREE_AGENTS=()
if [[ -d "system/skills" ]]; then
    # Find all manifest files in the skill tree
    while IFS= read -r manifest; do
        [[ -f "$manifest" ]] || continue

        # Check if this is an agent manifest (type: agent)
        skill_type=$(grep -m 1 "^type:" "$manifest" 2>/dev/null | sed 's/^type:[[:space:]]*//' | tr -d '\r ' || true)
        [[ "$skill_type" == "agent" ]] || continue

        # Get the full_spec path from the manifest
        full_spec=$(grep -m 1 "^full_spec:" "$manifest" 2>/dev/null | sed 's/^full_spec:[[:space:]]*//' | tr -d '\r ' || true)
        [[ -n "$full_spec" && -f "$full_spec" ]] || continue

        dest_name=$(basename "$full_spec")
        dest="$AGENTS_DIR/$dest_name"
        SKILL_TREE_AGENTS+=("$dest_name")
        process_agent "$full_spec" "$dest"
    done < <(find "system/skills" -name "*.manifest.md" 2>/dev/null | sort)
else
    echo "  No system/skills/ directory found — falling back to legacy system/agents/."
fi
echo ""

# --- Tier 2: Legacy System Agents (backward-compat stubs — skip if already copied from skill tree) ---
echo "--- Tier 2: Legacy System Agents (backward-compat stubs) ---"
if [[ -d "system/agents" ]]; then
    for agent in system/agents/*.md; do
        [[ -f "$agent" ]] || continue
        dest_name=$(basename "$agent")
        # Skip if already loaded from skill tree (avoid overwriting full spec with stub)
        if [[ ${#SKILL_TREE_AGENTS[@]} -gt 0 && " ${SKILL_TREE_AGENTS[*]} " =~ " ${dest_name} " ]]; then
            echo "  SKIP (already loaded from skill tree): $dest_name"
            SKIP_COUNT=$((SKIP_COUNT + 1))
            continue
        fi
        dest="$AGENTS_DIR/$dest_name"
        process_agent "$agent" "$dest"
    done
else
    echo "  No system/agents/ directory found."
fi
echo ""

# --- Tier 3: Project Agents (project prefix) ---
echo "--- Tier 3: Project Agents ---"
if [[ -d "projects" ]]; then
    for project_dir in projects/*/; do
        [[ -d "$project_dir/components/agents" ]] || continue
        project_name=$(basename "$project_dir")
        echo "  Project: $project_name"
        for agent in "$project_dir/components/agents"/*.md; do
            [[ -f "$agent" ]] || continue
            agent_name=$(basename "$agent" .md)
            dest="$AGENTS_DIR/${project_name}_${agent_name}.md"
            process_agent "$agent" "$dest"
        done
    done
else
    echo "  No projects/ directory found."
fi
echo ""

# --- Tier 4: Shared Agents (no prefix) ---
echo "--- Tier 4: Shared Agents (components/agents/) ---"
if [[ -d "components/agents" ]]; then
    for agent in components/agents/*.md; do
        [[ -f "$agent" ]] || continue
        dest="$AGENTS_DIR/$(basename "$agent")"
        process_agent "$agent" "$dest"
    done
else
    echo "  No components/agents/ directory found."
fi
echo ""

# --- Tier 5: Install from sources.list (optional) ---
if $INSTALL_SOURCES && [[ -f "system/sources.list" ]]; then
    echo "--- Tier 5: Remote Sources (sources.list) ---"
    SOURCES_INSTALLED=0
    mkdir -p "$CACHE_DIR"

    while IFS= read -r line; do
        # Skip comments and blank lines
        [[ "$line" =~ ^#.*$ || -z "${line// /}" ]] && continue

        read -r src_type src_uri src_branch src_path <<< "$line"
        src_path="${src_path:-./}"

        case "$src_type" in
            github)
                repo_hash=$(echo "$src_uri-$src_branch" | md5 -q 2>/dev/null || echo "$src_uri-$src_branch" | md5sum | cut -d' ' -f1)
                cache_path="$CACHE_DIR/$repo_hash"

                # Clone or update cache
                if [[ -d "$cache_path" ]]; then
                    echo "  Updating cache: $src_uri ($src_branch)"
                    (cd "$cache_path" && git pull --quiet 2>/dev/null) || true
                else
                    echo "  Cloning: $src_uri ($src_branch)"
                    git clone --depth 1 --branch "$src_branch" "https://github.com/$src_uri.git" "$cache_path" 2>/dev/null || {
                        echo "  WARNING: Failed to clone $src_uri ($src_branch) - skipping"
                        WARNING_COUNT=$((WARNING_COUNT + 1))
                        continue
                    }
                fi

                # Install agent/tool files from the source path
                skill_dir="$cache_path/$src_path"
                if [[ -d "$skill_dir" ]]; then
                    for skill_file in "$skill_dir"/*.md; do
                        [[ -f "$skill_file" ]] || continue
                        skill_basename=$(basename "$skill_file")

                        # Determine if agent or tool
                        if [[ "$skill_basename" == *Agent.md ]]; then
                            dest="$AGENTS_DIR/$skill_basename"
                            process_agent "$skill_file" "$dest"
                        elif [[ "$skill_basename" == *Tool.md ]]; then
                            echo "  FOUND TOOL: $skill_basename (tools are not auto-copied to agents dir)"
                        else
                            dest="$AGENTS_DIR/$skill_basename"
                            process_agent "$skill_file" "$dest"
                        fi
                        SOURCES_INSTALLED=$((SOURCES_INSTALLED + 1))
                    done
                else
                    echo "  WARNING: Path '$src_path' not found in $src_uri"
                    WARNING_COUNT=$((WARNING_COUNT + 1))
                fi
                ;;
            local)
                if [[ -d "$src_uri" ]]; then
                    echo "  Installing from local: $src_uri"
                    for skill_file in "$src_uri"/*.md; do
                        [[ -f "$skill_file" ]] || continue
                        dest="$AGENTS_DIR/$(basename "$skill_file")"
                        process_agent "$skill_file" "$dest"
                        SOURCES_INSTALLED=$((SOURCES_INSTALLED + 1))
                    done
                else
                    echo "  WARNING: Local path not found: $src_uri"
                    WARNING_COUNT=$((WARNING_COUNT + 1))
                fi
                ;;
            url)
                echo "  URL sources require manual download: $src_uri"
                ;;
            *)
                echo "  WARNING: Unknown source type: $src_type"
                WARNING_COUNT=$((WARNING_COUNT + 1))
                ;;
        esac
    done < "system/sources.list"

    echo "  Skills from sources: $SOURCES_INSTALLED"
    echo ""
fi

# --- Summary ---
echo "=========================================="
echo "Setup Summary"
echo "=========================================="
echo "  Copied/Updated: $SUCCESS_COUNT"
echo "  Skipped (unchanged): $SKIP_COUNT"
echo "  Warnings: $WARNING_COUNT"
echo "  Errors: $ERROR_COUNT"
echo ""

# List discovered agents
echo "Discovered Agents:"
for agent in "$AGENTS_DIR"/*.md; do
    [[ -f "$agent" ]] || continue
    name=$(grep -m 1 "^name:" "$agent" 2>/dev/null | sed 's/name:\s*//' | tr -d '\r' || true)
    if [[ -n "$name" ]]; then
        echo "  - $name ($(basename "$agent"))"
    else
        echo "  - $(basename "$agent" .md) (no name in frontmatter)"
    fi
done

echo ""
if [[ $ERROR_COUNT -gt 0 ]]; then
    echo "STATUS: COMPLETED WITH ERRORS"
    exit 1
elif [[ $WARNING_COUNT -gt 0 ]]; then
    echo "STATUS: COMPLETED WITH WARNINGS"
    exit 0
else
    echo "STATUS: SUCCESS"
    exit 0
fi
