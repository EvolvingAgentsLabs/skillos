---
dialect_id: dom-nav
name: DOM Navigation Dialect
version: 1.0.0
domain_scope: [orchestration, knowledge]
compression_type: structural
compression_ratio: "~90-97%"
reversible: false
input_format: html-dom
output_format: semantic-ui-tree
---

# DOM Navigation Dialect

## Purpose

Compresses raw HTML DOM into a minimal semantic UI tree containing only interactive elements and their identifiers. Solves the **small-model web browsing problem**: feeding raw HTML to a small LLM (Gemma 4B, Qwen 2.5) exhausts the context window with div noise, CSS classes, and non-interactive elements. The model cannot figure out which buttons to click or fields to fill.

The key insight: **a web agent only needs to see interactive elements and their labels.** By compiling the messy DOM into a flat list of clickable/typeable elements with numeric IDs, a small model can navigate any web page in under 500 tokens — regardless of how bloated the actual HTML is.

## Domain Scope

- **orchestration** — Used by web automation agents. The Cloud Compiler fetches and compresses the DOM, then sends the semantic tree to a local/small model agent for action selection.
- **knowledge** — Used during web research ingestion. Compress web page structure to identify navigation paths to content (pagination, "load more" buttons, menu structures).

## Compression Rules

1. **Strip non-interactive elements**: Remove all `<div>`, `<span>`, `<p>`, `<style>`, `<script>`, `<meta>`, `<link>`, `<header>`, `<footer>`, `<nav>` (structure), and all text content not associated with interactive elements.
2. **Extract interactive elements**: Keep only elements the user can interact with:
   - Buttons: `<button>`, `<input type="submit">`, `[role="button"]`
   - Inputs: `<input>`, `<textarea>`, `<select>`
   - Links: `<a href="...">` (with meaningful text or aria-label)
   - Checkboxes/Radios: `<input type="checkbox|radio">`
3. **Assign numeric IDs**: Each interactive element gets a sequential integer ID (`:N`).
4. **Element type prefix**: `[BTN:N]`, `[INP:N]`, `[LNK:N]`, `[SEL:N]`, `[CHK:N]`, `[RAD:N]`, `[TXT:N]`.
5. **Label extraction**: Use the visible text, `aria-label`, `placeholder`, `title`, or `name` attribute — whichever is most human-readable.
6. **State annotation**: `*` suffix for currently focused/active element. `(disabled)` for disabled elements. `(checked)` for checked checkboxes/radios.
7. **Value annotation**: For inputs with existing values, show `="current_value"`.
8. **Grouping**: Related elements (e.g., form fields) are indented under a `[FORM]` or `[GROUP]` header.
9. **Pagination**: `[PAGE N/M]` shows current page if detectable.
10. **Drop attributes**: Remove all CSS classes, inline styles, data-* attributes, event handlers.

## Preservation Rules

1. **Element identity**: The numeric ID must map consistently to the same DOM element within a session.
2. **Labels**: Visible text and aria-labels preserved exactly (may be truncated to 50 chars).
3. **Input types**: The type of each input must be preserved (text, password, email, number, etc.).
4. **Link destinations**: URLs preserved for links (may be abbreviated for display but full URL available on request).
5. **Element state**: Disabled, checked, selected states must be accurately reflected.
6. **Form structure**: Logical grouping of form elements must be preserved.
7. **Ordering**: Elements appear in DOM order (top-to-bottom, left-to-right reading order).

## Grammar / Syntax

```
UI_TREE     := (PAGE_HEADER "\n")? ELEMENT_LIST
PAGE_HEADER := "[PAGE" SP page_info "]"
page_info   := integer "/" integer | url_fragment

ELEMENT_LIST := (ELEMENT | GROUP) ("\n" (ELEMENT | GROUP))*
GROUP       := GROUP_HEADER "\n" (SP SP ELEMENT)+
GROUP_HEADER := "[FORM]" SP? label? | "[GROUP]" SP? label?

ELEMENT     := ELEM_TYPE ":" id "]" SP label STATE? VALUE?
ELEM_TYPE   := "[BTN" | "[INP" | "[LNK" | "[SEL" | "[CHK" | "[RAD" | "[TXT"
id          := positive_integer
label       := quoted_string | unquoted_text
STATE       := SP "*" | SP "(disabled)" | SP "(checked)"
VALUE       := SP "=" quoted_string

ACTION      := "[ACT]" SP verb SP id (SP argument)?
verb        := "CLICK" | "TYPE" | "SELECT" | "CHECK" | "UNCHECK" | "SCROLL" | "HOVER" | "WAIT"
argument    := quoted_string | number
```

### Element Type Prefixes

| Prefix | HTML Source | Example |
|--------|-----------|---------|
| `[BTN:N]` | `<button>`, `<input type="submit">`, `[role="button"]` | `[BTN:12] "Submit"` |
| `[INP:N]` | `<input type="text\|email\|password\|number">` | `[INP:14] "Email"` |
| `[LNK:N]` | `<a href="...">` | `[LNK:18] "Forgot Password"` |
| `[SEL:N]` | `<select>` | `[SEL:22] "Country"` |
| `[CHK:N]` | `<input type="checkbox">` | `[CHK:25] "Remember me"` |
| `[RAD:N]` | `<input type="radio">` | `[RAD:28] "Monthly billing"` |
| `[TXT:N]` | `<textarea>` | `[TXT:30] "Message"` |

### Action Verbs

