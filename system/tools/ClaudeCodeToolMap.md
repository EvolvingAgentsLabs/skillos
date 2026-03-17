---
name: claude-code-tool-map
type: tool-registry
version: "2.0"
description: >
  Authoritative mapping of SkillOS framework component calls to Claude Code's
  native tools. Defines parameters, cost envelopes, latency targets, error
  modes, retry strategies, fallback chains, and a decision matrix.
status: "[REAL] - Production Ready"
last_updated: "2026-03-12"
tools_covered:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - WebFetch
  - WebSearch
  - Task
  - NotebookEdit
---

# Claude Code Tool Map

## Purpose

This registry defines how every SkillOS framework operation maps to Claude Code's native tools. It is the single source of truth for tool selection, cost estimation, error handling, and retry strategies.

## Tool Specifications

### Read
- **Framework aliases**: FileReaderTool, RealFileSystemTool (read), QueryMemoryTool (memory loading)
- **Use cases**: Loading agent specs, reading state files, ingesting input documents, viewing images/PDFs
- **Cost**: ~$0.0001-$0.005/call | Latency p50: <50ms
- **Reliability**: 99%
- **Error modes**: FILE_NOT_FOUND (5%), PERMISSION_DENIED (1%), PDF_TOO_LARGE
- **Retry**: 2 attempts, immediate. Correct path on FILE_NOT_FOUND. Add pages param for large PDFs.
- **Fallback**: Bash cat, Grep content mode

### Write
- **Framework aliases**: FileWriterTool, RealFileSystemTool (write), MemoryTraceManager
- **Use cases**: Creating agent specs, writing outputs, initializing state files, persisting memory
- **Cost**: ~$0.0001-$0.01/call | Latency p50: <100ms
- **Reliability**: 98%
- **Error modes**: DIRECTORY_NOT_FOUND (10%), PERMISSION_DENIED (2%)
- **Retry**: 2 attempts. On DIRECTORY_NOT_FOUND: mkdir -p first, then retry.
- **Fallback**: Bash mkdir + cat redirection

### Edit
- **Framework aliases**: FileEditorTool, AdaptivePlanningTool (state updates)
- **Use cases**: Updating state file sections, appending log entries, patching agent specs
- **Cost**: ~$0.0001-$0.003/call | Latency p50: <100ms
- **Reliability**: 96%
- **Error modes**: STRING_NOT_FOUND (15%), AMBIGUOUS_MATCH (5%)
- **Retry**: 3 attempts. Read file first to verify exact text. Widen context for unique match.
- **Fallback**: Read + modify + Write entire file

### Bash
- **Framework aliases**: SystemTool, QuantumComputingTool, LocalLLMTool, TreeSearchTool
- **Use cases**: Package installs, Python execution, directory creation, git ops, text processing
- **Cost**: ~$0.0002-$0.05/call | Latency p50: 100ms-5s
- **Reliability**: 92%
- **Error modes**: COMMAND_NOT_FOUND (8%), TIMEOUT (3%), IMPORT_ERROR (10%)
- **Retry**: 2 attempts. Install missing packages first. Split large operations.
- **Fallback**: Write script file then execute. Read + manual analysis.
- **Best practice**: Always use absolute paths. Pipe through head to limit output.

### Glob
- **Framework aliases**: SearchTool (file discovery), RealFileSystemTool (listing)
- **Use cases**: Discovering agent files, finding outputs by type, checking path existence
- **Cost**: ~$0.0001/call | Latency p50: <100ms
- **Reliability**: 99%
- **Error modes**: NO_MATCHES (common, not an error), INVALID_PATTERN (2%)
- **Retry**: Broaden pattern on NO_MATCHES.
- **Fallback**: Bash find

### Grep
- **Framework aliases**: SearchTool (content), MemoryAnalysisAgent (pattern search)
- **Use cases**: Memory log pattern search, finding agent capabilities, content verification
- **Cost**: ~$0.0001-$0.005/call | Latency p50: <200ms
- **Reliability**: 99%
- **Modes**: files_with_matches (default, cheapest) | content | count
- **Error modes**: INVALID_REGEX (3%), OUTPUT_LARGE (5%)
- **Retry**: Simplify regex. Add head_limit for broad patterns.
- **Fallback**: Bash rg, Read entire file

