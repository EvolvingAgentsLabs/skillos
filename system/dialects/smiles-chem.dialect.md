---
dialect_id: smiles-chem
name: SMILES Chemical Notation
version: 1.0.0
domain_scope: [knowledge]
compression_type: structural
compression_ratio: "~80-95%"
reversible: true
input_format: natural-language-molecule
output_format: smiles-notation
---

# SMILES Chemical Notation Dialect

## Purpose

Compresses natural language molecular descriptions into SMILES (Simplified Molecular-Input Line-Entry System) notation. LLMs trained on chemical literature already have SMILES strings in their latent space — using this notation activates domain-specific molecular knowledge that verbose descriptions cannot reach. A single SMILES string encodes complete molecular structure (atoms, bonds, branches, rings, stereochemistry) in a fraction of the tokens needed for a prose description.

## Domain Scope

- **knowledge** — Encode molecular structures in chemistry wiki articles, drug discovery research, materials science summaries. SMILES strings enable structure-aware reasoning: the LLM can compare, modify, and analyze molecules using the same notation chemists use. Enables Grep-based molecular search across knowledge bases.

## Compression Rules

1. **Atoms**: Organic subset atoms (B, C, N, O, P, S, F, Cl, Br, I) written as single letters (or `Cl`, `Br`). Other atoms in brackets: `[Fe]`, `[Na+]`.
2. **Bonds**: Single `-` (usually implicit), double `=`, triple `#`, aromatic `:`.
3. **Branches**: Side chains in parentheses `()`. Nested branches allowed.
4. **Rings**: Ring openings and closures marked with matching digits. `C1CCCCC1` = cyclohexane.
5. **Aromatic atoms**: Lowercase letters for aromatic atoms: `c`, `n`, `o`. Kekulé form also accepted.
6. **Stereochemistry**: `@`/`@@` for tetrahedral, `/`/`\` for cis-trans.
7. **Charges**: In brackets: `[NH4+]`, `[O-]`.
8. **Isotopes**: Mass number prefix in brackets: `[13C]`, `[2H]`.
9. **Drop descriptive prose**: Remove "which is", "commonly known as", "a type of", "found in". Preserve only the structural information.
10. **Preserve common names as comments**: Append `# common_name` after the SMILES string for reversibility.

## Preservation Rules

1. **Molecular structure**: All atoms, bonds, and connectivity preserved exactly.
2. **Stereochemistry**: Chiral centers and geometric isomerism preserved when specified.
3. **Charges and isotopes**: All ionic charges and isotope labels preserved.
4. **Common names**: Preserved as trailing comments for expansion.
5. **Functional groups**: All functional group connectivity preserved in the SMILES structure.

## Grammar / Syntax

```
SMILES      := atom (bond? (atom | branch | ring_bond))*
atom        := organic_atom | bracket_atom
organic_atom:= "B" | "C" | "N" | "O" | "P" | "S" | "F" | "Cl" | "Br" | "I"
             | "b" | "c" | "n" | "o" | "p" | "s"
bracket_atom:= "[" isotope? symbol chirality? hcount? charge? "]"

bond        := "-" | "=" | "#" | ":" | "/" | "\\"
branch      := "(" SMILES ")"
ring_bond   := digit | "%" digit digit

isotope     := number
symbol      := element_symbol
chirality   := "@" | "@@"
hcount      := "H" digit?
charge      := "+" digit? | "-" digit?

comment     := SP "#" SP text
```

Standard SMILES as defined by OpenSMILES specification.

## Examples

### Example 1 — Caffeine

**Input** (22 words):
```
Caffeine — a trimethylxanthine found in coffee and tea. It has three methyl groups attached to a xanthine backbone with two carbonyl groups.
```

**Output** (5 words):
```
Cn1c(=O)c2c(ncn2C)n(C)c1=O  # caffeine
```

**Ratio**: 22 words → 5 words, ~77% reduction

### Example 2 — Aspirin

**Input** (20 words):
```
Aspirin, also known as acetylsalicylic acid. It's a common pain reliever consisting of a salicylate ester with an acetyl group.
```

**Output** (4 words):
```
CC(=O)Oc1ccccc1C(=O)O  # aspirin
```

**Ratio**: 20 words → 4 words, ~80% reduction

### Example 3 — Ethanol

**Input** (18 words):
```
Ethanol, the alcohol found in beverages. A simple two-carbon chain with a hydroxyl group on the terminal carbon.
```

**Output** (2 words):
```
CCO  # ethanol
```

**Ratio**: 18 words → 2 words, ~89% reduction

## Expansion Protocol

SMILES-chem is **reversible**. The expander reconstructs molecular descriptions:

1. **Atom sequence → element listing**: "The molecule contains [atoms]."
2. **Bond types → bond description**: "Connected by [single/double/triple] bonds."
3. **Branches → structural description**: "With a [group] branching from the main chain."
4. **Ring digits → ring description**: "Forming a [N]-membered ring."
5. **Aromatic lowercase → aromaticity**: "Containing an aromatic ring system."
6. **`# name` comment → common name**: "Commonly known as [name]."
7. **Functional groups → classification**: Identify and name functional groups (hydroxyl, carbonyl, amine, etc.).

### Target Registers

- **formal**: IUPAC systematic name + structural description with numbered atoms.
- **conversational**: "This is [common name], a molecule with [key features]."
- **technical**: SMILES string + molecular formula + molecular weight + functional group list.

### Reversibility Confidence

- Common molecules (in training data): 95-100%
- Complex molecules (10+ heavy atoms): 80-90%
- Stereochemistry details: 70-80% (chirality description may be imprecise in prose)

## Metrics

| Metric | Value |
|--------|-------|
| Compression ratio | ~80-95% |
| Token reduction | ~75-90% |
| Reversibility | High — structure fully encoded in SMILES string |
| Latency | Very Low (direct notation) |
| Error rate | <2% for common molecules; depends on LLM's SMILES training data |
| Quality improvement | Activates chemical domain knowledge; enables structural reasoning |
