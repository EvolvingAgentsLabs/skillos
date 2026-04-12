# Math Benchmark Report: Formal Proof Dialect

**Generated**: 2026-04-12 18:27
**Task**: Calculate spanning trees of K_{3,4} via Matrix Tree Theorem
**Correct Answer**: 432

## Summary

| Metric | Plain Claude | SkillOS Solver | SkillOS Solver+Renderer |
|---|---|---|---|
| Output tokens | 4,582 | 2,232 | 2,634 |
| Token reduction | baseline | **-51.3%** | **-42.5%** |
| Cost (USD) | $0.2885 | $0.0770 | $0.1208 |
| Duration (s) | 71.5 | 33.0 | 42.6 |
| Turns | 1 | 1 | 2 |

## Quality Verification (Automated)

| Check (pts) | Plain Claude | SkillOS Solver |
|---|---|---|
| Answer = 432 (50) | YES | YES |
| Laplacian matrix (10) | No | No |
| Cofactor/minor (10) | Yes | Yes |
| Determinant calc (10) | Yes | Yes |
| Intermediate 27x16 (20) | Yes | Yes |
| **Total score** | **90/100** | **90/100** |

## Key Findings

- **Token reduction (solver only)**: 51.3% fewer output tokens
- **Token reduction (with renderer)**: 42.5% fewer even with English translation step
- **Math accuracy**: Plain CORRECT, SkillOS CORRECT
- **Cognitive Scaffolding**: Formal-proof notation forces step-by-step computation, maintaining arithmetic accuracy

## Raw Outputs

### Plain Claude

<details>
<summary>Click to expand (4,582 tokens)</summary>

Let me redo my Schur complement calculation carefully — I made an error. Let me recompute by hand.

---

## Corrected Step 3: Compute det(L₁₁) carefully

The 6×6 cofactor matrix L₁₁ (deleting row/column of a₁):

```
        a2  a3  b1  b2  b3  b4
    ┌                            ┐
a2  │  4   0  -1  -1  -1  -1    │
a3  │  0   4  -1  -1  -1  -1    │
b1  │ -1  -1   3   0   0   0    │
b2  │ -1  -1   0   3   0   0    │
b3  │ -1  -1   0   0   3   0    │
b4  │ -1  -1   0   0   0   3    │
    └                            ┘
```

### Block structure:

- **P** = `[[4,0],[0,4]]` = 4I₂ (2×2, top-left)
- **Q** = 2×4 matrix, all entries -1
- **R** = 4×2 matrix, all entries -1
- **S** = 3I₄ (4×4, bottom-right)

**Schur complement** = S - R P⁻¹ Q

**R P⁻¹:** Each entry of R is -1, P⁻¹ = (1/4)I₂, so R P⁻¹ is 4×2 with all entries -1/4.

**(R P⁻¹) Q:** This is a 4×4 matrix. Entry (i,j):

$$\sum_{k=1}^{2} (RP^{-1})_{ik} \cdot Q_{kj} = (-\tfrac{1}{4})(-1) + (-\tfrac{1}{4})(-1) = \tfrac{1}{4} + \tfrac{1}{4} = \tfrac{1}{2}$$

So R P⁻¹ Q = (1/2) J₄ — this part was correct.

**Schur complement** = 3I₄ - (1/2)J₄:

```
┌                          ┐
│  5/2   -1/2  -1/2  -1/2  │
│ -1/2    5/2  -1/2  -1/2  │
│ -1/2   -1/2   5/2  -1/2  │
│ -1/2   -1/2  -1/2   5/2  │
└                          ┘
```

Wait — that's wrong! 3 - 1/2 = **5/2** on diagonal, and 0 - 1/2 = **-1/2** off diagonal. That's what I had. Let me recompute the determinant more carefully.

### det(3I₄ - (1/2)J₄) = det((1/2)(6I₄ - J₄))

Factor out 1/2 from each of 4 rows: (1/2)⁴ · det(6I₄ - J₄)

**Eigenvalues of J₄** (the 4×4 all-ones matrix): 4 (multiplicity 1) and 0 (multiplicity 3).

**Eigenvalues of 6I₄ - J₄**: 6 - 4 = **2** (multiplicity 1) and 6 - 0 = **6** (multiplicity 3).

