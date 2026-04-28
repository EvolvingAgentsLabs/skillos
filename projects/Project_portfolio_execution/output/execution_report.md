# Portfolio Execution Report: CUT + DEVELOP

**Date**: 2026-04-26
**Parent**: Project_strategic_portfolio_analysis
**Status**: SUCCESS

---

## CUT Operations — Summary

### skillos — 18 items deleted (~1.5 MB)
| Item | Type | Size |
|------|------|------|
| `agent_runtime.py` | Python runtime (deprecated) | 1847 lines |
| `system/agents/` | 9 backward-compat stubs | 9 .md files |
| `system/tools/` | 6 backward-compat stubs | 6 .md files |
| `system/SmartLibrary.md` | Deprecated redirect | 36 lines |
| `system/memory_log.md` | Deprecated redirect | 7 lines |
| Boot.md evolving-memory ref | Stale :8420 reference | 2 lines |
| `projects/Project_llm_os/` | Demo artifact | 112K |
| `projects/Project_aorta_dialects/` | Demo artifact | 256K |
| `projects/Project_dialect_benchmark/` | Demo artifact | 32K |
| `projects/Project_echo_q/` | Demo artifact | 136K |
| `projects/Project_echo_q_dialects/` | Demo artifact | 112K |
| `projects/Project_patch_benchmark/` | Demo artifact | 76K |

### skillos_mini — 15 items deleted (~1.0 MB)
| Item | Type | Size |
|------|------|------|
| `experiments/gemma4-skills/` | Completed spike | 92K |
| `cartridges/cooking/` | Off-pivot (not oficios) | 52K |
| `cartridges/learn/` | Off-pivot (not oficios) | 88K |
| `cartridges/demo/` | Off-pivot demos | 80K |
| `compactor.py` | Dead code (TS version used) | 6.6K |
| `run_aorta_gemma.py` | Obsolete runner | 1.3K |
| `run_echoq_gemma.py` | Obsolete runner | 1.5K |
| `projects/Project_aorta_gemma/` (v1-v4) | Demo outputs | 84K |
| `projects/Project_echo_q_gemma/` (v1-v4) | Demo outputs | 144K |

### Remaining Doc Debt (tracked, not blocking)
- 60+ dangling documentation references across QWEN.md, README.md, docs/, tests/
- Should be cleaned up in a follow-up PR per project

---

## DEVELOP Operations — llm_os Improvements

### 1. `<|state|>` — 14th ISA Opcode (grammar/isa.gbnf)

**What**: Added `state-stmt` as a daemon-injected opcode for ISA state recovery after KV compaction.

**Grammar rule**: `state-stmt ::= "<|state|>" json "<|/state|>" nl`

**Added to**: both `top-stmt` and `loop-stmt` alternations (legal at any depth).

**Invariant I6**: `<|state|>` is daemon-injected after KV compaction to rehydrate ISA state. Informational — no transition, no daemon response needed.

### 2. ISA-Aware Compaction (runtime/swap.rs)

**What**: The compactor now walks the dropped token window to extract ISA state before discarding tokens. If state is nontrivial (open loops, pending results), it injects a `<|state|>{...}<|/state|>` preamble.

**New types**:
```rust
struct IsaState {
    loop_depth: u32,
    pending_results: Vec<String>,
    pending_acks: Vec<String>,
    open_forks: Vec<String>,
    open_loops: Vec<String>,
}
```

**Key functions**:
- `extract_isa_state(messages)` — walks message history, tracks ISA state
- `IsaState::to_preamble()` — serializes as `<|state|>{...}<|/state|>`
- `IsaState::is_nontrivial()` — returns true if any state must survive compaction

**Modified**: `compact()` now returns `CompactResult { ..., isa_state: Option<IsaState> }`

### 3. State Parsing + Rehydration (runtime/parser.rs)

**What**: Parser recognizes `<|state|>` and rehydrates the OpcodeStream's loop_depth from the payload.

**New**:
- `Opcode::State` variant (14th opcode)
- `Opcode::is_daemon_injected()` method
- `Statement::State { payload: Value }` variant
- `parse_state()` function
- OpcodeStream rehydrates `loop_depth` from State payload

**Tests**: 3 new tests covering parsing, rehydration, and opcode classification.

### 4. Cross-Project Trace Pipeline (scripts/promote_traces.py)

**What**: The DPO trace promotion pipeline now supports YAML-frontmatter markdown traces from skillos and RoClaw, in addition to JSONL.

**New CLI flag**: `--markdown-traces` accepts glob patterns for .md trace files.

**New functions**:
- `_parse_yaml_frontmatter()` — regex-based parser (no pyyaml dependency)
- `_md_trace_to_jsonl()` — converts markdown traces to DPO pipeline schema
- `load_markdown_traces()` — loads and converts markdown trace files

**Usage**:
```bash
python3 scripts/promote_traces.py \
    --traces traces/*.jsonl \
    --markdown-traces ../skillos_robot/traces/sim3d/*.md ../skillos/projects/*/memory/short_term/*.md \
    --out out/dpo.jsonl
```

---

## Impact Assessment

| Metric | Before | After |
|--------|--------|-------|
| skillos file count | ~130 | ~95 (-27%) |
| skillos_mini file count | ~180 | ~140 (-22%) |
| llm_os ISA opcodes | 13 | 14 (+<|state|>) |
| Compaction safety | Silent state corruption risk | ISA-aware with preamble injection |
| Trace pipeline scope | llm_os JSONL only | Cross-project (JSONL + markdown) |
| Grammar invariants | 5 (I1-I5) | 6 (I1-I6) |

---

## What's Next (from strategic analysis Tier 1-2)

1. **llm_os §1 grammar swap**: The `<|state|>` opcode lays groundwork. Next: the multi-grammar stack patch to llama.cpp for in-process grammar switching.
2. **RoClaw: Commit 28 sim traces**: Training data sitting untracked.
3. **skillos_mini M1**: Schedule validation interviews with electricistas.
4. **Doc debt cleanup**: Fix 60+ dangling references across repos.
