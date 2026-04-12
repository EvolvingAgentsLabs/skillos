# Math Benchmark Report: Formal Proof Dialect

**Generated**: 2026-04-12 16:40
**Task**: Calculate spanning trees of K_{3,4} via Matrix Tree Theorem
**Correct Answer**: 432

## Summary

| Metric | Plain Claude | SkillOS Solver | SkillOS Solver+Renderer |
|---|---|---|---|
| Output tokens | 4,632 | 1,976 | 2,370 |
| Token reduction | baseline | **-57.3%** | **-48.8%** |
| Cost (USD) | $0.1783 | $0.0706 | $0.1126 |
| Duration (s) | 58.9 | 29.3 | 40.7 |
| Turns | 1 | 1 | 2 |

## Quality Verification (Automated)

| Check (pts) | Plain Claude | SkillOS Solver |
|---|---|---|
| Answer = 432 (50) | YES | YES |
| Laplacian matrix (10) | No | No |
| Cofactor/minor (10) | No | Yes |
| Determinant calc (10) | Yes | Yes |
| Intermediate 27x16 (20) | Yes | Yes |
| **Total score** | **80/100** | **90/100** |

## Key Findings

- **Token reduction (solver only)**: 57.3% fewer output tokens
- **Token reduction (with renderer)**: 48.8% fewer even with English translation step
- **Math accuracy**: Plain CORRECT, SkillOS CORRECT
- **Cognitive Scaffolding**: Formal-proof notation forces step-by-step computation, maintaining arithmetic accuracy

## Raw Outputs

### Plain Claude

<details>
<summary>Click to expand (4,632 tokens)</summary>

Let me work through the Gaussian elimination by hand with exact arithmetic.

### Step-by-step Gaussian elimination on L₁₁

Starting matrix:

```
     c1   c2   c3   c4   c5   c6
R1 [  4    0   -1   -1   -1   -1 ]
R2 [  0    4   -1   -1   -1   -1 ]
R3 [ -1   -1    3    0    0    0 ]
R4 [ -1   -1    0    3    0    0 ]
R5 [ -1   -1    0    0    3    0 ]
R6 [ -1   -1    0    0    0    3 ]
```

**Pivot on R1, c1 (pivot = 4):**

Eliminate entries in column 1. Only R3–R6 have nonzero entries (-1) in column 1.

- R3 → R3 + (1/4)R1
- R4 → R4 + (1/4)R1
- R5 → R5 + (1/4)R1
- R6 → R6 + (1/4)R1

```
R3: [0, -1,    3-1/4,  0-1/4,  0-1/4,  0-1/4] = [0, -1,  11/4, -1/4, -1/4, -1/4]
R4: [0, -1,   0-1/4,  3-1/4,  0-1/4,  0-1/4] = [0, -1, -1/4,  11/4, -1/4, -1/4]
R5: [0, -1,   0-1/4,  0-1/4,  3-1/4,  0-1/4] = [0, -1, -1/4, -1/4,  11/4, -1/4]
R6: [0, -1,   0-1/4,  0-1/4,  0-1/4,  3-1/4] = [0, -1, -1/4, -1/4, -1/4,  11/4]
```

After step 1:

```
R1 [  4    0    -1     -1     -1     -1   ]
R2 [  0    4    -1     -1     -1     -1   ]
R3 [  0   -1   11/4   -1/4   -1/4   -1/4 ]
R4 [  0   -1   -1/4   11/4   -1/4   -1/4 ]
R5 [  0   -1   -1/4   -1/4   11/4   -1/4 ]
R6 [  0   -1   -1/4   -1/4   -1/4   11/4 ]
```

**Pivot on R2, c2 (pivot = 4):**

Eliminate column 2 in R3–R6 (each has -1 in column 2).

- R3 → R3 + (1/4)R2
- R4 → R4 + (1/4)R2
- R5 → R5 + (1/4)R2
- R6 → R6 + (1/4)R2

```
R3: [0, 0, 11/4-1/4, -1/4-1/4, -1/4-1/4, -1/4-1/4] = [0, 0, 10/4, -2/4, -2/4, -2/4]
   = [0, 0, 5/2, -1/2, -1/2, -1/2]

R4: [0, 0, -1/4-1/4, 11/4-1/4, -1/4-1/4, -1/4-1/4] = [0, 0, -1/2, 5/2, -1/2, -1/2]
R5: [0, 0, -1/2, -1/2, 5/2, -1/2]
R6: [0, 0, -1/2, -1/2, -1/2, 5/2]
```

After step 2, the lower-right 4×4 block is:

