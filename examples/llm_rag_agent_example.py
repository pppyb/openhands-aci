"""
Example demonstrating how to use the LLM-powered RAG agent.

This example shows:
1. How to initialize the LLM RAG agent
2. How the agent uses an LLM to decide when to use RAG
3. How the agent incorporates RAG results into its LLM-generated responses
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import openhands_aci
sys.path.append(str(Path(__file__).parent.parent))

from openhands_aci.agent import LLMRAGAgent


def main():
    # Check if API key is set
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Warning: OPENAI_API_KEY environment variable not set.")
        print("This example requires an OpenAI API key to run.")
        print("You can set it with: export OPENAI_API_KEY=your_api_key")
        return
    
    # Path to the repository to index
    repo_path = str(Path(__file__).parent.parent)
    
    # Directory to save the search index
    save_dir = "code_search_index"
    
    # Initialize the LLM RAG agent
    print(f"Initializing LLM RAG agent for repository: {repo_path}")
    agent = LLMRAGAgent(
        repo_path=repo_path,
        llm_provider="openai",
        llm_model="gpt-3.5-turbo",
        save_dir=save_dir,
        auto_initialize=True,
    )
    
    # Example questions that might benefit from RAG
    questions = [
        "How does the file editing functionality work in this codebase?",
        "What's the best way to implement a new linter in this framework?",
        "Explain the architecture of the code search module",
        "What design patterns are used in this codebase?",
    ]
    
    # Process each question
    for question in questions:
        print(f"\n\n{'='*80}\nQuestion: {question}\n{'='*80}")
        
        # Process the question
        result = agent.process_query(question)
        
        # Print whether RAG was used
        if result["rag_used"]:
            print(f"RAG was used: Found {len(result['rag_results'])} relevant code snippets")
            print(f"Processing time: {result['processing_time']:.2f} seconds")
            
            # Print the top result
            if result["rag_results"]:
                top_result = result["rag_results"][0]
                print(f"\nTop result (score: {top_result['score']:.3f}):")
                print(f"File: {top_result['path']}")
        else:
            print("RAG was not used for this question")
            print(f"Processing time: {result['processing_time']:.2f} seconds")
        
        # Print the response
        print(f"\nResponse:\n{result['response']}")
    
    # Example of code implementation suggestion
    implementation_task = "Implement a function to find all Python files in a directory recursively"
    
    print(f"\n\n{'='*80}\nImplementation task: {implementation_task}\n{'='*80}")
    
    implementation = agent.suggest_code_implementation(implementation_task)
    print(f"\nSuggested implementation:\n{implementation}")
    
    # Example of code explanation
    code_to_explain = """
def search_codebase(self, query: str, k: Optional[int] = None) -> Dict[str, Any]:
    if not self.index_initialized:
        if self.auto_initialize:
            success = self._initialize_index()
            if not success:
                return {"status": "error", "message": "Failed to initialize index"}
        else:
            return {"status": "error", "message": "Index not initialized"}
    
    # Enhance the query for better retrieval
    enhanced_query = self._enhance_query(query)
    
    # Search the codebase
    return search_code(
        save_dir=self.save_dir,
        query=enhanced_query,
        k=k or self.max_results
    )
    """
    
    print(f"\n\n{'='*80}\nExplaining code:\n{'='*80}")
    print(code_to_explain)
    
    explanation = agent.explain_code(code_to_explain)
    print(f"\nExplanation:\n{explanation}")


if __name__ == "__main__":
    main()