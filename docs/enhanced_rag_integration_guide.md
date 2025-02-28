# Enhanced RAG Integration Guide for OpenHands

This guide explains how to use the enhanced RAG integration features in OpenHands ACI, which provide deeper integration between RAG capabilities and other components of the system.

## Overview

The enhanced RAG integration in OpenHands ACI includes:

1. **Event-Driven Architecture**: A flexible event system that allows components to communicate and react to events
2. **Enhanced Editor**: Editor functionality with RAG context for more intelligent code editing
3. **Enhanced Linter**: Linting with RAG-powered fix suggestions
4. **Integrated Workflow**: Complete development workflows that combine multiple components
5. **Visualization Tools**: Tools for formatting and displaying RAG results

## Installation

First, install the required dependencies:

```bash
# Install with the code-search group
poetry install --with code-search,pytorch-cpu
```

## Event-Driven Architecture

The event system allows components to communicate through events:

```python
from openhands_aci.events import subscribe, trigger

# Subscribe to an event
def handle_search_results(event_name, query, results, **kwargs):
    print(f"Search results for: {query}")
    for result in results:
        print(f"- {result['path']} (score: {result['score']})")

# Register the handler
subscribe("search_results", handle_search_results)

# Trigger an event
trigger("search_results", query="function to parse JSON", results=[...])
```

### Common Events

- `search_results`: Triggered when search results are available
- `file_edited`: Triggered when a file is edited
- `file_created`: Triggered when a file is created
- `lint_result`: Triggered when linting results are available
- `task_result`: Triggered when a task is completed
- `workflow_complete`: Triggered when a workflow is completed

## Enhanced Editor

The enhanced editor integrates RAG capabilities into the editing process:

```python
from openhands_aci.editor import edit_with_context, create_with_context, str_replace_with_context

# Edit a file with RAG context
result = edit_with_context(
    file_path="/path/to/file.py",
    task="Implement a function to calculate the Fibonacci sequence",
)

# Create a file with RAG context
result = create_with_context(
    file_path="/path/to/new_file.py",
    task="Create a utility module with date formatting functions",
)

# Replace a string with RAG context
result = str_replace_with_context(
    file_path="/path/to/file.py",
    old_str="def old_function():\n    pass",
    task="Implement a better version of this function",
)
```

## Enhanced Linter

The enhanced linter provides RAG-powered fix suggestions:

```python
from openhands_aci.linter import lint_with_context, suggest_fixes

# Lint a file with RAG context
result = lint_with_context(
    file_path="/path/to/file.py",
    fix=True,  # Automatically apply fixes when possible
)

# Get fix suggestions for specific issues
issues = [
    {"line": 10, "column": 5, "code": "E501", "message": "Line too long"},
    {"line": 15, "column": 1, "code": "F401", "message": "Unused import"},
]
suggestions = suggest_fixes(
    file_path="/path/to/file.py",
    issues=issues,
)
```

## Integrated Workflow

The integrated workflow combines multiple components for complete development tasks:

```python
from openhands_aci.workflow import execute_task, format_result

# Execute a development task
result = execute_task(
    task="Implement a utility function to convert temperature between Celsius and Fahrenheit",
    file_paths=["/path/to/file.py"],
    run_tests=True,
)

# Format the result for display
formatted_result = format_result(result, format_type="markdown")
print(formatted_result)
```

## Visualization Tools

The visualization tools help format and display RAG results:

```python
from openhands_aci.visualization import format_search_results, format_rag_context, format_task_result

# Format search results
formatted_results = format_search_results(
    results=search_results,
    format_type="markdown",  # or "html", "json", "text"
    max_results=5,
    max_content_length=500,
)

# Format RAG context
formatted_context = format_rag_context(
    context=rag_context,
    format_type="markdown",
    include_header=True,
)

# Format task result
formatted_task_result = format_task_result(
    task="Implement a function",
    rag_used=True,
    rag_results=rag_results,
    response="Function implemented successfully",
    format_type="markdown",
)
```

## Configuration

The system can be configured through the `config.py` module:

```python
from openhands_aci.config import get_config, update_config

# Get configuration
rag_config = get_config("rag")
print(f"Default embedding model: {rag_config['default_embedding_model']}")

# Update configuration
update_config("rag", {
    "default_embedding_model": "sentence-transformers/all-mpnet-base-v2",
    "max_results": 10,
})
```

## Complete Example

Here's a complete example that demonstrates the enhanced RAG integration:

```python
import os
from openhands_aci.editor import edit_with_context
from openhands_aci.linter import lint_with_context
from openhands_aci.events import subscribe, trigger
from openhands_aci.workflow import execute_task, format_result

# Register event handlers
def handle_file_edited(event_name, file_path, task, context, result, **kwargs):
    print(f"File edited: {file_path}")
    print(f"Task: {task}")
    print(f"Status: {result.get('status', 'unknown')}")

subscribe("file_edited", handle_file_edited)

# Execute a development task
result = execute_task(
    task="Implement a function to calculate the factorial of a number",
    file_paths=["/path/to/math_utils.py"],
    run_tests=True,
)

# Print the formatted result
print(format_result(result, format_type="markdown"))
```

## Best Practices

1. **Use Event Handlers**: Register event handlers to react to system events
2. **Provide Clear Tasks**: Give clear and specific task descriptions for better RAG results
3. **Configure for Your Needs**: Adjust configuration settings based on your specific requirements
4. **Combine with LLMs**: For even better results, combine RAG with LLMs for code generation
5. **Cache Results**: Consider caching search results for frequently accessed code patterns

## Troubleshooting

- **Event Handlers Not Called**: Make sure you've registered the handlers before triggering events
- **Poor RAG Results**: Try adjusting the query or using a different embedding model
- **Performance Issues**: Consider using a smaller embedding model or reducing batch size
- **Integration Problems**: Check the event flow and make sure components are properly connected

## Examples

See the `examples/` directory for complete examples:

- `examples/enhanced_workflow_example.py`: Demonstrates the enhanced workflow
- `examples/event_system_example.py`: Shows how to use the event system
- `examples/visualization_example.py`: Demonstrates the visualization tools