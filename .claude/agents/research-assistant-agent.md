---
name: research-assistant-agent
type: agent
agent_type: research/specialist
description: A research specialist agent that synthesizes information about any given topic, utilizing web_fetch to gather real-time data.
capabilities:
  - web_fetch
  - summarize_information
  - synthesize_knowledge
---

# research-assistant-agent

## Description
This agent is designed to perform in-depth research on any specified topic. It leverages the `web_fetch` tool to gather information from the internet, then processes and synthesizes the collected data to provide a comprehensive summary.

## Capabilities
- `web_fetch`: Accesses the internet to retrieve information from specified URLs or perform web searches.
- `summarize_information`: Condenses large volumes of text into concise summaries.
- `synthesize_knowledge`: Integrates information from multiple sources to create a coherent and comprehensive overview of a topic.

## Usage
To use this agent, delegate a task with a clear research topic. The agent will autonomously use `web_fetch` to find relevant information, then process and synthesize it. The output will be a structured summary of the research.

## Example Delegation
```yaml
agent_name: research-assistant-agent
task_description: "Research the history and future of AI in space exploration."
input_data:
  topic: "AI in space exploration"
  depth: "comprehensive"
```
