"""
Example demonstrating how to use the autonomous RAG agent.

This example shows:
1. How to initialize the RAG agent
2. How the agent autonomously decides when to use RAG
3. How the agent incorporates RAG results into its responses
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import openhands_aci
sys.path.append(str(Path(__file__).parent.parent))

from openhands_aci.agent import RAGAgent


def main():
    # Path to the repository to index
    repo_path = str(Path(__file__).parent.parent)
    
    # Directory to save the search index
    save_dir = "code_search_index"
    
    # Initialize the RAG agent
    print(f"Initializing RAG agent for repository: {repo_path}")
    agent = RAGAgent(
        repo_path=repo_path,
        save_dir=save_dir,
        extensions=[".py"],  # Only index Python files
        auto_initialize=True,
    )
    
    # Example tasks that would benefit from RAG
    tasks = [
        "How does the file editing functionality work in this codebase?",
        "Find code that handles parsing Python syntax",
        "What's the implementation for running shell commands?",
        "Explain how the code search functionality works",
    ]
    
    # Process each task
    for task in tasks:
        print(f"\n\n{'='*80}\nTask: {task}\n{'='*80}")
        
        # Process the task
        result = agent.process_task(task)
        
        # Print whether RAG was used
        if result["rag_used"]:
            print(f"RAG was used: Found {len(result['rag_results'])} relevant code snippets")
            
            # Print the top result
            if result["rag_results"]:
                top_result = result["rag_results"][0]
                print(f"\nTop result (score: {top_result['score']:.3f}):")
                print(f"File: {top_result['path']}")
                
                # Show a snippet of the content
                content_preview = top_result['content'][:200].replace('\n', ' ')
                if len(top_result['content']) > 200:
                    content_preview += "..."
                print(f"Preview: {content_preview}")
            
            # Get an answer using the RAG results
            answer = agent.answer_question(task)
            print(f"\nAnswer:\n{answer['answer']}")
        else:
            print("RAG was not used for this task")
    
    # Example of code explanation
    code_to_explain = """
def search_code(save_dir: str, query: str, k: int = 5) -> Dict[str, Any]:
    try:
        # Load index
        index = CodeSearchIndex.load(save_dir)
        
        # Search
        results = index.search(query, k=k)
        
        return {'status': 'success', 'results': results}
    except Exception as e:
        return {'status': 'error', 'message': f'Error searching code: {str(e)}'}
    """
    
    print(f"\n\n{'='*80}\nExplaining code:\n{'='*80}")
    print(code_to_explain)
    
    explanation = agent.explain_code(code_to_explain)
    print(f"\nExplanation:\n{explanation['explanation']}")
    
    # Example of code debugging
    code_to_debug = """
def initialize_index(repo_path, save_dir):
    documents = get_files_from_repo(repo_path)
    index = CodeSearchIndex()
    index.add_documents(documents)
    index.save(save_dir)
    return {'status': 'success'}
    """
    
    error_message = "NameError: name 'get_files_from_repo' is not defined"
    
    print(f"\n\n{'='*80}\nDebugging code:\n{'='*80}")
    print(code_to_debug)
    print(f"Error: {error_message}")
    
    debug_result = agent.debug_code(code_to_debug, error_message)
    print(f"\nDebugging suggestions:\n{debug_result['suggestions']}")


if __name__ == "__main__":
    main()