# Code Search with RAG Capabilities

This module provides semantic code search functionality using Retrieval Augmented Generation (RAG) techniques. It allows agents to search codebases using natural language queries and retrieve relevant code snippets.

## Features

- Semantic code search using sentence transformers (configurable via env var)
- Fast similarity search using FAISS
- Support for indexing any git repository with configurable file extensions
- Save/load functionality for search indices
- Comprehensive error handling and test coverage

## Installation

The code search functionality requires additional dependencies. Install them using:

```bash
# Install with the code-search group
poetry install --with code-search,pytorch-cpu
```

## Usage

### Basic Usage

```python
from openhands_aci.code_search import initialize_code_search, search_code

# Initialize search for a repository
result = initialize_code_search(
    repo_path="/path/to/repo",
    save_dir="/path/to/save",
    extensions=[".py"],  # optional
    embedding_model="BAAI/bge-base-en-v1.5"  # optional
)

# Search code
result = search_code(
    save_dir="/path/to/save",
    query="function that handles HTTP requests",
    k=5  # number of results
)

# Process search results
if result["status"] == "success":
    for doc in result["results"]:
        print(f"File: {doc['path']}")
        print(f"Score: {doc['score']}")
        print(f"Content: {doc['content'][:100]}...")
```

### Advanced Usage

For more advanced usage, you can use the `CodeSearchIndex` class directly:

```python
from openhands_aci.code_search import CodeSearchIndex

# Create an index
index = CodeSearchIndex(embedding_model="BAAI/bge-base-en-v1.5")

# Add documents
documents = [
    {"id": "file1.py", "content": "def hello(): print('Hello')", "path": "file1.py"},
    {"id": "file2.py", "content": "def add(a, b): return a + b", "path": "file2.py"},
]
index.add_documents(documents)

# Search
results = index.search("function that adds numbers", k=5)

# Save the index
index.save("/path/to/save")

# Load the index
loaded_index = CodeSearchIndex.load("/path/to/save")
```

## Configuration

You can configure the embedding model using the `EMBEDDING_MODEL` environment variable:

```bash
export EMBEDDING_MODEL="BAAI/bge-base-en-v1.5"
```

## Integration with Agents

See the examples directory for demonstrations of how to integrate code search with agent workflows:

- `examples/code_search_example.py`: Basic usage example
- `examples/agent_with_rag.py`: Integration with an agent workflow

## Performance Considerations

- The first time you load a model, it will download the model files
- For large codebases, indexing can take some time
- Consider using a smaller model for faster performance on resource-constrained environments