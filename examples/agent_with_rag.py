"""
Example demonstrating how to integrate the code search tool with RAG capabilities
into an agent workflow.

This example shows:
1. How to initialize a code search index for a repository
2. How to use the search results to enhance an agent's understanding of the codebase
3. How to integrate code search into the agent's decision-making process
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add the parent directory to the path so we can import openhands_aci
sys.path.append(str(Path(__file__).parent.parent))

from openhands_aci.code_search import initialize_code_search, search_code


class AgentWithRAG:
    """Example agent class that uses RAG for code understanding."""
    
    def __init__(self, repo_path: str, save_dir: str = "code_search_index"):
        """Initialize the agent with RAG capabilities.
        
        Args:
            repo_path: Path to the repository to index
            save_dir: Directory to save the search index
        """
        self.repo_path = repo_path
        self.save_dir = save_dir
        self.index_initialized = False
        
    def initialize_index(self, extensions: List[str] = [".py"]) -> Dict[str, Any]:
        """Initialize the code search index for the repository.
        
        Args:
            extensions: List of file extensions to include in the index
            
        Returns:
            Dictionary with status and message
        """
        result = initialize_code_search(
            repo_path=self.repo_path,
            save_dir=self.save_dir,
            extensions=extensions,
        )
        
        if result["status"] == "success":
            self.index_initialized = True
            
        return result
    
    def search_codebase(self, query: str, k: int = 5) -> Dict[str, Any]:
        """Search the codebase using a natural language query.
        
        Args:
            query: Natural language query
            k: Number of results to return
            
        Returns:
            Dictionary with status and search results
        """
        if not self.index_initialized and not os.path.exists(self.save_dir):
            print("Index not initialized. Initializing now...")
            init_result = self.initialize_index()
            if init_result["status"] == "error":
                return init_result
        
        return search_code(save_dir=self.save_dir, query=query, k=k)
    
    def answer_question(self, question: str) -> str:
        """Answer a question about the codebase using RAG.
        
        Args:
            question: Question about the codebase
            
        Returns:
            Answer to the question
        """
        # Search the codebase for relevant code
        search_result = self.search_codebase(question)
        
        if search_result["status"] == "error":
            return f"Error: {search_result['message']}"
        
        if not search_result["results"]:
            return "I couldn't find any relevant code to answer your question."
        
        # In a real agent, you would use an LLM to generate an answer based on the search results
        # Here we'll just return a simple response with the top result
        top_result = search_result["results"][0]
        
        answer = (
            f"Based on my search of the codebase, I found this relevant file: {top_result['path']}\n\n"
            f"Here's a snippet that might help answer your question:\n\n"
            f"```python\n{top_result['content'][:500]}...\n```\n\n"
            f"This code has a relevance score of {top_result['score']:.3f} to your question."
        )
        
        return answer


def main():
    # Path to the repository to index
    repo_path = str(Path(__file__).parent.parent)
    
    # Create an agent with RAG capabilities
    agent = AgentWithRAG(repo_path)
    
    # Initialize the index (only needs to be done once)
    print("Initializing code search index...")
    result = agent.initialize_index()
    
    if result["status"] == "error":
        print(f"Error initializing index: {result['message']}")
        return
    
    print(f"Successfully indexed {result['num_documents']} files")
    
    # Example questions to answer
    questions = [
        "How does the file editing functionality work?",
        "What utilities are available for running shell commands?",
        "How can I parse Python code in this codebase?",
    ]
    
    for question in questions:
        print(f"\n\nQuestion: {question}")
        answer = agent.answer_question(question)
        print(f"\nAnswer:\n{answer}")


if __name__ == "__main__":
    main()