```
     c3     c4     c5     c6
R3 [ 5/2   -1/2   -1/2   -1/2 ]
R4 [-1/2    5/2   -1/2   -1/2 ]
R5 [-1/2   -1/2    5/2   -1/2 ]
R6 [-1/2   -1/2   -1/2    5/2 ]
```

**Pivot on R3, c3 (pivot = 5/2):**

Eliminate column 3 in R4–R6. Each has -1/2, so multiplier = (-1/2)/(5/2) = -1/5.

- R4 → R4 + (1/5)R3
- R5 → R5 + (1/5)R3
- R6 → R6 + (1/5)R3

For R4:
- c4: 5/2 + (1/5)(-1/2) = 5/2 - 1/10 = 24/10 = **12/5**
- c5: -1/2 + (1/5)(-1/2) = -1/2 - 1/10 = -6/10 = **-3/5**
- c6: -1/2 + (1/5)(-1/2) = **-3/5**

By symmetry, R5 and R6 have the same pattern:

```
     c4     c5     c6
R4 [12/5   -3/5   -3/5 ]
R5 [-3/5   12/5   -3/5 ]
R6 [-3/5   -3/5   12/5 ]
```

**Pivot on R4, c4 (pivot = 12/5):**

Multiplier for R5, R6: (-3/5)/(12/5) = -3/12 = -1/4.

- R5 → R5 + (1/4)R4
- R6 → R6 + (1/4)R4

For R5:
- c5: 12/5 + (1/4)(-3/5) = 12/5 - 3/20 = 48/20 - 3/20 = **45/20 = 9/4**
- c6: -3/5 + (1/4)(-3/5) = -3/5 - 3/20 = -12/20 - 3/20 = **-15/20 = -3/4**

For R6:
- c5: -3/5 + (1/4)(-3/5) = **-3/4**
- c6: 12/5 + (1/4)(-3/5) = **9/4**

Remaining 2×2 block:

```
     c5     c6
R5 [ 9/4   -3/4 ]
R6 [-3/4    9/4 ]
```

**Pivot on R5, c5 (pivot = 9/4):**

Multiplier for R6: (-3/4)/(9/4) = -1/3.

- R6 → R6 + (1/3)R5

R6, c6: 9/4 + (1/3)(-3/4) = 9/4 - 3/12 = 9/4 - 1/4 = **8/4 = 2**

**Final pivot:** R6, c6 = **2**.

### Collecting the determinant

The determinant is the product of all pivots:

```
det(L₁₁) = 4 × 4 × 5/2 × 12/5 × 9/4 × 2
```

Let me compute step by step:

| Step | Multiplication | Running product |
|------|---------------|-----------------|
| 4 × 4 | | **16** |
| × 5/2 | 16 × 5/2 | **40** |
| × 12/5 | 40 × 12/5 | **96** |
| × 9/4 | 96 × 9/4 | **216** |
| × 2 | 216 × 2 | **432** |

## 4. Final Answer

$$\boxed{t(K_{3,4}) = 432}$$

### Verification via the known formula

For complete bipartite graphs, there is a closed-form result:

$$t(K_{m,n}) = m^{n-1} \cdot n^{m-1}$$

With m = 3, n = 4:

$$t(K_{3,4}) = 3^{4-1} \cdot 4^{3-1} = 3^3 \cdot 4^2 = 27 \cdot 16 = 432 \checkmark$$

The Matrix Tree Theorem computation agrees exactly with the formula. **The number of spanning trees of K_{3,4} is 432.**

</details>

### SkillOS Solver (formal-proof dialect)

