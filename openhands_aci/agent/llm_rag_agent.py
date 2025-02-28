"""
LLM-powered RAG Agent for OpenHands.

This module provides an agent that uses an LLM to decide when to use RAG and how to
incorporate the retrieved information into its responses.
"""

import os
import json
import time
from typing import Any, Dict, List, Optional, Union

from .rag_agent import RAGAgent


class LLMRAGAgent:
    """Agent that uses an LLM to decide when and how to use RAG."""
    
    def __init__(
        self,
        repo_path: str,
        llm_provider: str = "openai",
        llm_model: str = "gpt-3.5-turbo",
        api_key: Optional[str] = None,
        save_dir: str = "code_search_index",
        auto_initialize: bool = True,
        max_rag_results: int = 5,
    ):
        """Initialize the LLM-powered RAG agent.
        
        Args:
            repo_path: Path to the repository to index
            llm_provider: LLM provider (e.g., "openai", "anthropic")
            llm_model: LLM model to use
            api_key: API key for the LLM provider (defaults to env var)
            save_dir: Directory to save the search index
            auto_initialize: Whether to automatically initialize the index
            max_rag_results: Maximum number of RAG results to return
        """
        self.repo_path = repo_path
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self.api_key = api_key or os.getenv(f"{llm_provider.upper()}_API_KEY")
        self.save_dir = save_dir
        self.auto_initialize = auto_initialize
        self.max_rag_results = max_rag_results
        
        # Initialize the RAG agent
        self.rag_agent = RAGAgent(
            repo_path=repo_path,
            save_dir=save_dir,
            auto_initialize=auto_initialize,
            max_results=max_rag_results,
        )
        
        # Initialize the LLM client
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the LLM client based on the provider."""
        if self.llm_provider == "openai":
            try:
                import openai
                self.llm_client = openai.OpenAI(api_key=self.api_key)
            except ImportError:
                print("OpenAI package not installed. Install with: pip install openai")
                self.llm_client = None
        elif self.llm_provider == "anthropic":
            try:
                import anthropic
                self.llm_client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                print("Anthropic package not installed. Install with: pip install anthropic")
                self.llm_client = None
        else:
            try:
                import litellm
                self.llm_client = litellm
            except ImportError:
                print("LiteLLM package not installed. Install with: pip install litellm")
                self.llm_client = None
    
    def _call_llm(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Call the LLM with the given messages.
        
        Args:
            messages: List of message dictionaries
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        if self.llm_client is None:
            return "LLM client not initialized."
        
        try:
            if self.llm_provider == "openai":
                response = self.llm_client.chat.completions.create(
                    model=self.llm_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return response.choices[0].message.content
            elif self.llm_provider == "anthropic":
                messages_text = "\n\n".join([f"{m['role']}: {m['content']}" for m in messages])
                response = self.llm_client.completions.create(
                    model=self.llm_model,
                    prompt=messages_text,
                    temperature=temperature,
                    max_tokens_to_sample=max_tokens,
                )
                return response.completion
            else:
                # Use LiteLLM as a fallback
                response = self.llm_client.completion(
                    model=self.llm_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return response.choices[0].message.content
        except Exception as e:
            return f"Error calling LLM: {str(e)}"
    
    def _should_use_rag(self, query: str) -> bool:
        """Use the LLM to decide if RAG should be used for this query.
        
        Args:
            query: The user query
            
        Returns:
            True if RAG should be used, False otherwise
        """
        messages = [
            {"role": "system", "content": (
                "You are an AI assistant that decides whether a query would benefit from "
                "retrieving relevant code from a repository before answering. "
                "Respond with 'YES' if the query is about code, implementation details, "
                "or would benefit from seeing similar code examples. "
                "Respond with 'NO' if the query is general, conceptual, or doesn't need "
                "specific code references."
            )},
            {"role": "user", "content": f"Query: {query}\n\nShould I use code retrieval for this query? Answer YES or NO."}
        ]
        
        response = self._call_llm(messages, temperature=0.1, max_tokens=10)
        return "YES" in response.upper()
    
    def _format_rag_results_for_llm(self, results: List[Dict[str, Any]]) -> str:
        """Format RAG results for inclusion in LLM prompt.
        
        Args:
            results: List of RAG results
            
        Returns:
            Formatted string
        """
        formatted = "Here are relevant code snippets from the repository:\n\n"
        
        for i, result in enumerate(results[:3], 1):  # Limit to top 3 for brevity
            path = result.get("path", "unknown")
            score = result.get("score", 0.0)
            content = result.get("content", "")
            
            # Truncate content if too long
            if len(content) > 800:
                content = content[:800] + "..."
            
            formatted += f"SNIPPET {i} (from {path}, relevance: {score:.2f}):\n```\n{content}\n```\n\n"
        
        return formatted
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process a user query, deciding whether to use RAG and generating a response.
        
        Args:
            query: The user query
            
        Returns:
            Dictionary with response and metadata
        """
        # First, decide if we should use RAG
        use_rag = self._should_use_rag(query)
        
        result = {
            "query": query,
            "rag_used": use_rag,
            "rag_results": None,
            "response": None,
            "processing_time": 0,
        }
        
        start_time = time.time()
        
        if use_rag:
            # Get RAG results
            search_result = self.rag_agent.search_codebase(query)
            
            if search_result["status"] == "success" and search_result["results"]:
                result["rag_results"] = search_result["results"]
                
                # Format RAG results for the LLM
                rag_context = self._format_rag_results_for_llm(search_result["results"])
                
                # Generate response with RAG context
                messages = [
                    {"role": "system", "content": (
                        "You are an AI assistant that helps with code-related questions. "
                        "Use the provided code snippets from the repository to inform your answer. "
                        "Reference specific parts of the code when relevant. "
                        "If the code snippets don't contain relevant information, say so."
                    )},
                    {"role": "user", "content": f"Question: {query}\n\n{rag_context}"}
                ]
                
                response = self._call_llm(messages)
                result["response"] = response
            else:
                # Fall back to non-RAG response
                messages = [
                    {"role": "system", "content": "You are an AI assistant that helps with code-related questions."},
                    {"role": "user", "content": query}
                ]
                
                response = self._call_llm(messages)
                result["response"] = response
                result["rag_used"] = False
        else:
            # Generate response without RAG
            messages = [
                {"role": "system", "content": "You are an AI assistant that helps with code-related questions."},
                {"role": "user", "content": query}
            ]
            
            response = self._call_llm(messages)
            result["response"] = response
        
        result["processing_time"] = time.time() - start_time
        
        return result
    
    def answer_code_question(self, question: str) -> str:
        """Answer a code-related question, using RAG if appropriate.
        
        Args:
            question: The code-related question
            
        Returns:
            Answer to the question
        """
        result = self.process_query(question)
        return result["response"]
    
    def suggest_code_implementation(self, task: str) -> str:
        """Suggest a code implementation for a task, using RAG if appropriate.
        
        Args:
            task: Description of the implementation task
            
        Returns:
            Suggested implementation
        """
        # Add a hint that we want code generation
        enhanced_task = f"Implement code for: {task}"
        
        result = self.process_query(enhanced_task)
        return result["response"]
    
    def explain_code(self, code: str) -> str:
        """Explain a code snippet, using RAG to find similar code for context.
        
        Args:
            code: Code snippet to explain
            
        Returns:
            Explanation of the code
        """
        # Add a hint that we want code explanation
        query = f"Explain this code:\n\n```\n{code}\n```"
        
        result = self.process_query(query)
        return result["response"]
    
    def debug_code(self, code: str, error_message: Optional[str] = None) -> str:
        """Debug code, using RAG to find similar patterns and solutions.
        
        Args:
            code: Code to debug
            error_message: Optional error message
            
        Returns:
            Debugging suggestions
        """
        # Construct query with code and error message
        query = f"Debug this code:\n\n```\n{code}\n```"
        if error_message:
            query += f"\n\nError message: {error_message}"
        
        result = self.process_query(query)
        return result["response"]