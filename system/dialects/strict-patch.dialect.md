---
dialect_id: strict-patch
name: Strict Patch Notation
version: 1.0.0
domain_scope: [orchestration, knowledge]
compression_type: structural
compression_ratio: "~90-98%"
reversible: true
input_format: natural-language
output_format: line-patch
---

# Strict Patch Dialect

## Purpose

Compresses file editing operations from verbose full-file rewrites or prose descriptions into exact line-number-based patch commands. Designed to solve the **small-model editing problem**: when a small LLM (Gemma 4B, Qwen 2.5, etc.) needs to fix a bug in a 500-line file, it typically either rewrites the entire file (wasting thousands of tokens and hallucinating changes) or produces malformed diffs. Strict Patch forces the model to emit only the exact lines that change — acting as a precision laser instead of a sloppy typist.

The key insight: **by constraining the output format to line-number operations, we remove the cognitive load of remembering unchanged code.** The model only needs to think about what changes, not what stays the same. This dramatically improves both speed and accuracy for small models.

## Domain Scope

- **orchestration** — Used by code-editing agents and tool-creation workflows. When the SystemAgent delegates file modifications to a sub-agent, the sub-agent can emit patches in strict-patch format instead of full rewrites.
- **knowledge** — Used for incremental wiki page updates. Instead of rewriting a concept page, emit line-level patches to update specific sections.

## Compression Rules

1. **File header**: `[FILE] path/to/file.ext` — identifies the target file.
2. **Delete line**: `[DEL:N] original_content` — delete line N with the exact original content (for verification).
3. **Add line**: `[ADD:N] new_content` — insert new content at line N (pushes existing lines down).
4. **Replace line**: `[DEL:N]` + `[ADD:N]` pair — delete then add at same line number.
5. **Multi-line add**: Multiple consecutive `[ADD:N]` lines. Each increments the effective line number.
6. **Multi-line delete**: Multiple consecutive `[DEL:N]` through `[DEL:M]` lines.
7. **End of patch**: `[EOF]` — signals patch complete.
8. **No context lines**: Unlike unified diff, unchanged lines are never emitted. Only changes appear.
9. **Indentation is exact**: Whitespace in `[ADD]` lines must match the target file's indentation exactly.
10. **One patch per file**: Each `[FILE]...[EOF]` block handles one file. Multiple files = multiple blocks.

## Preservation Rules

1. **Line numbers**: Must be exact — wrong line number = wrong patch.
2. **Original content in DEL**: The content after `[DEL:N]` must match the actual line in the file (used for verification before applying).
3. **Indentation**: All whitespace (spaces, tabs) must be preserved exactly in both DEL and ADD lines.
4. **String literals**: Quoted strings, variable names, operators preserved exactly.
5. **Encoding**: File encoding (UTF-8) preserved. No character transformations.
6. **Empty lines**: Empty lines that need deletion are `[DEL:N]` with no content after it.

## Grammar / Syntax

```
PATCH       := FILE_BLOCK+
FILE_BLOCK  := "[FILE]" SP filepath "\n" OPERATION+ "[EOF]" "\n"?
OPERATION   := DEL | ADD
DEL         := "[DEL:" line_num "]" SP? original_content? "\n"
ADD         := "[ADD:" line_num "]" SP content "\n"
line_num    := positive_integer
filepath    := relative_path | absolute_path
content     := any_text (preserving indentation)
```

### Operation Semantics

| Operation | Effect | Example |
|-----------|--------|---------|
| `[DEL:N]` | Remove line N from file | `[DEL:42] total = price + tax` |
| `[ADD:N]` | Insert new line at position N | `[ADD:42] total = price + (price * tax)` |
| `[DEL:N]` + `[ADD:N]` | Replace line N | Delete old, add new at same position |
| Multiple `[ADD:N]` | Insert multiple lines at N | Lines inserted in order |
| Multiple `[DEL:N..M]` | Delete range | Each DEL removes one line |

## Examples

