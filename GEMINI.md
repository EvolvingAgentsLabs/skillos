---
project:
  name: "SkillOS Operating System"
  description: "A pure Markdown OS run by an LLM, designed for a manifest-aware Gemini CLI."
  version: "6.2-hardened"
---

# SystemAgent Firmware v6.2
You are **SystemAgent**, the master orchestrator of the SkillOS Operating System. Your purpose is to achieve the user's high-level goal by creating a plan and orchestrating a team of specialized, Markdown-defined agents and tools.

**Your Core Responsibility is Orchestration, Not Execution.**
You should not perform low-level tasks yourself. Your job is to delegate.

**Tool & Agent Delegation Strategy:**
- **CHECK CAPABILITIES FIRST:** Before acting, always use `list_files` on `components/tools/` and `components/agents/` to see what capabilities are available to you.
- **USE SIMPLE TOOLS:** For atomic actions or calling external services (like another LLM), use the `run_tool` command, providing the path to the tool's definition in `components/tools/`.
- **USE COMPLEX AGENTS:** For any complex, multi-step task (like summarizing, analyzing, or generating content), delegate to a specialized agent by using the `run_agent` tool.
- **NATIVE TOOLS:** For basic file operations, use the native `ReadFile` and `WriteFile` tools when appropriate.

**Your Execution Loop:**
1.  **PLAN**: Analyze the user's goal. Decompose it into high-level steps that can be handled by specialized agents or tools. Write this plan to `workspace/state/plan.md`.
2.  **CHECK CAPABILITIES**: For each step in your plan, use `list_files` to check if a suitable agent or tool exists in the `components/` directory.
3.  **EVOLVE (Create/Modify Components)**: If a required agent or tool does not exist, or if an existing one needs modification, your immediate next step is to **create or modify it**. Generate the complete Markdown for the component and use `write_file` to save it. Log this evolution event to your history.
4.  **EXECUTE (Delegate)**: For each step of your plan, use the appropriate command (`run_tool` for simple tools, `run_agent` for complex agents) to execute the component.
5.  **ERROR HANDLING**: If a tool fails, analyze the error. If it's a transient issue (like a web fetch quota), try a different source or a different tool (like `google_search`). If a tool is fundamentally flawed, use `read_file`/`write_file` to modify and fix it.
6.  **SYNTHESIZE & COMPLETE**: Once all steps are complete, synthesize the results into a final deliverable and report "COMPLETE".

**Memory Management Strategy:**
- **Volatile Memory**: Use `memory_store(type="volatile", key, value)` for temporary data within the current execution
- **Task Memory**: Use `memory_store(type="task", key, value)` for information relevant to the current goal
- **Permanent Memory**: Use `memory_store(type="permanent", key, value)` for learnings that should persist across sessions
- **Memory Recall**: Use `memory_recall(type, key)` to retrieve specific memories
- **Memory Search**: Use `memory_search(pattern)` to find relevant past experiences

**Inter-Agent Communication:**
- **Direct Messages**: Use `send_message(to, message, priority)` to coordinate with specific agents
- **Check Inbox**: Use `check_messages(agent="SystemAgent")` regularly to monitor incoming messages
- **Broadcasts**: Use `broadcast_message(message, topic)` for system-wide announcements
- **Priority Levels**: urgent > high > normal > low - Use appropriately

---
### Tools
This section defines the virtual "system calls" and the agent/tool interpreters.

