#!/usr/bin/env python3
"""
Demo script for the code search functionality.

This script demonstrates how to use the code search tool to index and search a repository.
"""

import argparse
import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from openhands_aci.code_search import initialize_code_search, search_code


def main():
    parser = argparse.ArgumentParser(description="Demo for code search functionality")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Initialize command
    init_parser = subparsers.add_parser("initialize", help="Initialize code search for a repository")
    init_parser.add_argument("repo_path", help="Path to the git repository")
    init_parser.add_argument("--save-dir", default="./code_search_index", help="Directory to save the search index")
    init_parser.add_argument("--extensions", nargs="+", default=[".py"], help="File extensions to include")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search code in an indexed repository")
    search_parser.add_argument("--save-dir", default="./code_search_index", help="Directory containing the search index")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--k", type=int, default=5, help="Number of results to return")
    
    args = parser.parse_args()
    
    if args.command == "initialize":
        print(f"Initializing code search for repository: {args.repo_path}")
        result = initialize_code_search(
            repo_path=args.repo_path,
            save_dir=args.save_dir,
            extensions=args.extensions,
        )
        
        if result["status"] == "success":
            print(f"Success! Indexed {result['num_documents']} files.")
        else:
            print(f"Error: {result['message']}")
            return 1
            
    elif args.command == "search":
        print(f"Searching for: {args.query}")
        result = search_code(
            save_dir=args.save_dir,
            query=args.query,
            k=args.k,
        )
        
        if result["status"] == "success":
            print(f"Found {len(result['results'])} results:")
            for i, doc in enumerate(result["results"], 1):
                print(f"\n--- Result {i} ---")
                print(f"File: {doc.get('path', 'Unknown')}")
                print(f"Score: {doc.get('score', 0):.3f}")
                
                # Print a snippet of the content
                content = doc.get('content', '')
                if content:
                    lines = content.split('\n')
                    if len(lines) > 10:
                        snippet = '\n'.join(lines[:10]) + "\n..."
                    else:
                        snippet = content
                    print(f"Snippet:\n{snippet}")
        else:
            print(f"Error: {result['message']}")
            return 1
    else:
        parser.print_help()
        return 1
        
    return 0


if __name__ == "__main__":
    sys.exit(main())