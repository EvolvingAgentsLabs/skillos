---
name: hello-world
complexity: beginner
pattern: single-agent
estimated_cost: <$0.01
---

# Hello World: Your First SkillOS Execution

The simplest possible SkillOS execution — a single agent writes a file.

## Goal

```bash
skillos execute: "Write a hello_world.txt file that contains a friendly greeting and today's date"
```

## What Happens

1. SkillOS boots and displays the welcome banner
2. SystemAgent receives the goal
3. A single Write tool call creates the output file
4. Execution logged to memory

## Expected Output

```
projects/Project_hello_world/output/hello_world.txt
```

Contents:
```
Hello, World! 🌍

Today is [date].

Welcome to SkillOS — where markdown becomes intelligence.
```

## What to Try Next

After this works, try adding complexity:

```bash
# Add a web fetch
skillos execute: "Fetch the current time from worldtimeapi.org and write a greeting with the exact timestamp"

# Add file reading
skillos execute: "Read examples/01_hello_world.md and write a summary of what it demonstrates"
```

## Learning Objectives

- Understand the basic `skillos execute:` invocation pattern
- See how SkillOS creates project structure automatically
- Observe memory logging in `projects/Project_hello_world/memory/`