<details>
<summary>Click to expand (1,976 tokens)</summary>



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
       [BY definition: L_{ii} = deg(i), L_{ij} = -1 if {i,j} ∈ E, else 0]

  D2: L_{11} := L with row 1 and column 1 deleted =
       ⎡  4   0  -1  -1  -1  -1 ⎤
       ⎢  0   4  -1  -1  -1  -1 ⎥
       ⎢ -1  -1   3   0   0   0 ⎥
       ⎢ -1  -1   0   3   0   0 ⎥
       ⎢ -1  -1   0   0   3   0 ⎥
       ⎣ -1  -1   0   0   0   3 ⎦
       [BY definition: cofactor matrix deletion of row 1, column 1]

  D3: τ(K_{3,4}) = det(L_{11})
       [BY matrix_tree_theorem]

  D4: R3 ← R3 + (1/4)R1, R4 ← R4 + (1/4)R1, R5 ← R5 + (1/4)R1, R6 ← R6 + (1/4)R1
       ⎡  4    0   -1    -1    -1    -1   ⎤
       ⎢  0    4   -1    -1    -1    -1   ⎥
       ⎢  0   -1   11/4  -1/4  -1/4  -1/4 ⎥
       ⎢  0   -1   -1/4  11/4  -1/4  -1/4 ⎥
       ⎢  0   -1   -1/4  -1/4  11/4  -1/4 ⎥
       ⎣  0   -1   -1/4  -1/4  -1/4  11/4 ⎦
       [BY cofactor_expansion: row reduction preserves determinant]

  D5: R3 ← R3 + (1/4)R2, R4 ← R4 + (1/4)R2, R5 ← R5 + (1/4)R2, R6 ← R6 + (1/4)R2
       ⎡  4   0    -1     -1     -1     -1    ⎤
       ⎢  0   4    -1     -1     -1     -1    ⎥
       ⎢  0   0    10/4   -2/4   -2/4   -2/4  ⎥
       ⎢  0   0    -2/4   10/4   -2/4   -2/4  ⎥
       ⎢  0   0    -2/4   -2/4   10/4   -2/4  ⎥
       ⎣  0   0    -2/4   -2/4   -2/4   10/4  ⎦
       [BY cofactor_expansion: row reduction preserves determinant]

  D6: Simplify lower-right 4×4 block: entries = 5/2 on diagonal, -1/2 off diagonal
       M = ⎡  5/2  -1/2  -1/2  -1/2 ⎤
           ⎢ -1/2   5/2  -1/2  -1/2 ⎥
           ⎢ -1/2  -1/2   5/2  -1/2 ⎥
           ⎣ -1/2  -1/2  -1/2   5/2 ⎦
       [BY arithmetic: 10/4 = 5/2, -2/4 = -1/2]

  D7: M = (1/2)(3·I₄ + J₄) where J₄ = all-ones 4×4 matrix, I₄ = identity
       Equivalently: M = (3/2)I₄ + (1/2)J₄ — verify: diagonal = 3/2 + 1/2·1 ≠ 5/2 ✗
       Correction: M = 3I₄ - (1/2)J₄ + … 
       Direct: M = aI₄ + bJ₄ where a + b = 5/2 (diagonal), b = -1/2 (off-diagonal)
       ⟹ a = 3, b = -1/2
       M = 3I₄ + (-1/2)J₄
       [BY arithmetic]

  D8: Eigenvalues of J₄: λ = 4 (multiplicity 1), λ = 0 (multiplicity 3)
       Eigenvalues of M = 3I₄ - (1/2)J₄:
         λ₁ = 3 - (1/2)(4) = 3 - 2 = 1    (multiplicity 1)
         λ₂ = 3 - (1/2)(0) = 3              (multiplicity 3)
       [BY arithmetic: eigenvalues of aI + bJ are a + bn for J-eigval n]

  D9: det(M) = 1 · 3³ = 27
       [BY arithmetic: determinant = product of eigenvalues]

  D10: det(L_{11}) = det(upper-left 2×2 block of triangular form) · det(M)
        = 4 · 4 · det(M)
        = 16 · 27
        = 432
       [BY arithmetic: det of block upper-triangular = product of block determinants]

  D11: Verification by known formula: τ(K_{m,n}) = m^{n-1} · n^{m-1}
        τ(K_{3,4}) = 3^{4-1} · 4^{3-1} = 3³ · 4² = 27 · 16 = 432
       [BY substitution: standard bipartite spanning tree formula]

QED: τ(K_{3,4}) = det(L_{11}) = 432
```

</details>

### SkillOS Renderer (English translation)

<details>
<summary>Click to expand (394 tokens)</summary>

The complete bipartite graph K_{3,4} has 7 vertices split into two groups: A = {a1, a2, a3} and B = {b1, b2, b3, b4}, where every vertex in A is connected to every vertex in B. This gives each A-vertex a degree of 4 and each B-vertex a degree of 3. To count the graph's spanning trees, the proof constructs the 7×7 Laplacian matrix L(K_{3,4}) — with degrees on the diagonal and −1 for each edge — then deletes row 1 and column 1 to form the 6×6 cofactor matrix L_{11}. By the Matrix Tree Theorem, the number of spanning trees equals det(L_{11}).

The determinant is computed through row reduction. Two rounds of elimination zero out the first two columns of the bottom four rows, producing a block upper-triangular matrix: a 2×2 diagonal block with entries 4 and 4, and a 4×4 block M with 5/2 on the diagonal and −1/2 off-diagonal. Decomposing M as 3I₄ + (−1/2)J₄ reveals its eigenvalues — 1 (multiplicity 1) and 3 (multiplicity 3) — giving det(M) = 1 · 3³ = 27. Multiplying the block determinants yields 4 · 4 · 27 = 432, confirmed by the known formula τ(K_{m,n}) = m^{n−1} · n^{m−1} = 3³ · 4² = 432.

</details>
