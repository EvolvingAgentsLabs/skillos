---
schema_version: 1.0
domain: quantum-computing
dialect: formal-proof
project: Echo-Q Dialects
---

# Wiki Schema: Quantum Computing (formal-proof dialect)

## Purpose

This wiki documents quantum algorithmic primitives for the Echo-Q quantum cepstral analysis pipeline. All derivation sections use the `formal-proof` dialect.

## Dialect: formal-proof

All "How It Works" derivation sections MUST use:

```
GIVEN:
  G1. [premise]
  G2. [premise]
DERIVE:
  D1. [step] [BY rule_name]
  D2. [step] [BY D1, G2]
QED: [conclusion]
```

Symbolic operators: conjunction (AND), disjunction (OR), negation (NOT), implication (IMPLIES), universal quantifier, existential quantifier. Drop hedging language. Preserve all formulas, thresholds, and entity names. Every derivation step carries a [BY rule] annotation.

## Content Types

### concepts/
Quantum algorithmic primitives and techniques.
Required sections: Definition, Key Properties (table), How It Works (formal-proof blocks), Related Concepts (WikiLinks), Open Questions.

### entities/
Papers, researchers, organizations.
Required sections: Metadata (authors, year, venue), Summary, Key Contributions, Referenced By (WikiLinks).

### summaries/
Per-source summaries (auto-generated from raw/).

### queries/
Filed Q&A outputs (compounding loop).

## Structure Rules

1. Every concept page MUST have YAML frontmatter with: concept, type, domain, dialect, related, sources
2. Every concept MUST link to >= 2 related concepts via [[WikiLinks]]
3. Every concept MUST contain >= 1 formal-proof block (GIVEN/DERIVE/QED)
4. Key Properties MUST be in table format
5. Definitions MUST include the primary mathematical formula
6. Entity pages MUST list all concept pages that reference them

## Cross-Reference Convention

- Concept-to-concept: `[[concept-name]]` (e.g., `[[block-encoding]]`)
- Concept-to-entity: `[[entities/entity-name]]` (e.g., `[[entities/grand-unification-of-quantum-algorithms]]`)
- All links are bidirectional in intent (target should link back)
