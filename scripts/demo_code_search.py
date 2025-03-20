#!/usr/bin/env python3
"""
Demo script for the RAG-based code search tool.

This script demonstrates how to use the code search tool to index a repository
and search for code based on natural language queries.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from openhands_aci.tools.code_search_tool import code_search_tool


def main():
    # Get the repository path (current directory by default)
    repo_path = os.getcwd()
    
    # Set up the save directory for the index
    save_dir = os.path.join(repo_path, ".code_search_index")
    
    # Initialize the search index (only needed once)
    print(f"Indexing repository: {repo_path}")
    result = code_search_tool(
        query="initialize",  # Dummy query for initialization
        repo_path=repo_path,
        save_dir=save_dir,
        extensions=[".py"],  # Only index Python files
    )
    
    if result["status"] == "error":
        print(f"Error initializing code search: {result['message']}")
        return
    
    print(f"Successfully indexed {result['results'][0]['file'] if 'results' in result else ''}")
    
    # Example searches
    queries = [
        "code that handles file editing",
        "function that runs shell commands",
        "code for linting Python files",
        "utility functions for generating diffs",
    ]
    
    for query in queries:
        print(f"\n\nSearching for: '{query}'")
        result = code_search_tool(
            query=query,
            save_dir=save_dir,
            k=3  # Return top 3 results
        )
        
        if result["status"] == "error":
            print(f"Error searching code: {result['message']}")
            continue
        
        # Print results
        for i, res in enumerate(result["results"], 1):
            print(f"\nResult {i}: {res['file']} (Score: {res['score']:.3f})")
            print("-" * 80)
            # Show a snippet of the content
            content_lines = res["content"].split("\n")
            snippet = "\n".join(content_lines[:min(5, len(content_lines))])
            if len(content_lines) > 5:
                snippet += "\n... (content truncated)"
            print(snippet)


if __name__ == "__main__":
    main()