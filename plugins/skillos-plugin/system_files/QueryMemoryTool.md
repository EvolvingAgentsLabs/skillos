# QueryMemory Tool Specification

## Purpose
QueryMemory enables agents to search and retrieve relevant information from SkillOS's long-term memory, allowing the system to learn from past projects and reuse successful patterns.

## Tool Interface

### Function Signature
```
QueryMemory(
  query: string,
  memory_type: "agent_templates" | "workflow_patterns" | "domain_knowledge" | "all",
  project_context: string (optional)
)
```

### Parameters

**query** (required)
- Natural language description of what to find
- Examples:
  - "Agent designs for mathematical analysis tasks"
  - "Workflow patterns for quantum computing projects"
  - "Successful strategies for multi-agent coordination"

**memory_type** (required)
- Scope of search within long-term memory
- Values:
  - `agent_templates`: Search for reusable agent designs
  - `workflow_patterns`: Search for task decomposition and orchestration patterns
  - `domain_knowledge`: Search for domain-specific insights
  - `all`: Search across all memory types

**project_context** (optional)
- Current project description to improve relevance
- Helps filter and rank results

## Implementation Mapping

Since Claude Code does not have a native QueryMemory tool, this operation is implemented using existing tools:

### Search Implementation
```
1. Use Glob to find all long_term memory files:
   Glob(pattern: "projects/*/memory/long_term/**/*.md")

2. Use Grep to search for relevant keywords:
   Grep(pattern: query_keywords, path: "projects/", output_mode: "content")

3. Use Read to retrieve full content of matching files

4. Synthesize results based on relevance
```

### Example Query Execution
```
Query: "Agent designs for mathematical analysis"

Step 1: Glob "projects/*/memory/long_term/agent_templates/*.md"
Step 2: Grep pattern="mathematical|analysis|computation"
Step 3: Read top matches
Step 4: Extract and synthesize relevant agent specifications
```

## Usage Patterns

### Pattern 1: Agent Template Retrieval
When creating a new agent, first query for similar past designs:

```
1. QueryMemory(
     query: "Agent for [domain] tasks",
     memory_type: "agent_templates",
     project_context: current_goal
   )

2. If relevant templates found:
   - Adapt template to current needs
   - Reuse proven prompt structures

3. If no templates found:
   - Create agent from scratch
   - Log as new template for future use
```

### Pattern 2: Workflow Pattern Lookup
When planning task decomposition:

```
1. QueryMemory(
     query: "Workflow patterns for [type] projects",
     memory_type: "workflow_patterns",
     project_context: current_goal
   )

2. If relevant patterns found:
   - Apply successful orchestration strategies
   - Avoid documented pitfalls

3. If no patterns found:
   - Design workflow from first principles
   - Log pattern for future use
```

### Pattern 3: Domain Knowledge Retrieval
When working in specific domains:

```
1. QueryMemory(
     query: "[Domain] knowledge and best practices",
     memory_type: "domain_knowledge",
     project_context: current_goal
   )

2. Apply retrieved domain insights to:
   - Agent prompt engineering
   - Task decomposition strategies
   - Output quality criteria
```

## Return Format

### Successful Query
```markdown
# Query Results

## Query
[Original query string]

## Matches Found: [N]

### Match 1: [File name]
**Source Project**: [Project name]
**Relevance**: [High|Medium|Low]
**Summary**: [Brief description]

**Content**:
[Relevant excerpt or full content]

---

### Match 2: [File name]
[Repeat structure]
```

### No Results
```markdown
# Query Results

## Query
[Original query string]

## Matches Found: 0

No relevant memories found for this query.

**Recommendation**: Create new solution and log for future reference.
```

## Best Practices

### Query Formulation
- Use specific, descriptive queries
- Include domain keywords
- Specify the type of information needed (template, pattern, knowledge)

### Result Interpretation
- Review all returned matches
- Adapt templates to current context
- Combine insights from multiple sources
- Don't blindly copy—understand and customize

### Memory Maintenance
- After using retrieved knowledge, log the outcome
- Update templates with improvements
- Document new patterns discovered through adaptation

## Integration Points

### SystemAgent
- Queries memory before creating agents
- Uses retrieved templates as starting points
- Logs new patterns after project completion

### MemoryConsolidationAgent
- Creates queryable learning artifacts
- Structures knowledge for efficient retrieval
- Tags content with searchable metadata

## Performance Considerations

- Glob operations scale linearly with project count
- Grep performance depends on total memory size
- Limit Read operations to most relevant matches
- Cache frequently used templates

## Future Enhancements
- Semantic similarity search
- Automatic query expansion
- Relevance ranking algorithms
- Cross-project pattern detection
- Template versioning and evolution tracking