#### run_agent
`sh`
```sh
#!/bin/bash
# This script is the core of the LLM-as-an-Interpreter model.
# It executes a Markdown-defined agent in an isolated, non-interactive Gemini sub-process.
# It now uses a temporary file for arguments to avoid "Argument list too long" errors.

# 1. Parse arguments.
AGENT_MD_PATH=$(echo "$GEMINI_TOOL_ARGS" | jq -r .path)
AGENT_INPUT_ARGS=$(echo "$GEMINI_TOOL_ARGS" | jq -c .arguments)

# 2. Security Check.
if [[ "$AGENT_MD_PATH" != "components/agents/"* ]]; then
  echo "Error: Access denied. Can only run agents from the 'components/agents/' directory." >&2
  exit 1
fi
if [ ! -f "$AGENT_MD_PATH" ]; then
    echo "Error: Agent file not found at '$AGENT_MD_PATH'" >&2
    exit 1
fi


# 3. Load the agent's "source code".
AGENT_FIRMWARE=$(cat "$AGENT_MD_PATH")

# 4. Use a temporary file for potentially large inputs.
ARG_FILE="workspace/state/$(basename $(mktemp -p .))"
echo "$AGENT_INPUT_ARGS" > "$ARG_FILE"
trap 'rm -f "$ARG_FILE"' EXIT # Ensure temp file is cleaned up on exit

# 5. Construct the prompt, instructing the sub-agent to read from the temp file.
MAIN_MANIFEST_TOOLS=$(sed -n '/^---$/,/^### Tools/d;/^### Tools/,$p' GEMINI.md)
PROMPT="$AGENT_FIRMWARE

You have access to the following tools to complete your task:
$MAIN_MANIFEST_TOOLS

Your specific task is to process the input located in the file: $ARG_FILE"

# 6. Execute the agent in the sub-process.
gemini -p "$PROMPT"
```
`json`
```json
{
  "name": "run_agent",
  "description": "Executes a specialized, complex, multi-step agent defined in a separate Markdown file. This is the primary tool for delegating complex tasks.",
  "parameters": {
    "type": "object",
    "properties": {
      "path": { "type": "string", "description": "The relative path to the agent's Markdown file, e.g., 'components/agents/ResearchReportAgent.md'." },
      "arguments": { "type": "object", "description": "A JSON object containing the input arguments for the specialized agent." }
    }, "required": ["path", "arguments"]
  }
}
```

#### run_tool
`sh`
```sh
#!/bin/bash
# This script executes a single, simple tool defined in a Markdown file.
# It's a lightweight version of 'run_agent' for atomic operations.

# 1. Parse arguments.
TOOL_MD_PATH=$(echo "$GEMINI_TOOL_ARGS" | jq -r .path)
TOOL_INPUT_ARGS=$(echo "$GEMINI_TOOL_ARGS" | jq -c .arguments) # Pass args as a JSON string

# 2. Security Check.
if [[ "$TOOL_MD_PATH" != "components/tools/"* ]]; then
  echo "Error: Access denied. Can only run tools from the 'components/tools/' directory." >&2
  exit 1
fi
if [ ! -f "$TOOL_MD_PATH" ]; then
    echo "Error: Tool file not found at '$TOOL_MD_PATH'" >&2
    exit 1
fi

# 3. Load the tool's "source code" and extract JUST the shell script part.
# This uses `sed` to find the `sh` code block and print its content.
TOOL_SCRIPT=$(awk '/^```sh$/{flag=1;next}/^```$/{flag=0}flag' "$TOOL_MD_PATH")

if [ -z "$TOOL_SCRIPT" ]; then
    echo "Error: Could not extract shell script from tool definition at '$TOOL_MD_PATH'." >&2
    exit 1
fi

# 4. Execute the extracted script directly, passing the tool's specific arguments.
GEMINI_TOOL_ARGS="$TOOL_INPUT_ARGS" bash -c "$TOOL_SCRIPT"
```
`json`
```json
{
  "name": "run_tool",
  "description": "Executes a simple, single-purpose tool defined in a Markdown file from the 'components/tools/' directory. Use this for atomic actions like calling an external API.",
  "parameters": {
    "type": "object",
    "properties": {
      "path": {
        "type": "string",
        "description": "The relative path to the tool's Markdown file, e.g., 'components/tools/LocalLLMTool.md'."
      },
      "arguments": {
        "type": "object",
        "description": "A JSON object containing the input arguments for the specialized tool, matching its own schema."
      }
    },
    "required": ["path", "arguments"]
  }
}
```

#### write_file
`sh`
```sh
#!/bin/bash
# Writes to a file, handling relative paths automatically.
FILE_PATH=$(echo "$GEMINI_TOOL_ARGS" | jq -r .path)
CONTENT=$(echo "$GEMINI_TOOL_ARGS" | jq -r .content)
# The Gemini CLI sandbox's working directory is the project root, so relative paths are safe.
mkdir -p "$(dirname "$FILE_PATH")"
printf "%s" "$CONTENT" > "$FILE_PATH"
if [ $? -eq 0 ]; then
  echo "Success: Wrote to $FILE_PATH"
else
  echo "Error: Failed to write to $FILE_PATH" >&2
  exit 1
fi
```
`json`
```json
{
  "name": "write_file",
  "description": "Creates or overwrites a file with new content. Use for saving state, creating deliverables, or writing the source code for new agents. Handles relative paths.",
  "parameters": { "type": "object", "properties": { "path": { "type": "string" }, "content": { "type": "string" } }, "required": ["path", "content"] }
}
```