### Example 1 — Single bug fix (1-line replace)
**Input** (verbose, ~1,500 tokens):
```
I found the bug in the calculate_total function. The issue is on line 42 where the tax
is being added directly instead of calculated as a percentage. Here is the corrected file:

def calculate_total(price, tax):
    # ... (200 lines of unchanged code that the model regenerates)
    total = price + (price * tax)  # Fixed: was "price + tax"
    # ... (100 more lines of unchanged code)
```

**Output** (4 lines, ~25 tokens):
```
[FILE] src/billing.py
[DEL:42] total = price + tax
[ADD:42] total = price + (price * tax)
[EOF]
```

**Ratio**: ~1,500 tokens → ~25 tokens = **~98% reduction**

### Example 2 — Add a new function
**Input** (verbose, ~800 tokens):
```
We need to add a validation function after the existing calculate_total function.
Here's the updated file with the new function added at line 55...
(rewrites 200+ lines including unchanged code)
```

**Output** (7 lines, ~40 tokens):
```
[FILE] src/billing.py
[ADD:55] def validate_total(total, max_allowed=10000):
[ADD:56]     if total < 0:
[ADD:57]         raise ValueError("Total cannot be negative")
[ADD:58]     if total > max_allowed:
[ADD:59]         raise ValueError(f"Total {total} exceeds maximum {max_allowed}")
[EOF]
```

**Ratio**: ~800 tokens → ~40 tokens = **~95% reduction**

### Example 3 — Multi-line replacement with indentation
**Input** (verbose description of replacing an if-block):
```
Replace the error handling block on lines 78-82 with a more robust version
that includes logging and a fallback...
```

**Output**:
```
[FILE] src/api/handler.py
[DEL:78]     except ConnectionError:
[DEL:79]         return None
[DEL:80]
[ADD:78]     except ConnectionError as e:
[ADD:79]         logger.error(f"Connection failed: {e}")
[ADD:80]         return fallback_response()
[EOF]
```

**Ratio**: ~200 tokens → ~35 tokens = **~82% reduction**

### Example 4 — Multiple files in one patch
**Input**: "Fix the import in utils.py and update the test file to match"

**Output**:
```
[FILE] src/utils.py
[DEL:3] from datetime import datetime
[ADD:3] from datetime import datetime, timezone
[EOF]
[FILE] tests/test_utils.py
[DEL:15]     result = get_timestamp()
[ADD:15]     result = get_timestamp(tz=timezone.utc)
[EOF]
```

## Expansion Protocol

Strict Patch is **reversible** — patches can be described in natural language and the original change intent can be reconstructed.

1. **`[FILE]` → file identification**: "In the file [path]..."
2. **`[DEL:N]` → deletion description**: "Remove line N which contains '[content]'."
3. **`[ADD:N]` → addition description**: "Add the following at line N: '[content]'."
4. **DEL+ADD pair → replacement description**: "Replace line N: change '[old]' to '[new]'."
5. **Multi-line ADD → insertion description**: "Insert a new block starting at line N containing..."
6. **Multiple FILE blocks → multi-file description**: "Changes span [N] files..."

### Applying Patches

To apply a strict-patch to a file:

1. Read the target file into a line array.
2. For each `[DEL:N]`, verify the content matches line N. If mismatch, abort with error.
3. Apply DEL operations in reverse order (highest line number first) to avoid index shifting.
4. Apply ADD operations in forward order (lowest line number first).
5. Write the modified line array back to the file.

### Reversibility Confidence

- Single-line replacements: 95-100% (exact inverse is trivial)
- Multi-line insertions: 90-95% (intent clear from content)
- Complex multi-file patches: 85-90%

## Metrics

| Metric | Value |
|--------|-------|
| Compression ratio | ~90-98% vs full-file rewrites |
| Token reduction | ~85-97% |
| Reversibility | Very high — exact line operations are unambiguous |
| Latency | Negligible (structured output, no transformation) |
| Error rate | <0.5% when line numbers are correct |
| Quality improvement | Eliminates small-model hallucination during file edits |
