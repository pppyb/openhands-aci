"""
Example script demonstrating how to use the code search tool with RAG capabilities.

This script shows how to:
1. Initialize a code search index for a repository
2. Search for code using natural language queries
3. Use the search results to enhance an agent's understanding of the codebase
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import openhands_aci
sys.path.append(str(Path(__file__).parent.parent))

from openhands_aci.code_search import initialize_code_search, search_code


def main():
    # Path to the repository to index
    repo_path = str(Path(__file__).parent.parent)
    
    # Directory to save the search index
    save_dir = "code_search_index"
    
    # Initialize the code search index (only needs to be done once)
    print(f"Initializing code search index for repository: {repo_path}")
    result = initialize_code_search(
        repo_path=repo_path,
        save_dir=save_dir,
        extensions=[".py"],  # Only index Python files
        embedding_model="BAAI/bge-base-en-v1.5",  # Can be configured via EMBEDDING_MODEL env var
    )
    
    if result["status"] == "error":
        print(f"Error initializing code search: {result['message']}")
        return
    
    print(f"Successfully indexed {result['num_documents']} files")
    
    # Example searches
    queries = [
        "code that handles file editing",
        "function that parses Python code",
        "utility for running shell commands",
    ]
    
    for query in queries:
        print(f"\nSearching for: '{query}'")
        search_result = search_code(save_dir=save_dir, query=query, k=3)
        
        if search_result["status"] == "error":
            print(f"Error searching: {search_result['message']}")
            continue
        
        # Display the search results
        print(f"Found {len(search_result['results'])} results:")
        for i, doc in enumerate(search_result["results"]):
            print(f"\nResult {i+1} (score: {doc['score']:.3f}):")
            print(f"File: {doc['path']}")
            
            # Show a snippet of the content (first 200 chars)
            content_preview = doc['content'][:200].replace('\n', ' ')
            if len(doc['content']) > 200:
                content_preview += "..."
            print(f"Preview: {content_preview}")


if __name__ == "__main__":
    main()