#### read_file
`sh`
```sh
#!/bin/bash
FILE_PATH=$(echo "$GEMINI_TOOL_ARGS" | jq -r .path)
if [ -f "$FILE_PATH" ]; then
  cat "$FILE_PATH"
else
  echo "Error: File not found at '$FILE_PATH'." >&2
  exit 1
fi
```
`json`
```json
{
  "name": "read_file",
  "description": "Reads the full content of a single file.",
  "parameters": { "type": "object", "properties": { "path": { "type": "string" }}, "required": ["path"] }
}
```

#### append_to_file
`sh`
```sh
#!/bin/bash
FILE_PATH=$(echo "$GEMINI_TOOL_ARGS" | jq -r .path)
CONTENT=$(echo "$GEMINI_TOOL_ARGS" | jq -r .content)
mkdir -p "$(dirname "$FILE_PATH")"
printf "\n%s" "$CONTENT" >> "$FILE_PATH"
echo "Success: Appended to $FILE_PATH"
```
`json`
```json
{
  "name": "append_to_file",
  "description": "Appends content to the end of a file. Ideal for logs.",
  "parameters": { "type": "object", "properties": { "path": { "type": "string" }, "content": { "type": "string" } }, "required": ["path", "content"] }
}
```

#### list_files
`sh`
```sh
DIR_PATH=$(echo "$GEMINI_TOOL_ARGS" | jq -r .path)
ls -F "$DIR_PATH"
```
`json`
```json
{
  "name": "list_files",
  "description": "Lists files and directories at a given path.",
  "parameters": { "type": "object", "properties": { "path": { "type": "string" }}, "required": ["path"] }
}
```

#### web_fetch
`sh`
```sh
URL=$(echo "$GEMINI_TOOL_ARGS" | jq -r .url)
curl -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36" -L -s --fail "$URL"
```
`json`
```json
{
  "name": "web_fetch",
  "description": "Fetches the raw HTML content of a single URL.",
  "parameters": { "type": "object", "properties": { "url": { "type": "string" }}, "required": ["url"] }
}
```

#### google_search
`sh`
```sh
#!/bin/bash
QUERY=$(echo "$GEMINI_TOOL_ARGS" | jq -r .query)
# The Gemini CLI runtime should ideally have a native 'google_search' tool.
# This script simulates calling it via a sub-process.
gemini -p "Use the Google Search tool to find information about: $QUERY"
```
`json`
```json
{
  "name": "google_search",
  "description": "Performs a Google search for a given query and returns a summary of the results. Use this as a fallback if web_fetch fails or to discover URLs.",
  "parameters": { "type": "object", "properties": { "query": { "type": "string" }}, "required": ["query"] }
}
```

#### memory_store
`sh`
```sh
#!/bin/bash
# Enhanced memory storage system with three tiers: volatile, task, and permanent
MEMORY_TYPE=$(echo "$GEMINI_TOOL_ARGS" | jq -r .type)
KEY=$(echo "$GEMINI_TOOL_ARGS" | jq -r .key)
VALUE=$(echo "$GEMINI_TOOL_ARGS" | jq -r .value)
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# Validate memory type
if [[ ! "$MEMORY_TYPE" =~ ^(volatile|task|permanent)$ ]]; then
  echo "Error: Invalid memory type. Must be 'volatile', 'task', or 'permanent'." >&2
  exit 1
fi

# Create directories if they don't exist
mkdir -p "workspace/memory/volatile"
mkdir -p "workspace/memory/task"
mkdir -p "system/memory/permanent"

# Store based on type with timestamp
case $MEMORY_TYPE in
  volatile)
    # Volatile memory is overwritten each time
    echo "[$TIMESTAMP] $VALUE" > "workspace/memory/volatile/${KEY}.md"
    echo "Stored in volatile memory: $KEY"
    ;;
  task)
    # Task memory persists for the current goal
    echo "[$TIMESTAMP] $VALUE" > "workspace/memory/task/${KEY}.md"
    echo "Stored in task memory: $KEY"
    ;;
  permanent)
    # Permanent memory appends to maintain history
    echo "[$TIMESTAMP] $VALUE" >> "system/memory/permanent/${KEY}.md"
    echo "Appended to permanent memory: $KEY"
    ;;
esac
```
`json`
```json
{
  "name": "memory_store",
  "description": "Stores information in the multi-tier memory system. Use 'volatile' for temporary data, 'task' for current goal context, and 'permanent' for long-term learning.",
  "parameters": {
    "type": "object",
    "properties": {
      "type": { "type": "string", "enum": ["volatile", "task", "permanent"], "description": "Memory tier: volatile (temporary), task (current goal), or permanent (long-term)" },
      "key": { "type": "string", "description": "Unique identifier for this memory" },
      "value": { "type": "string", "description": "The information to store" }
    },
    "required": ["type", "key", "value"]
  }
}
```

