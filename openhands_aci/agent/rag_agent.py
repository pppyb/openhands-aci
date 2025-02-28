"""
RAG-enhanced Agent for OpenHands.

This module provides a framework for agents to autonomously use RAG (Retrieval Augmented Generation)
capabilities to improve their performance on code-related tasks.
"""

import os
import re
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from openhands_aci.code_search import initialize_code_search, search_code, CodeSearchIndex


class RAGAgent:
    """Agent that autonomously uses RAG to improve code understanding and generation."""

    def __init__(
        self,
        repo_path: str,
        save_dir: str = "code_search_index",
        extensions: List[str] = [".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".hpp"],
        embedding_model: Optional[str] = None,
        auto_initialize: bool = True,
        rag_threshold: float = 0.6,
        max_results: int = 5,
    ):
        """Initialize the RAG-enhanced agent.

        Args:
            repo_path: Path to the repository to index
            save_dir: Directory to save the search index
            extensions: List of file extensions to include in the index
            embedding_model: Name or path of the embedding model to use
            auto_initialize: Whether to automatically initialize the index if it doesn't exist
            rag_threshold: Threshold for deciding when to use RAG (0.0-1.0)
            max_results: Maximum number of results to return from RAG
        """
        self.repo_path = repo_path
        self.save_dir = save_dir
        self.extensions = extensions
        self.embedding_model = embedding_model
        self.auto_initialize = auto_initialize
        self.rag_threshold = rag_threshold
        self.max_results = max_results
        self.index_initialized = os.path.exists(save_dir)
        self.code_context = {}  # Store context about the codebase
        
        # Initialize the index if auto_initialize is True and the index doesn't exist
        if auto_initialize and not self.index_initialized:
            self._initialize_index()
    
    def _initialize_index(self) -> bool:
        """Initialize the code search index.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            result = initialize_code_search(
                repo_path=self.repo_path,
                save_dir=self.save_dir,
                extensions=self.extensions,
                embedding_model=self.embedding_model,
            )
            
            if result["status"] == "success":
                self.index_initialized = True
                self.code_context["num_files"] = result.get("num_documents", 0)
                return True
            return False
        except Exception as e:
            print(f"Error initializing RAG index: {str(e)}")
            return False
    
    def _should_use_rag(self, query: str) -> bool:
        """Determine if RAG should be used for this query.
        
        This method uses heuristics to decide if the query would benefit from RAG.
        
        Args:
            query: The user query or task description
            
        Returns:
            True if RAG should be used, False otherwise
        """
        # Check if the index is initialized
        if not self.index_initialized:
            if self.auto_initialize:
                self._initialize_index()
            else:
                return False
        
        # Keywords that suggest code understanding is needed
        code_keywords = [
            "how does", "where is", "find", "search", "locate", "code for", 
            "implementation of", "function", "class", "method", "implement",
            "fix", "debug", "error", "bug", "issue", "problem", "improve",
            "refactor", "optimize", "performance", "example of"
        ]
        
        # Check if any code keywords are in the query
        if any(keyword in query.lower() for keyword in code_keywords):
            return True
        
        # Check for code-related patterns
        code_patterns = [
            r'`[^`]+`',  # Code in backticks
            r'function\s+\w+',  # Function references
            r'class\s+\w+',  # Class references
            r'import\s+\w+',  # Import statements
            r'require\s*\(',  # Require statements
            r'\w+\.\w+\(',  # Method calls
            r'<[^>]+>',  # HTML/XML tags
        ]
        
        for pattern in code_patterns:
            if re.search(pattern, query):
                return True
        
        # If no clear indicators, use a random threshold
        # In a real implementation, this could be based on more sophisticated heuristics
        return True
    
    def _extract_code_elements(self, query: str) -> List[str]:
        """Extract code elements from the query for better RAG retrieval.
        
        Args:
            query: The user query or task description
            
        Returns:
            List of extracted code elements
        """
        elements = []
        
        # Extract code in backticks
        backtick_code = re.findall(r'`([^`]+)`', query)
        elements.extend(backtick_code)
        
        # Extract function names
        functions = re.findall(r'function\s+(\w+)', query)
        elements.extend(functions)
        
        # Extract class names
        classes = re.findall(r'class\s+(\w+)', query)
        elements.extend(classes)
        
        # Extract method calls
        methods = re.findall(r'(\w+\.\w+)\(', query)
        elements.extend(methods)
        
        # Extract file paths
        file_paths = re.findall(r'[\w/\.-]+\.(py|js|ts|java|c|cpp|h|hpp)', query)
        elements.extend([f[0] for f in file_paths])
        
        return elements
    
    def _enhance_query(self, query: str) -> str:
        """Enhance the query with extracted code elements for better RAG retrieval.
        
        Args:
            query: The original query
            
        Returns:
            Enhanced query
        """
        elements = self._extract_code_elements(query)
        if not elements:
            return query
        
        # Add extracted elements to the query with higher weight
        enhanced_query = query
        if elements:
            enhanced_query += " " + " ".join(elements)
        
        return enhanced_query
    
    def search_codebase(self, query: str, k: Optional[int] = None) -> Dict[str, Any]:
        """Search the codebase using RAG.
        
        Args:
            query: The search query
            k: Number of results to return (defaults to self.max_results)
            
        Returns:
            Search results
        """
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
    
    def process_task(self, task: str) -> Dict[str, Any]:
        """Process a task using RAG when appropriate.
        
        This method decides whether to use RAG for the given task and returns
        relevant code snippets if needed.
        
        Args:
            task: The task description
            
        Returns:
            Dictionary with task information and RAG results if used
        """
        result = {
            "task": task,
            "rag_used": False,
            "rag_results": None,
            "enhanced_context": None,
        }
        
        # Decide whether to use RAG
        if self._should_use_rag(task):
            search_result = self.search_codebase(task)
            
            if search_result["status"] == "success" and search_result["results"]:
                result["rag_used"] = True
                result["rag_results"] = search_result["results"]
                
                # Create enhanced context from RAG results
                context = self._create_context_from_results(search_result["results"])
                result["enhanced_context"] = context
        
        return result
    
    def _create_context_from_results(self, results: List[Dict[str, Any]]) -> str:
        """Create a context string from RAG results.
        
        Args:
            results: List of RAG results
            
        Returns:
            Context string
        """
        context = "Based on the codebase, I found these relevant code snippets:\n\n"
        
        for i, result in enumerate(results[:3], 1):  # Limit to top 3 for brevity
            path = result.get("path", "unknown")
            score = result.get("score", 0.0)
            content = result.get("content", "")
            
            # Truncate content if too long
            if len(content) > 500:
                content = content[:500] + "..."
            
            context += f"Snippet {i} (from {path}, relevance: {score:.2f}):\n```\n{content}\n```\n\n"
        
        return context
    
    def answer_question(self, question: str) -> Dict[str, Any]:
        """Answer a question about the codebase using RAG.
        
        Args:
            question: The question to answer
            
        Returns:
            Dictionary with answer and supporting information
        """
        # Process the task to get RAG results if appropriate
        result = self.process_task(question)
        
        if not result["rag_used"] or not result["rag_results"]:
            return {
                "answer": "I don't have enough information from the codebase to answer this question.",
                "rag_used": False
            }
        
        # In a real implementation, this would use an LLM to generate an answer
        # based on the RAG results. Here we'll just return the context.
        return {
            "answer": f"Here's what I found in the codebase:\n\n{result['enhanced_context']}",
            "rag_used": True,
            "rag_results": result["rag_results"]
        }
    
    def suggest_implementation(self, task_description: str) -> Dict[str, Any]:
        """Suggest an implementation for a coding task using RAG.
        
        Args:
            task_description: Description of the implementation task
            
        Returns:
            Dictionary with suggested implementation and supporting information
        """
        # Process the task to get RAG results if appropriate
        result = self.process_task(task_description)
        
        # Create a response based on whether RAG was used
        if result["rag_used"] and result["rag_results"]:
            # Find similar implementations in the codebase
            similar_code = result["enhanced_context"]
            
            # In a real implementation, this would use an LLM to generate code
            # based on the RAG results. Here we'll just return a template.
            return {
                "suggestion": (
                    f"Based on similar code in the repository, here's a suggested implementation:\n\n"
                    f"```python\n# Implementation based on similar patterns in the codebase\n"
                    f"def implement_task():\n    # TODO: Implement based on the examples below\n    pass\n```\n\n"
                    f"Reference code from the repository:\n{similar_code}"
                ),
                "rag_used": True,
                "rag_results": result["rag_results"]
            }
        else:
            return {
                "suggestion": "I don't have enough context from the codebase to suggest a specific implementation.",
                "rag_used": False
            }
    
    def explain_code(self, code_or_file: str) -> Dict[str, Any]:
        """Explain a code snippet or file using RAG for context.
        
        Args:
            code_or_file: Code snippet or file path to explain
            
        Returns:
            Dictionary with explanation and supporting information
        """
        # Check if input is a file path
        is_file_path = os.path.exists(code_or_file) and not code_or_file.count('\n')
        
        if is_file_path:
            # Read the file content
            try:
                with open(code_or_file, 'r', encoding='utf-8') as f:
                    code_content = f.read()
            except Exception as e:
                return {
                    "explanation": f"Error reading file: {str(e)}",
                    "rag_used": False
                }
        else:
            code_content = code_or_file
        
        # Search for similar code in the repository
        search_result = self.search_codebase(code_content)
        
        if search_result["status"] == "success" and search_result["results"]:
            # In a real implementation, this would use an LLM to generate an explanation
            # based on the RAG results. Here we'll just return a template.
            return {
                "explanation": (
                    f"Here's an explanation of the code:\n\n"
                    f"This code appears to be similar to other code in the repository. "
                    f"I found {len(search_result['results'])} similar code snippets that might provide context."
                ),
                "rag_used": True,
                "rag_results": search_result["results"]
            }
        else:
            return {
                "explanation": "I don't have enough context from the codebase to provide a detailed explanation.",
                "rag_used": False
            }
    
    def debug_code(self, code: str, error_message: Optional[str] = None) -> Dict[str, Any]:
        """Debug code using RAG to find similar patterns and solutions.
        
        Args:
            code: The code to debug
            error_message: Optional error message
            
        Returns:
            Dictionary with debugging suggestions and supporting information
        """
        # Create a search query from the code and error
        query = code
        if error_message:
            query += f" {error_message}"
        
        # Search for similar code and errors in the repository
        search_result = self.search_codebase(query)
        
        if search_result["status"] == "success" and search_result["results"]:
            # In a real implementation, this would use an LLM to generate debugging suggestions
            # based on the RAG results. Here we'll just return a template.
            return {
                "suggestions": (
                    f"Based on similar code in the repository, here are some debugging suggestions:\n\n"
                    f"1. Check for common patterns in similar code\n"
                    f"2. Look for error handling patterns\n"
                    f"3. Compare your implementation with working examples\n\n"
                    f"Similar code from the repository:\n{self._create_context_from_results(search_result['results'])}"
                ),
                "rag_used": True,
                "rag_results": search_result["results"]
            }
        else:
            return {
                "suggestions": "I don't have enough context from the codebase to provide specific debugging suggestions.",
                "rag_used": False
            }