# Tutorial: Running Operation Echo-Q

A step-by-step guide to running the quantum cepstral deconvolution scenario — the "Markdown as mathematical blackboard" demonstration.

---

## What This Scenario Does

Operation Echo-Q orchestrates 4 dynamically created agents through a pipeline that:

1. **Builds a math wiki** — LaTeX-rich concept pages on quantum computing
2. **Extracts invariants** — mathematical constraints that code must satisfy
3. **Writes & validates code** — Qiskit implementation with a reflective error-recovery loop
4. **Synthesizes a whitepaper** — citing every wiki page

The key insight: no single LLM call could derive the math AND write correct code. The wiki acts as external memory that compounds across agent invocations.

---

## Prerequisites

### Required Software

| Dependency | Purpose | Install |
|---|---|---|
| Python 3.12+ | Runtime | `brew install python@3.12` (macOS) |
| Qiskit | Quantum simulation | `pip install qiskit qiskit-aer` |
| NumPy | Signal processing | `pip install numpy` |
| Claude Code | SkillOS runtime | Already installed if you're reading this |

### Verify Installation

```bash
python3.12 -c "import qiskit; print(qiskit.__version__)"
python3.12 -c "import numpy; print(numpy.__version__)"
```

If Qiskit isn't installed, the scenario's reflective loop will attempt to install it automatically via `pip install qiskit qiskit-aer` in Phase 3.

---

## Quick Start (Full Scenario)

The simplest way — run all 4 phases end-to-end:

```bash
skillos execute: "Run the Operation Echo-Q scenario: derive and implement a quantum cepstral analysis algorithm using the wiki as a mathematical blackboard"
```

This boots SkillOS (if not already booted), creates the `projects/Project_echo_q/` directory structure, and executes all 4 phases sequentially.

**Estimated time**: 5-15 minutes depending on model speed and error-recovery cycles.

---

## Step-by-Step Walkthrough

If you prefer to run each phase independently (useful for learning or debugging):

### Step 1: Boot SkillOS

If this is your first command in the session:

```bash
boot skillos
```

You'll see the ASCII banner and `System Status: READY`.

### Step 2: Run Phase 1 — Build the Math Wiki

```bash
skillos execute: "Run Operation Echo-Q Phases 1-2: build the quantum computing wiki and extract mathematical constraints"
```

**What happens**:
- `quantum-theorist-agent` is created dynamically
- It writes 5 concept pages and 1 entity page to `wiki/concepts/` and `wiki/entities/`
- Each page contains LaTeX formulas and `[[WikiLinks]]` to related concepts
- `pure-mathematician-agent` reads the wiki and writes `state/constraints.md`

**Inspect the results**:
```bash
# See what wiki pages were created
ls projects/Project_echo_q/wiki/concepts/
ls projects/Project_echo_q/wiki/entities/

# Read a concept page (check for LaTeX and WikiLinks)
cat projects/Project_echo_q/wiki/concepts/quantum-fourier-transform.md

# Read the constraints file
cat projects/Project_echo_q/state/constraints.md

# Check the wiki index
cat projects/Project_echo_q/wiki/_index.md
```

**What to look for**:
- Each concept page has YAML frontmatter with `related:` WikiLinks
- LaTeX formulas use `$...$` (inline) and `$$...$$` (display)
- `constraints.md` has >= 5 hard constraints, each citing a wiki page
- The non-unitarity problem is addressed in `[[homomorphic-signal-separation]]`

### Step 3: Run Phase 3 — Implement & Validate

```bash
skillos execute: "Run Operation Echo-Q Phase 3: implement quantum_cepstrum.py from the existing wiki and constraints"
```

**What happens**:
- `qiskit-engineer-agent` reads wiki + constraints, writes `output/quantum_cepstrum.py`
- The code is executed via Bash
- If it fails, `error-recovery-agent` cross-references the error against wiki math and constraints
- Fix → re-run → validate (up to 3 cycles)

**Inspect the results**:
```bash
# Read the implementation
cat projects/Project_echo_q/output/quantum_cepstrum.py

# Check validation result
cat projects/Project_echo_q/state/validation_result.md

# If errors occurred, read the diagnosis
cat projects/Project_echo_q/state/error_diagnosis.md
```

