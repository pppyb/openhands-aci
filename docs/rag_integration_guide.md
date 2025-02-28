# RAG Integration Guide for OpenHands

This guide explains how to integrate the Retrieval Augmented Generation (RAG) capabilities into your OpenHands agents to improve their performance on code-related tasks.

## Overview

The RAG system in OpenHands allows agents to:

1. Automatically index code repositories for semantic search
2. Autonomously decide when to use code retrieval
3. Enhance their responses with relevant code snippets
4. Improve code understanding, generation, and debugging

## Installation

First, install the required dependencies:

```bash
# Install with the code-search group
poetry install --with code-search,pytorch-cpu
```

## Basic Usage

### Initializing the RAG Index

Before using RAG, you need to index your code repository:

```python
from openhands_aci.code_search import initialize_code_search

# Initialize the index
result = initialize_code_search(
    repo_path="/path/to/repo",
    save_dir="code_search_index",
    extensions=[".py", ".js", ".ts"],  # Optional: specify file extensions
)

if result["status"] == "success":
    print(f"Successfully indexed {result['num_documents']} files")
else:
    print(f"Error: {result['message']}")
```

### Using the RAG Agent

The `RAGAgent` class provides a high-level interface for using RAG in your agents:

```python
from openhands_aci.agent import RAGAgent

# Initialize the agent
agent = RAGAgent(
    repo_path="/path/to/repo",
    save_dir="code_search_index",
    auto_initialize=True,  # Automatically initialize the index if it doesn't exist
)

# Process a task with RAG
result = agent.process_task("How does the file editing functionality work?")

if result["rag_used"]:
    # RAG was used for this task
    print(f"Found {len(result['rag_results'])} relevant code snippets")
    
    # Use the enhanced context in your agent
    context = result["enhanced_context"]
    # ... use the context to inform your agent's response
```

## Advanced Usage: LLM-powered RAG Agent

For more sophisticated RAG integration, use the `LLMRAGAgent` which uses an LLM to decide when to use RAG and how to incorporate the results:

```python
from openhands_aci.agent import LLMRAGAgent

# Initialize the agent
agent = LLMRAGAgent(
    repo_path="/path/to/repo",
    llm_provider="openai",  # or "anthropic", etc.
    llm_model="gpt-3.5-turbo",
    api_key="your_api_key",  # Optional: defaults to environment variable
)

# Process a query with autonomous RAG
result = agent.process_query("How does the file editing functionality work?")

# The response already incorporates RAG results if they were used
response = result["response"]
print(f"RAG was used: {result['rag_used']}")
print(f"Response: {response}")
```

## Integration with Custom Agents

You can integrate RAG into your custom agents by using the `RAGAgent` as a component:

```python
from openhands_aci.agent import RAGAgent

class MyCustomAgent:
    def __init__(self, repo_path):
        # Initialize the RAG component
        self.rag_agent = RAGAgent(repo_path=repo_path, auto_initialize=True)
        
        # ... other initialization
    
    def process_user_request(self, request):
        # Check if the request would benefit from RAG
        rag_result = self.rag_agent.process_task(request)
        
        if rag_result["rag_used"]:
            # Use the RAG results to enhance your agent's response
            enhanced_context = rag_result["enhanced_context"]
            
            # ... generate a response using the enhanced context
            response = self._generate_response_with_context(request, enhanced_context)
        else:
            # Generate a response without RAG
            response = self._generate_response(request)
        
        return response
```

## Performance Considerations

- **Indexing Time**: For large repositories, indexing can take several minutes
- **Memory Usage**: The embedding model and index can use significant memory
- **Query Time**: Each RAG query takes a few hundred milliseconds
- **Storage**: The index files can be large for big repositories

## Best Practices

1. **Index Once, Use Many Times**: Index repositories once and reuse the index
2. **Use Selective Indexing**: Only index relevant file types
3. **Tune RAG Thresholds**: Adjust when RAG is used based on your use case
4. **Cache Results**: Consider caching RAG results for common queries
5. **Combine with LLM**: Use an LLM to decide when to use RAG and how to incorporate results

## Examples

See the `examples/` directory for complete examples:

- `examples/code_search_example.py`: Basic code search usage
- `examples/agent_with_rag.py`: Simple RAG agent integration
- `examples/autonomous_rag_agent.py`: Autonomous RAG agent
- `examples/llm_rag_agent_example.py`: LLM-powered RAG agent

## Troubleshooting

- **Index Not Found**: Ensure the index directory exists and has been initialized
- **Out of Memory**: Try using a smaller embedding model or reducing batch size
- **Slow Performance**: Consider using a CPU-optimized model or reducing the repository size
- **Poor Results**: Try adjusting the query or using a different embedding model