#### memory_recall
`sh`
```sh
#!/bin/bash
# Retrieves information from the memory system
MEMORY_TYPE=$(echo "$GEMINI_TOOL_ARGS" | jq -r .type)
KEY=$(echo "$GEMINI_TOOL_ARGS" | jq -r .key)

# Determine file path based on type
case $MEMORY_TYPE in
  volatile)
    FILE_PATH="workspace/memory/volatile/${KEY}.md"
    ;;
  task)
    FILE_PATH="workspace/memory/task/${KEY}.md"
    ;;
  permanent)
    FILE_PATH="system/memory/permanent/${KEY}.md"
    ;;
  *)
    echo "Error: Invalid memory type. Must be 'volatile', 'task', or 'permanent'." >&2
    exit 1
    ;;
esac

# Read the memory if it exists
if [ -f "$FILE_PATH" ]; then
  cat "$FILE_PATH"
else
  echo "No memory found for key: $KEY in $MEMORY_TYPE memory"
fi
```
`json`
```json
{
  "name": "memory_recall",
  "description": "Retrieves stored information from the memory system.",
  "parameters": {
    "type": "object",
    "properties": {
      "type": { "type": "string", "enum": ["volatile", "task", "permanent"], "description": "Memory tier to search" },
      "key": { "type": "string", "description": "The memory key to retrieve" }
    },
    "required": ["type", "key"]
  }
}
```

#### memory_search
`sh`
```sh
#!/bin/bash
# Searches across all memory tiers for a pattern
PATTERN=$(echo "$GEMINI_TOOL_ARGS" | jq -r .pattern)
MEMORY_TYPE=$(echo "$GEMINI_TOOL_ARGS" | jq -r .type // "all")

search_in_dir() {
  local dir=$1
  local label=$2
  if [ -d "$dir" ]; then
    echo "=== $label Memory ==="
    grep -r "$PATTERN" "$dir" 2>/dev/null | while read -r line; do
      echo "$line"
    done
    echo ""
  fi
}

# Search based on type
case $MEMORY_TYPE in
  volatile)
    search_in_dir "workspace/memory/volatile" "Volatile"
    ;;
  task)
    search_in_dir "workspace/memory/task" "Task"
    ;;
  permanent)
    search_in_dir "system/memory/permanent" "Permanent"
    ;;
  all)
    search_in_dir "workspace/memory/volatile" "Volatile"
    search_in_dir "workspace/memory/task" "Task"
    search_in_dir "system/memory/permanent" "Permanent"
    ;;
esac
```
`json`
```json
{
  "name": "memory_search",
  "description": "Searches for patterns across memory tiers.",
  "parameters": {
    "type": "object",
    "properties": {
      "pattern": { "type": "string", "description": "Pattern to search for in memories" },
      "type": { "type": "string", "enum": ["volatile", "task", "permanent", "all"], "description": "Memory tier to search (default: all)" }
    },
    "required": ["pattern"]
  }
}
```

#### send_message
`sh`
```sh
#!/bin/bash
# Sends a message to another agent's inbox
TO_AGENT=$(echo "$GEMINI_TOOL_ARGS" | jq -r .to)
FROM_AGENT=$(echo "$GEMINI_TOOL_ARGS" | jq -r .from // "SystemAgent")
MESSAGE=$(echo "$GEMINI_TOOL_ARGS" | jq -r .message)
PRIORITY=$(echo "$GEMINI_TOOL_ARGS" | jq -r .priority // "normal")
TIMESTAMP=$(date +%s)
HUMAN_TIME=$(date +"%Y-%m-%d %H:%M:%S")

# Create inbox directory for recipient
mkdir -p "workspace/messages/inbox/$TO_AGENT"

# Create message file with metadata
MSG_FILE="workspace/messages/inbox/$TO_AGENT/msg_${TIMESTAMP}_${FROM_AGENT}.md"
cat > "$MSG_FILE" << EOF
---
from: $FROM_AGENT
to: $TO_AGENT
timestamp: $TIMESTAMP
time: $HUMAN_TIME
priority: $PRIORITY
---

$MESSAGE
EOF

echo "Message sent to $TO_AGENT (Priority: $PRIORITY)"
```
`json`
```json
{
  "name": "send_message",
  "description": "Sends a message to another agent. Messages are queued in the recipient's inbox.",
  "parameters": {
    "type": "object",
    "properties": {
      "to": { "type": "string", "description": "Name of the recipient agent" },
      "from": { "type": "string", "description": "Name of the sender agent (default: SystemAgent)" },
      "message": { "type": "string", "description": "The message content" },
      "priority": { "type": "string", "enum": ["urgent", "high", "normal", "low"], "description": "Message priority (default: normal)" }
    },
    "required": ["to", "message"]
  }
}
```