### WebFetch
- **Framework aliases**: WebFetcherTool, RealWebFetchTool
- **Use cases**: Fetching live content from known URLs, research tasks
- **Cost**: ~$0.001-$0.02/call | Latency p50: 2-5s | 15-min cache
- **Reliability**: 88%
- **Error modes**: HTTP_TIMEOUT (5%), AUTH_REQUIRED (10%), RATE_LIMITED (5%), REDIRECT (8%)
- **Retry**: 3 attempts, exponential backoff (2s, 5s, 15s). Do NOT retry AUTH_REQUIRED.
- **Fallback**: WebSearch, Bash curl, gh CLI for GitHub

### WebSearch
- **Framework aliases**: WebSearchTool
- **Use cases**: Topic discovery, finding URLs before WebFetch, current events
- **Cost**: ~$0.002-$0.01/call | Latency p50: 1-3s
- **Reliability**: 92%
- **Error modes**: NO_RESULTS (3%), GEO_RESTRICTED
- **Retry**: Broaden query. Remove domain filters.
- **Fallback**: WebFetch with known base URL
- **Best practice**: Include current year (2026) in queries for recent info.

### Task (Agent Delegation)
- **Framework aliases**: SubTaskTool, AgentDelegation
- **Use cases**: Invoking specialized agents, parallel research, domain-specific tasks
- **Cost**: ~$0.01-$0.50/call | Latency p50: 30s-2min
- **Reliability**: 90%
- **Error modes**: AGENT_NOT_FOUND (10%), CONTEXT_INSUFFICIENT (15%), OUTPUT_INCOMPLETE (8%)
- **Retry**: 2 attempts. Copy agent file to .claude/agents/ on AGENT_NOT_FOUND. Enrich prompt on CONTEXT_INSUFFICIENT.
- **Fallback**: Execute directly without delegation. Break into smaller tasks.

### NotebookEdit
- **Framework aliases**: JupyterNotebookTool
- **Use cases**: Adding/replacing/deleting cells in .ipynb notebooks
- **Cost**: ~$0.0002-$0.005/call | Latency p50: <200ms
- **Reliability**: 94%
- **Error modes**: INVALID_CELL_INDEX (5%), INVALID_JSON (2%)
- **Retry**: Read notebook to count cells, correct index.

## Decision Matrix

### Read vs. Grep vs. Bash cat
| Situation | Tool | Reason |
|---|---|---|
| Load known file fully | Read | Line-numbered, clean |
| Find files containing pattern | Grep (files_with_matches) | Purpose-built |
| Extract matching lines | Grep (content) | Lower cost than full Read |

### Write vs. Edit
| Situation | Tool | Reason |
|---|---|---|
| New file | Write | File doesn't exist |
| Full replacement | Write | Intentional overwrite |
| Patch specific section | Edit | Preserves rest of file |
| Append log entry | Edit | Atomic, no full rewrite |

### WebFetch vs. WebSearch
| Situation | Tool | Reason |
|---|---|---|
| URL known | WebFetch | Direct, richer content |
| URL unknown | WebSearch | Discovers candidates |
| Authenticated URL | Neither | Use gh CLI or MCP |

### Task vs. Bash
| Situation | Tool | Reason |
|---|---|---|
| Domain reasoning needed | Task | Agent context |
| Pure computation | Bash | No LLM overhead |
| Parallel subtasks | Task | True parallelism |

## Cost Tiers

```yaml
tier_0_free: [Read, Write, Edit, Glob, Grep, NotebookEdit]
tier_1_low: [WebFetch, WebSearch, Bash (simple)]
tier_2_medium: [Task (simple sub-agent)]
tier_3_high: [Task (complex multi-tool sub-agents)]
```

## Rate Limits

```yaml
WebFetch: {per_domain_rps: 1, concurrent: 3}
WebSearch: {per_minute: 10, concurrent: 2}
Task: {concurrent: 5}
Bash: {concurrent: 3}
NotebookEdit: {concurrent: 1}
```
