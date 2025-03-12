"""Function calling integration for code search in OpenHands.

This module provides the necessary functions to register code search as a tool
in the OpenHands function calling system.
"""

from typing import Dict, Any, List, Optional, Callable

from openhands.agenthub.codeact_agent.function_calling import register_tool
from openhands.core.schema.action import ActionType
from openhands.events import EventSource
from openhands.events.action import Action

from openhands_aci.rag.code_search import CodeSearchAction, execute_code_search


def code_search_function(
    query: str,
    repo_path: str,
    extensions: Optional[List[str]] = None,
    k: int = 5,
    thought: Optional[str] = None,
) -> Dict[str, Any]:
    """Search for relevant code in a codebase using semantic search.
    
    Args:
        query: Search query to find relevant code
        repo_path: Path to the repository to search in
        extensions: List of file extensions to include (e.g., [".py", ".js"])
        k: Number of results to return
        thought: Optional thought process behind the search
        
    Returns:
        Dictionary with function call information
    """
    return {
        "name": "code_search",
        "action": CodeSearchAction(
            query=query,
            repo_path=repo_path,
            extensions=extensions,
            k=k,
            thought=thought,
        ),
        "action_type": ActionType.CODE_SEARCH,
    }


def register_code_search_tool() -> Dict[str, Any]:
    """Register code search as a tool in the OpenHands function calling system.
    
    Returns:
        Dictionary with tool registration information
    """
    return register_tool(
        name="code_search",
        description="Search for relevant code in a codebase using semantic search.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query to find relevant code",
                },
                "repo_path": {
                    "type": "string",
                    "description": "Path to the repository to search in",
                },
                "extensions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of file extensions to include (e.g., [\".py\", \".js\"])",
                },
                "k": {
                    "type": "integer",
                    "description": "Number of results to return",
                },
                "thought": {
                    "type": "string",
                    "description": "Optional thought process behind the search",
                },
            },
            "required": ["query", "repo_path"],
        },
        function=code_search_function,
        executor=execute_code_search,
        event_source=EventSource.AGENT,
    )


def get_code_search_tools() -> List[Dict[str, Any]]:
    """Get all code search tools.
    
    Returns:
        List of tool registration dictionaries
    """
    return [register_code_search_tool()]


def register_code_search_tools(register_fn: Callable[[Dict[str, Any]], None]) -> None:
    """Register all code search tools using the provided registration function.
    
    Args:
        register_fn: Function to register a tool
    """
    for tool in get_code_search_tools():
        register_fn(tool)