| Verb | Meaning | Example |
|------|---------|---------|
| CLICK | Click/tap element | `[ACT] CLICK 12` |
| TYPE | Enter text into input | `[ACT] TYPE 14 "user@email.com"` |
| SELECT | Choose dropdown option | `[ACT] SELECT 22 "United States"` |
| CHECK | Check a checkbox | `[ACT] CHECK 25` |
| UNCHECK | Uncheck a checkbox | `[ACT] UNCHECK 25` |
| SCROLL | Scroll the page | `[ACT] SCROLL down 500` |
| HOVER | Hover over element | `[ACT] HOVER 18` |
| WAIT | Wait for element/time | `[ACT] WAIT 3000` |

## Examples

### Example 1 — Login page (50,000 tokens HTML → 6 lines)
**Input** (raw HTML, ~50,000 tokens):
```html
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport"...>
<title>Login - MyApp</title>
<link rel="stylesheet" href="/assets/css/main.min.css">
<script src="/assets/js/bundle.min.js"></script>
</head>
<body>
<div class="app-container">
  <header class="top-nav bg-white shadow-sm">
    <div class="container mx-auto flex items-center justify-between py-4">
      <img src="/logo.svg" class="h-8" alt="MyApp">
      <nav class="hidden md:flex space-x-6">
        <a href="/pricing" class="text-gray-600 hover:text-blue-600">Pricing</a>
        <a href="/docs" class="text-gray-600 hover:text-blue-600">Docs</a>
      </nav>
    </div>
  </header>
  <main class="flex items-center justify-center min-h-screen">
    <div class="bg-white rounded-xl shadow-lg p-8 w-96">
      <h1 class="text-2xl font-bold mb-6">Sign In</h1>
      <form action="/api/auth/login" method="POST">
        <div class="mb-4">
          <label for="email" class="block text-sm font-medium">Email</label>
          <input type="email" id="email" name="email" placeholder="you@example.com"
                 class="mt-1 block w-full rounded-md border p-2">
        </div>
        <!-- ... 200 more lines of nested divs, CSS, JS ... -->
```

**Output** (6 lines, ~80 tokens):
```
[LNK:1] "Pricing"
[LNK:2] "Docs"
[FORM] "Sign In"
  [INP:3] "Email" (email)
  [INP:4] "Password" (password)
  [CHK:5] "Remember me"
  [BTN:6] "Sign In"
[LNK:7] "Forgot Password"
[LNK:8] "Create Account"
```

**Ratio**: ~50,000 tokens → ~80 tokens = **~99.8% reduction**

**Agent response** (action):
```
[ACT] TYPE 3 "user@email.com"
[ACT] TYPE 4 "mypassword123"
[ACT] CHECK 5
[ACT] CLICK 6
```

### Example 2 — Search results page
**Input**: Complex Google-like search results page with ads, sidebar, pagination (~80,000 tokens HTML)

**Output** (15 lines, ~200 tokens):
```
[PAGE 1/12]
[INP:1] "Search" ="current query"
[BTN:2] "Search"
[LNK:3] "Result: How to use Python decorators - RealPython"
[LNK:4] "Result: Python Decorators 101 - PythonDocs"
[LNK:5] "Result: Understanding Decorators - Medium"
[LNK:6] "Result: Advanced Decorator Patterns - Stack Overflow"
[LNK:7] "Result: Decorator Best Practices - GitHub Blog"
[LNK:8] "Result: Python Decorator Tutorial - YouTube"
[LNK:9] "Result: Mastering Decorators - Dev.to"
[LNK:10] "Result: Decorator Cookbook - Python Wiki"
[LNK:11] "Next Page"
[LNK:12] "Page 2"
[LNK:13] "Page 3"
```

**Ratio**: ~80,000 tokens → ~200 tokens = **~99.7% reduction**

### Example 3 — E-commerce checkout form
**Input**: Complex checkout page with cart summary, shipping form, payment form (~30,000 tokens)

**Output**:
```
[GROUP] "Shipping"
  [INP:1] "Full Name"
  [INP:2] "Address Line 1"
  [INP:3] "Address Line 2"
  [INP:4] "City"
  [SEL:5] "State"
  [INP:6] "ZIP Code"
  [SEL:7] "Country" ="United States"
[GROUP] "Payment"
  [INP:8] "Card Number"
  [INP:9] "Expiration" (mm/yy)
  [INP:10] "CVV"
[CHK:11] "Save payment method"
[BTN:12] "Place Order - $47.99"
[LNK:13] "Back to Cart"
```

**Ratio**: ~30,000 tokens → ~180 tokens = **~99.4% reduction**

## Expansion Protocol

DOM-nav is **not reversible**. The original HTML structure, styling, layout, and non-interactive content are permanently discarded during compression. Expansion produces a **structured description** of the interactive elements, not the original HTML.

1. **`[BTN:N]` → button description**: "A button labeled '[label]' (element #N)."
2. **`[INP:N]` → input description**: "A [type] input field for '[label]' (element #N)."
3. **`[LNK:N]` → link description**: "A link to '[label]' (element #N)."
4. **`[FORM]` → form description**: "A form titled '[label]' containing the following fields..."
5. **`[ACT]` → action description**: "Click the [label] button" / "Type [value] into the [label] field."

### Information Loss

- All visual layout and styling (CSS, positioning, colors, fonts)
- Non-interactive text content (paragraphs, headings not associated with interactive elements)
- Images and media (unless they're interactive)
- JavaScript behavior and dynamic content
- Nested DOM structure and semantic HTML hierarchy
- Accessibility attributes beyond aria-label
- Form validation rules and constraints

## Metrics

| Metric | Value |
|--------|-------|
| Compression ratio | ~90-97% for simple pages, ~99%+ for complex pages |
| Token reduction | ~95-99.8% |
| Reversibility | None — structural transformation, HTML permanently discarded |
| Latency | Medium (DOM parsing + element extraction) |
| Error rate | <5% element misidentification (depends on HTML quality) |
| Quality improvement | Small models can navigate any page in <500 tokens context |
