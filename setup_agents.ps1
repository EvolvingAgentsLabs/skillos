# SkillOS Agent Setup Script for Claude Code (Windows)
# v2.0 - Synced with setup_agents.sh feature parity
# Copies agent markdown files to .claude/agents/ for Claude Code discovery

$ErrorActionPreference = "SilentlyContinue"

# Counters
$copied = 0
$skipped = 0
$warned = 0

# Create the .claude/agents directory if it doesn't exist
New-Item -ItemType Directory -Force -Path ".\.claude\agents" | Out-Null

# Function to compute file hash for idempotent copy
function Get-FileHash256 {
    param ([string]$Path)
    return (Get-FileHash -Path $Path -Algorithm MD5).Hash
}

# Function to process agent files with YAML frontmatter validation
function Process-AgentFile {
    param (
        [string]$sourcePath,
        [string]$destPath
    )

    # Check if the file has YAML frontmatter (starts with ---)
    $firstLine = (Get-Content -Path $sourcePath -TotalCount 1)
    if ($firstLine -notmatch "^---") {
        Write-Host "  SKIP (no frontmatter): $sourcePath" -ForegroundColor Yellow
        $script:warned++
        return
    }

    # Check for required 'name:' field in frontmatter
    $content = Get-Content -Path $sourcePath -Raw
    if ($content -notmatch "(?m)^name:\s*\S+") {
        Write-Host "  WARN (missing name: field): $sourcePath" -ForegroundColor Yellow
        $script:warned++
    }

    # Idempotent copy: skip if destination exists and is identical
    if (Test-Path $destPath) {
        $srcHash = Get-FileHash256 -Path $sourcePath
        $dstHash = Get-FileHash256 -Path $destPath
        if ($srcHash -eq $dstHash) {
            $script:skipped++
            return
        }
    }

    Copy-Item -Path $sourcePath -Destination $destPath -Force
    Write-Host "  Copied: $sourcePath -> $destPath" -ForegroundColor Green
    $script:copied++
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SkillOS Agent Setup (Windows)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# --- Tier 1: System Agents ---
Write-Host "[Tier 1] System agents (system/agents/)..." -ForegroundColor Cyan
$systemAgents = Get-ChildItem -Path "system\agents\*.md" -ErrorAction SilentlyContinue
foreach ($agent in $systemAgents) {
    $destPath = ".\.claude\agents\$($agent.Name)"
    Process-AgentFile -sourcePath $agent.FullName -destPath $destPath
}

# --- Tier 2: Project-Specific Agents ---
Write-Host "[Tier 2] Project agents (projects/*/components/agents/)..." -ForegroundColor Cyan
$projectDirs = Get-ChildItem -Path "projects" -Directory -ErrorAction SilentlyContinue
foreach ($projectDir in $projectDirs) {
    $agentsPath = Join-Path $projectDir.FullName "components\agents"
    if (Test-Path $agentsPath) {
        Write-Host "  Project: $($projectDir.Name)" -ForegroundColor Gray
        $projectAgents = Get-ChildItem -Path "$agentsPath\*.md" -ErrorAction SilentlyContinue
        foreach ($agent in $projectAgents) {
            $agentName = $agent.BaseName
            $destPath = ".\.claude\agents\$($projectDir.Name)_$($agentName).md"
            Process-AgentFile -sourcePath $agent.FullName -destPath $destPath
        }
    }
}

# --- Tier 3: Shared Agents (components/agents/) ---
Write-Host "[Tier 3] Shared agents (components/agents/)..." -ForegroundColor Cyan
$sharedAgents = Get-ChildItem -Path "components\agents\*.md" -ErrorAction SilentlyContinue
foreach ($agent in $sharedAgents) {
    $destPath = ".\.claude\agents\$($agent.Name)"
    Process-AgentFile -sourcePath $agent.FullName -destPath $destPath
}

# --- Summary ---
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Setup Complete" -ForegroundColor Cyan
Write-Host "  Copied: $copied | Skipped (unchanged): $skipped | Warnings: $warned" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# List discovered agents
Write-Host "Discovered agents:" -ForegroundColor Cyan
$agentFiles = Get-ChildItem -Path ".\.claude\agents\*.md" -ErrorAction SilentlyContinue
foreach ($f in $agentFiles) {
    $content = Get-Content -Path $f.FullName -Raw
    if ($content -match "(?m)^name:\s*(.+)$") {
        Write-Host "  - $($Matches[1].Trim())" -ForegroundColor White
    } else {
        Write-Host "  - $($f.BaseName) (no name in frontmatter)" -ForegroundColor Yellow
    }
}