$$\det(6I_4 - J_4) = 2 \times 6^3 = 2 \times 216 = 432$$

$$\det(S - RP^{-1}Q) = \frac{1}{16} \times 432 = 27$$

### Final answer:

$$\det(L_{11}) = \det(P) \times \det(S - RP^{-1}Q) = 16 \times 27 = 432$$

---

I see my earlier error: I incorrectly wrote 3I₄ - (1/2)J₄ = (1/2)(5I₄ - J₄). The correct factorization is (1/2)(6I₄ - J₄).

## Step 4: Verification

The known formula for the number of spanning trees of K_{m,n} is:

$$\tau(K_{m,n}) = m^{n-1} \cdot n^{m-1}$$

For K_{3,4}:

$$\tau = 3^{4-1} \cdot 4^{3-1} = 3^3 \cdot 4^2 = 27 \cdot 16 = 432$$

This matches our Matrix Tree Theorem computation exactly.

---

## **The number of spanning trees in K_{3,4} is 432.**

</details>

### SkillOS Solver (formal-proof dialect)

<details>
<summary>Click to expand (2,232 tokens)</summary>



```
GIVEN:
  P1: K_{3,4} is the complete bipartite graph with partition A = {a1,a2,a3}, B = {b1,b2,b3,b4}
  P2: |V| = 7, every vertex in A is adjacent to every vertex in B and vice versa
  P3: deg(a_i) = 4 for i ∈ {1,2,3}, deg(b_j) = 3 for j ∈ {1,2,3,4}

DERIVE:

  D1: L(K_{3,4}) =
       ⎡  4   0   0  -1  -1  -1  -1 ⎤
       ⎢  0   4   0  -1  -1  -1  -1 ⎥
       ⎢  0   0   4  -1  -1  -1  -1 ⎥
       ⎢ -1  -1  -1   3   0   0   0 ⎥
       ⎢ -1  -1  -1   0   3   0   0 ⎥
       ⎢ -1  -1  -1   0   0   3   0 ⎥
       ⎣ -1  -1  -1   0   0   0   3 ⎦
       rows/cols indexed (a1,a2,a3,b1,b2,b3,b4)
       BY definition (L = D - A, L_{ii} = deg(i), L_{ij} = -1 if ij ∈ E, 0 otherwise)

  D2: τ(K_{3,4}) = det(L_{11})
       where L_{11} is L with row 1 and column 1 deleted
       BY matrix_tree_theorem

  D3: L_{11} =
       ⎡  4   0  -1  -1  -1  -1 ⎤
       ⎢  0   4  -1  -1  -1  -1 ⎥
       ⎢ -1  -1   3   0   0   0 ⎥
       ⎢ -1  -1   0   3   0   0 ⎥
       ⎢ -1  -1   0   0   3   0 ⎥
       ⎣ -1  -1   0   0   0   3 ⎦
       rows/cols indexed (a2,a3,b1,b2,b3,b4)
       BY definition (delete row 1, column 1 from D1)

  D4: R3 ← R3 + (1/4)R1, R4 ← R4 + (1/4)R1, R5 ← R5 + (1/4)R1, R6 ← R6 + (1/4)R1
       ⎡  4     0    -1    -1    -1    -1   ⎤
       ⎢  0     4    -1    -1    -1    -1   ⎥
       ⎢  0    -1   11/4  -1/4  -1/4  -1/4 ⎥
       ⎢  0    -1   -1/4  11/4  -1/4  -1/4 ⎥
       ⎢  0    -1   -1/4  -1/4  11/4  -1/4 ⎥
       ⎣  0    -1   -1/4  -1/4  -1/4  11/4 ⎦
       det unchanged (row operations adding multiple of one row to another)
       BY cofactor_expansion (Gaussian elimination preserving determinant)

  D5: R3 ← R3 + (1/4)R2, R4 ← R4 + (1/4)R2, R5 ← R5 + (1/4)R2, R6 ← R6 + (1/4)R2
       ⎡  4    0     -1      -1      -1      -1    ⎤
       ⎢  0    4     -1      -1      -1      -1    ⎥
       ⎢  0    0    10/4    -2/4    -2/4    -2/4   ⎥
       ⎢  0    0    -2/4    10/4    -2/4    -2/4   ⎥
       ⎢  0    0    -2/4    -2/4    10/4    -2/4   ⎥
       ⎣  0    0    -2/4    -2/4    -2/4    10/4   ⎦
       i.e.,
       ⎡  4    0     -1      -1      -1      -1   ⎤
       ⎢  0    4     -1      -1      -1      -1   ⎥
       ⎢  0    0     5/2    -1/2    -1/2    -1/2  ⎥
       ⎢  0    0    -1/2     5/2    -1/2    -1/2  ⎥
       ⎢  0    0    -1/2    -1/2     5/2    -1/2  ⎥
       ⎣  0    0    -1/2    -1/2    -1/2     5/2  ⎦
       BY arithmetic

  D6: det(L_{11}) = 4 · 4 · det(M)
       where M =
       ⎡  5/2   -1/2   -1/2   -1/2 ⎤
       ⎢ -1/2    5/2   -1/2   -1/2 ⎥
       ⎢ -1/2   -1/2    5/2   -1/2 ⎥
       ⎣ -1/2   -1/2   -1/2    5/2 ⎦
       BY cofactor_expansion (block upper-triangular: det = product of diagonal block dets)

  D7: M = (1/2)(5I_4 - J_4 + I_4) is not the clearest form; instead:
       M = 3I_4 - (1/2)J_4 + (-1/2)I_4 ... 
       Rewrite: M = (1/2)(5I_4 - 𝟏𝟏ᵀ + I_4) — use direct eigenvalue approach:
       M has the form aI + bJ where a = 3, b = -1/2, and J = 𝟏𝟏ᵀ (rank-1)?
       No: M = (5/2)I_4 + (-1/2)(J_4 - I_4) = (5/2)I_4 - (1/2)J_4 + (1/2)I_4 = 3I_4 - (1/2)J_4
       where J_4 is the 4×4 all-ones matrix.
       Eigenvalues of J_4: λ = 4 (multiplicity 1), λ = 0 (multiplicity 3)
       Eigenvalues of M = 3I - (1/2)J_4:
         λ₁ = 3 - (1/2)(4) = 3 - 2 = 1    (multiplicity 1)
         λ₂ = 3 - (1/2)(0) = 3              (multiplicity 3)
       BY definition (eigenvalues of aI + bJ_n)

  D8: det(M) = λ₁ · λ₂³ = 1 · 3³ = 1 · 27 = 27
       BY arithmetic

  D9: det(L_{11}) = 4 · 4 · 27 = 432
       BY substitution (D6, D8)

  D10: τ(K_{3,4}) = 432
       BY substitution (D2, D9)

  D11: Verification via formula τ(K_{m,n}) = m^{n-1} · n^{m-1}:
       τ(K_{3,4}) = 3^{4-1} · 4^{3-1} = 3³ · 4² = 27 · 16 = 432 ✓
       BY arithmetic

QED: The number of spanning trees in K_{3,4} is 432.
```

