# Code Search Tool with RAG Capabilities

This module provides a semantic code search tool that uses Retrieval Augmented Generation (RAG) to find relevant code based on natural language queries.

## Features

- Semantic code search using sentence transformers
- Fast similarity search using FAISS
- Support for indexing any git repository with configurable file extensions
- Save/load functionality for search indices
- Comprehensive error handling and test coverage

## Installation

The code search tool requires additional dependencies. You can install them using Poetry:

```bash
# Install the code search dependencies
poetry install --with code-search,pytorch-cpu
```

Or with pip:

```bash
pip install sentence-transformers faiss-cpu torch
```

## Usage

### As a Tool in OpenHands Editor

The code search tool is integrated into the OpenHands Editor and can be used as follows:

```python
from openhands_aci.editor import OHEditor

editor = OHEditor()

# Search for code
result = editor(
    command="code_search",
    query="function that handles HTTP requests",
    repo_path="/path/to/repo",  # Optional if already indexed
    save_dir="/path/to/save",   # Optional, defaults to .code_search_index
    extensions=[".py"],         # Optional
    k=5                         # Optional, number of results
)

print(result.output)
```

### Direct API Usage

You can also use the code search tool directly:

```python
from openhands_aci.tools.code_search_tool import code_search_tool

# Initialize search for a repository
result = code_search_tool(
    query="initialize",  # Dummy query for initialization
    repo_path="/path/to/repo",
    save_dir="/path/to/save",
    extensions=[".py"],  # Optional
)

# Search code
result = code_search_tool(
    query="function that handles HTTP requests",
    save_dir="/path/to/save",
    k=5  # Number of results
)

# Print results
for res in result["results"]:
    print(f"File: {res['file']}")
    print(f"Score: {res['score']}")
    print(res["content"][:200] + "...")  # Show a snippet
    print()
```

## Configuration

The embedding model can be configured through an environment variable:

```bash
export EMBEDDING_MODEL="BAAI/bge-base-en-v1.5"
```

Default model is `BAAI/bge-base-en-v1.5`, but you can use any model from the [Sentence Transformers](https://www.sbert.net/docs/pretrained_models.html) library.

## Demo

A demo script is provided in the `scripts` directory:

```bash
python scripts/demo_code_search.py
```

This will index the current repository and perform some example searches.