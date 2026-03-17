---
name: algorithmic-art
description: Creating algorithmic art using p5.js with seeded randomness and interactive parameter exploration. Use this when users request creating art using code, generative art, algorithmic art, flow fields, or particle systems.
source: github:anthropics/skills
version: latest
installed: 2026-03-16
license: See LICENSE.txt
---

# Algorithmic Art Skill

Creates gallery-quality computational art through a two-step process:

1. **Algorithmic Philosophy Creation** — Define a generative aesthetic movement (.md)
2. **p5.js Implementation** — Express it as interactive generative art (.html + .js)

## Features
- Seeded randomness (Art Blocks pattern) for reproducible variations
- Interactive parameter controls (sliders, color pickers)
- Seed navigation (prev/next/random/jump)
- Self-contained HTML artifacts (works in any browser)
- Anthropic-branded viewer template

## Templates
- `templates/viewer.html` — Required starting point for all HTML artifacts
- `templates/generator_template.js` — Reference for p5.js best practices

## Usage
```
skillos execute: "Create algorithmic art inspired by ocean waves"
skillos execute: "Generate a flow field visualization"
skillos execute: "Create generative art with particle systems"
```