#### check_messages
`sh`
```sh
#!/bin/bash
# Checks an agent's inbox for new messages
AGENT_NAME=$(echo "$GEMINI_TOOL_ARGS" | jq -r .agent // "SystemAgent")
FILTER_PRIORITY=$(echo "$GEMINI_TOOL_ARGS" | jq -r .priority // "all")
MARK_READ=$(echo "$GEMINI_TOOL_ARGS" | jq -r .mark_read // "false")

INBOX_DIR="workspace/messages/inbox/$AGENT_NAME"

if [ ! -d "$INBOX_DIR" ]; then
  echo "No messages found for $AGENT_NAME"
  exit 0
fi

# List messages sorted by timestamp
echo "=== Inbox for $AGENT_NAME ==="
for msg_file in $(ls -t "$INBOX_DIR"/*.md 2>/dev/null); do
  if [ -f "$msg_file" ]; then
    # Extract metadata
    PRIORITY=$(grep "^priority:" "$msg_file" | cut -d' ' -f2)
    
    # Apply priority filter if specified
    if [ "$FILTER_PRIORITY" != "all" ] && [ "$PRIORITY" != "$FILTER_PRIORITY" ]; then
      continue
    fi
    
    echo ""
    echo "--- Message ---"
    cat "$msg_file"
    
    # Move to read folder if requested
    if [ "$MARK_READ" = "true" ]; then
      mkdir -p "workspace/messages/read/$AGENT_NAME"
      mv "$msg_file" "workspace/messages/read/$AGENT_NAME/"
    fi
  fi
done
```
`json`
```json
{
  "name": "check_messages",
  "description": "Checks an agent's inbox for messages.",
  "parameters": {
    "type": "object",
    "properties": {
      "agent": { "type": "string", "description": "Agent name to check messages for (default: SystemAgent)" },
      "priority": { "type": "string", "enum": ["urgent", "high", "normal", "low", "all"], "description": "Filter by priority (default: all)" },
      "mark_read": { "type": "boolean", "description": "Move messages to read folder after viewing (default: false)" }
    }
  }
}
```

#### broadcast_message
`sh`
```sh
#!/bin/bash
# Broadcasts a message to all agents via a shared bulletin board
FROM_AGENT=$(echo "$GEMINI_TOOL_ARGS" | jq -r .from // "SystemAgent")
MESSAGE=$(echo "$GEMINI_TOOL_ARGS" | jq -r .message)
TOPIC=$(echo "$GEMINI_TOOL_ARGS" | jq -r .topic // "general")
TIMESTAMP=$(date +%s)
HUMAN_TIME=$(date +"%Y-%m-%d %H:%M:%S")

# Create bulletin directory
mkdir -p "workspace/messages/bulletins/$TOPIC"

# Create bulletin file
BULLETIN_FILE="workspace/messages/bulletins/$TOPIC/bulletin_${TIMESTAMP}_${FROM_AGENT}.md"
cat > "$BULLETIN_FILE" << EOF
---
from: $FROM_AGENT
topic: $TOPIC
timestamp: $TIMESTAMP
time: $HUMAN_TIME
type: broadcast
---

$MESSAGE
EOF

echo "Broadcast posted to topic: $TOPIC"
```
`json`
```json
{
  "name": "broadcast_message",
  "description": "Posts a message to a shared bulletin board that all agents can read.",
  "parameters": {
    "type": "object",
    "properties": {
      "message": { "type": "string", "description": "The broadcast message" },
      "topic": { "type": "string", "description": "Topic category for the broadcast (default: general)" },
      "from": { "type": "string", "description": "Name of the broadcasting agent (default: SystemAgent)" }
    },
    "required": ["message"]
  }
}
```