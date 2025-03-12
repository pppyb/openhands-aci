"""Code search implementation for OpenHands ACI.

This module provides the necessary classes for code search in OpenHands.
"""

import os
import uuid
from typing import List, Dict, Any, Optional

from openhands.core.schema.action import ActionType
from openhands.core.schema.observation import ObservationType
from openhands.events.action import Action
from openhands.events.observation import Observation

from openhands_aci.tools.code_search_tool import code_search_tool


class CodeSearchAction(Action):
    """Search for relevant code in a codebase using semantic search."""
    
    action = ActionType.CODE_SEARCH
    query: str
    repo_path: str
    extensions: Optional[List[str]] = None
    k: int = 5
    thought: Optional[str] = None
    
    def __init__(
        self,
        query: str,
        repo_path: str,
        extensions: Optional[List[str]] = None,
        k: int = 5,
        thought: Optional[str] = None,
        **kwargs
    ):
        """Initialize a code search action.
        
        Args:
            query: Search query
            repo_path: Path to the repository
            extensions: List of file extensions to include (e.g., [".py", ".js"])
            k: Number of results to return
            thought: Optional thought process behind the action
        """
        super().__init__(**kwargs)
        self.query = query
        self.repo_path = repo_path
        self.extensions = extensions
        self.k = k
        self.thought = thought
        self.id = str(uuid.uuid4())


class CodeSearchObservation(Observation):
    """Result of a code search operation."""
    
    observation = ObservationType.CODE_SEARCH
    content: str
    results: List[Dict[str, Any]]
    
    def __init__(
        self,
        content: Optional[str] = None,
        results: List[Dict[str, Any]] = None,
        **kwargs
    ):
        """Initialize a code search observation.
        
        Args:
            content: Optional formatted content for display
            results: List of search results
        """
        super().__init__(**kwargs)
        self.results = results or []
        
        # If content is not provided, generate it from results
        if content is None:
            self.content = self._format_results(self.results)
        else:
            self.content = content
    
    def _format_results(self, results: List[Dict[str, Any]]) -> str:
        """Format search results for display.
        
        Args:
            results: List of search results
            
        Returns:
            Formatted string with search results
        """
        if not results:
            return "No relevant code found."
        
        formatted = []
        for i, result in enumerate(results):
            formatted.append(f"Result {i+1}: {result['file']} (Relevance score: {result['score']:.2f})")
            formatted.append("```")
            # Truncate content if too long
            content = result['content']
            if len(content) > 1000:
                content = content[:1000] + "...\n[content truncated]"
            formatted.append(content)
            formatted.append("```")
            formatted.append("")
        
        return "\n".join(formatted)


def execute_code_search(action: CodeSearchAction, mock_mode: bool = False) -> CodeSearchObservation:
    """Execute a code search action and return an observation.
    
    Args:
        action: Code search action to execute
        mock_mode: Whether to use mock mode for testing
        
    Returns:
        Code search observation with results
    """
    # Validate repo_path
    if not os.path.isdir(action.repo_path):
        return CodeSearchObservation(
            content=f"Error: Repository path '{action.repo_path}' is not a directory.",
            results=[],
            cause=action.id
        )
    
    # Execute code search
    try:
        # Check if we should use mock mode
        use_mock = mock_mode or os.environ.get('OPENHANDS_TEST_MOCK_MODE') == 'true'
        
        search_result = code_search_tool(
            query=action.query,
            repo_path=action.repo_path,
            extensions=action.extensions,
            k=action.k,
            mock_mode=use_mock
        )
        
        # Check for errors
        if "error" in search_result:
            return CodeSearchObservation(
                content=f"Error: {search_result['error']}",
                results=[],
                cause=action.id
            )
        
        # Return observation with results
        return CodeSearchObservation(
            content=None,  # Will be auto-generated from results
            results=search_result["results"],
            cause=action.id
        )
    except Exception as e:
        return CodeSearchObservation(
            content=f"Error executing code search: {str(e)}",
            results=[],
            cause=action.id
        )