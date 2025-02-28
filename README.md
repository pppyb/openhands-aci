# Agent-Computer Interface (ACI) for OpenHands

An Agent-Computer Interface (ACI) designed for software development agents [OpenHands](https://github.com/All-Hands-AI/OpenHands). This package provides essential tools and interfaces for AI agents to interact with computer systems for software development tasks.

## Features

- **Code Editor Interface**: Sophisticated editing capabilities through the `editor` module
  - File creation and modification
  - Code editing
  - Configuration management

- **Code Linting**: Built-in linting capabilities via the `linter` module
  - Tree-sitter based code analysis
  - Python-specific linting support

- **Code Search with RAG**: Semantic code search using Retrieval Augmented Generation
  - Index and search code repositories using natural language
  - Find relevant code snippets based on semantic similarity
  - Enhance agent understanding of codebases

- **Autonomous RAG Agents**: Agents that can autonomously use RAG capabilities
  - Automatic decision-making for when to use code retrieval
  - Integration with LLMs for enhanced responses
  - Improved code understanding, generation, and debugging

- **Utility Functions**: Helper modules for common operations
  - Shell command execution utilities
  - Diff generation and analysis
  - Logging functionality

## Installation

```bash
pip install openhands-aci
```

Or using Poetry:

```bash
poetry add openhands-aci
```

For RAG capabilities, install with optional dependencies:

```bash
pip install "openhands-aci[code-search,pytorch-cpu]"
```

Or using Poetry:

```bash
poetry add openhands-aci --extras "code-search pytorch-cpu"
```

## Project Structure

```
openhands_aci/
├── agent/            # Agent implementations
│   ├── rag_agent.py  # RAG-enhanced agent
│   └── llm_rag_agent.py # LLM-powered RAG agent
├── code_search/      # Code search with RAG capabilities
│   ├── core.py       # Core indexing and search functionality
│   └── tools.py      # High-level tool functions
├── editor/           # Code editing functionality
├── linter/           # Code linting capabilities
└── utils/            # Utility functions
```

## Development

1. Clone the repository:
```bash
git clone https://github.com/All-Hands-AI/openhands-aci.git
cd openhands-aci
```

2. Install development dependencies:
```bash
# Basic installation
poetry install

# With RAG capabilities
poetry install --with code-search,pytorch-cpu
```

3. Configure pre-commit-hooks
```bash
make install-pre-commit-hooks
```

4. Run tests:
```bash
poetry run pytest
```

## License

This project is licensed under the MIT License.
