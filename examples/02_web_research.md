---
name: web-research
complexity: beginner
pattern: sequential-two-agent
estimated_cost: <$0.05
---

# Web Research: Fetch, Summarize, Save

Demonstrates live web fetching and structured output generation.

## Goal

```bash
skillos execute: "Fetch the Hacker News front page, extract the top 10 story titles and URLs, and save as a formatted Markdown list with brief descriptions"
```

## What Happens

1. **FetchAgent** calls `WebFetch` on `https://news.ycombinator.com`
2. **WriterAgent** parses the HTML, extracts story titles and links
3. Output saved as a clean Markdown file with numbered list

## Expected Output

```
projects/Project_hacker_news/output/top_stories.md
```

```markdown
# Hacker News Top Stories — [Date]

1. **[Story Title]** ([domain])
   [Brief description or subtitle]
   [URL]

2. **[Story Title]** ([domain])
   ...
```

## Variations

```bash
# Research a specific topic
skillos execute: "Search for recent news about WebAssembly, fetch the top 3 articles, and write a 500-word summary of the current state of the technology"

# Fetch and compare
skillos execute: "Fetch the homepages of GitHub, GitLab, and Bitbucket, then write a comparison of how each positions itself"

# Extract structured data from a page
skillos execute: "Fetch https://pypi.org/project/requests/ and extract: version, description, dependencies, and download stats into a structured Markdown doc"
```

## Learning Objectives

- Use `WebFetch` through a SkillOS agent
- See parallel vs sequential agent patterns
- Understand how agents pass data through state files