**What to look for**:
- Code imports `qiskit` and `numpy`
- A synthetic test signal with known echo delay is created
- QFT is applied (via Qiskit's built-in `QFT` or manual construction)
- The log approximation uses QSVT or Taylor series (not a raw `np.log`)
- `validation_result.md` says PASS or PARTIAL with explanation

### Step 4: Run Phase 4 — Synthesize Whitepaper

```bash
skillos execute: "Run Operation Echo-Q Phase 4: synthesize the Echo-Q whitepaper from wiki, code, and validation results"
```

**What happens**:
- `system-architect-agent` reads all artifacts (wiki, constraints, code, validation)
- Writes `output/Echo_Q_Whitepaper.md` with citations to every wiki page

**Inspect the results**:
```bash
cat projects/Project_echo_q/output/Echo_Q_Whitepaper.md
```

**What to look for**:
- Abstract, theoretical foundation, algorithm design, results sections
- Every mathematical claim cites a `[[WikiLink]]`
- Constraint verification table showing C1-C5 status
- Error recovery journal (if errors occurred in Phase 3)

---

## Understanding the Output

After a full run, your project directory looks like:

```
projects/Project_echo_q/
├── components/agents/          # 4 dynamically created agent definitions
│   ├── quantum-theorist-agent.md
│   ├── pure-mathematician-agent.md
│   ├── qiskit-engineer-agent.md
│   └── system-architect-agent.md
├── wiki/
│   ├── _schema.md              # Wiki constitution for quantum computing
│   ├── _index.md               # Catalog of all wiki pages
│   ├── _log.md                 # Operation history
│   ├── concepts/               # 5 LaTeX-rich math pages
│   │   ├── quantum-fourier-transform.md
│   │   ├── quantum-singular-value-transformation.md
│   │   ├── block-encoding.md
│   │   ├── cepstral-analysis.md
│   │   └── homomorphic-signal-separation.md
│   └── entities/
│       └── grand-unification-of-quantum-algorithms.md
├── output/
│   ├── quantum_cepstrum.py     # Working Qiskit code
│   └── Echo_Q_Whitepaper.md    # Final synthesis document
├── state/
│   ├── constraints.md          # Mathematical invariants
│   ├── validation_result.md    # PASS or PARTIAL
│   └── error_diagnosis.md      # Error recovery log (if any)
└── memory/
    ├── short_term/             # Agent interaction logs
    └── long_term/              # Consolidated learnings
```

### Key Files to Read

| File | What it shows |
|---|---|
| `wiki/concepts/homomorphic-signal-separation.md` | The core theoretical challenge — non-unitary log |
| `state/constraints.md` | How math becomes enforceable code rules |
| `output/quantum_cepstrum.py` | The actual quantum algorithm implementation |
| `state/error_diagnosis.md` | How errors were traced back to math violations |
| `output/Echo_Q_Whitepaper.md` | Everything synthesized with citations |

---

## Viewing in Obsidian

The wiki is fully Obsidian-compatible. To browse it as a linked knowledge graph:

1. Open Obsidian
2. "Open folder as vault" → select `projects/Project_echo_q/wiki/`
3. Click any `[[WikiLink]]` to navigate between concepts
4. Open the Graph View to see the concept relationship network

---

## Troubleshooting

### "Qiskit not found"

The reflective loop handles this automatically. If it doesn't:

```bash
pip install qiskit qiskit-aer numpy
```

### Phase 3 exhausts all 3 retry cycles

This is expected for complex quantum algorithms. Check `state/validation_result.md` — it will say PARTIAL and document what works and what doesn't. The whitepaper in Phase 4 will still be generated with honest reporting of limitations.

### Wiki pages are missing cross-references

Run the knowledge lint agent manually:

```bash
skillos execute: "Run knowledge-lint-agent on projects/Project_echo_q/wiki/"
```

### Want to re-run just one phase

Each phase is idempotent. Re-running Phase 3, for example, will read the existing wiki and constraints and produce a new `quantum_cepstrum.py`:

```bash
skillos execute: "Run Operation Echo-Q Phase 3: implement quantum_cepstrum.py from the existing wiki and constraints"
```

---

## What Makes This Scenario Special

This isn't just a quantum computing demo. It demonstrates three core SkillOS patterns:

1. **Wiki as Blackboard** — The math is too complex for a single prompt. The wiki lets Agent 1 write theorems that Agent 3 reads when writing code. This is the compounding loop.

2. **Sentient State as Invariants** — `constraints.md` turns mathematical laws into enforceable rules. When code violates unitarity (C1), the error-recovery agent knows *why* because it can read the constraint and trace it back to the wiki derivation.

3. **Reflective Error Recovery** — Errors aren't just retried. They're *diagnosed* against the mathematical wiki. "Log of zero" isn't a mystery — it's constraint C3 being violated, and the wiki page `[[homomorphic-signal-separation]]` explains the fix.

These patterns apply to any domain where reasoning chains exceed a single context window: legal analysis, architectural design, scientific research, financial modeling.