</details>

### SkillOS Renderer (English translation)

<details>
<summary>Click to expand (402 tokens)</summary>

The complete bipartite graph K_{3,4} has 7 vertices split into two groups: A = {a1, a2, a3} and B = {b1, b2, b3, b4}, where every vertex in A connects to every vertex in B. This gives each A-vertex a degree of 4 and each B-vertex a degree of 3. To count the graph's spanning trees, the proof constructs the 7×7 Laplacian matrix L = D − A (degree matrix minus adjacency matrix), then applies Kirchhoff's matrix tree theorem: the number of spanning trees equals the determinant of any cofactor of L — here, the 6×6 submatrix L_{11} obtained by deleting the first row and column.

The proof evaluates det(L_{11}) through Gaussian elimination, using row operations to reduce it to a block upper-triangular form, factoring out the diagonal blocks to get det(L_{11}) = 4 · 4 · det(M), where M is a 4×4 matrix of the form 3I₄ − (1/2)J₄. Since J₄ (the all-ones matrix) has eigenvalues 4 and 0 with multiplicities 1 and 3, M has eigenvalues 1 and 3 with the same multiplicities, giving det(M) = 1 · 27 = 27. Thus τ(K_{3,4}) = 4 · 4 · 27 = 432, confirmed by the closed-form formula τ(K_{m,n}) = m^{n−1} · n^{m−1} = 3³ · 4² = 432.

</details>
