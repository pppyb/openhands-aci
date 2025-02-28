"""
Enhanced linter module with RAG integration.

This module extends the basic linter functionality with RAG capabilities,
providing context-aware code linting and fixing.
"""

import os
from typing import Any, Dict, List, Optional, Union

from openhands_aci.agent import RAGAgent
from openhands_aci.config import get_config
from openhands_aci.linter import lint_file
from openhands_aci.events import subscribe, trigger
from openhands_aci.visualization import format_rag_context


class EnhancedLinter:
    """Enhanced linter with RAG integration.
    
    This class extends the basic linter functionality with RAG capabilities,
    providing context-aware code linting and fixing.
    """
    
    def __init__(
        self,
        repo_path: str,
        save_dir: Optional[str] = None,
        auto_initialize: Optional[bool] = None,
        register_events: bool = True
    ):
        """Initialize the enhanced linter.
        
        Args:
            repo_path: Path to the repository
            save_dir: Directory to save the search index
            auto_initialize: Whether to automatically initialize the index
            register_events: Whether to register event handlers
        """
        # Get configuration
        rag_config = get_config("rag")
        
        # Set defaults from config if not provided
        if save_dir is None:
            save_dir = os.path.join(repo_path, "code_search_index")
        
        if auto_initialize is None:
            auto_initialize = rag_config.get("auto_initialize", True)
        
        # Initialize RAG agent
        self.rag_agent = RAGAgent(
            repo_path=repo_path,
            save_dir=save_dir,
            auto_initialize=auto_initialize
        )
        
        # Register event handlers
        if register_events:
            self._register_event_handlers()
    
    def _register_event_handlers(self):
        """Register event handlers."""
        # Register for lint_request event
        subscribe("lint_request", self._on_lint_request)
        
        # Register for lint_issue event
        subscribe("lint_issue", self._on_lint_issue)
    
    def _on_lint_request(self, event_name: str, file_path: str, **kwargs) -> None:
        """Handle lint_request event.
        
        Args:
            event_name: Name of the event
            file_path: Path to the file to lint
            **kwargs: Additional arguments
        """
        # Perform enhanced linting
        lint_result = self.lint_with_context(file_path, **kwargs)
        
        # Trigger lint_result event
        trigger(
            "lint_result",
            file_path=file_path,
            result=lint_result,
            **kwargs
        )
    
    def _on_lint_issue(self, event_name: str, file_path: str, issue: Dict[str, Any], **kwargs) -> None:
        """Handle lint_issue event.
        
        Args:
            event_name: Name of the event
            file_path: Path to the file with the issue
            issue: Linting issue details
            **kwargs: Additional arguments
        """
        # Search for similar issues and fixes
        query = f"fix {issue['code']} {issue['message']}"
        search_result = self.rag_agent.search_codebase(query, k=3)
        
        if search_result["status"] == "success" and search_result["results"]:
            # Add fix suggestions to the issue
            issue["fix_suggestions"] = [
                {
                    "source": result["path"],
                    "code": result["content"],
                    "relevance": result["score"]
                }
                for result in search_result["results"]
            ]
            
            # Trigger lint_issue_enhanced event
            trigger(
                "lint_issue_enhanced",
                file_path=file_path,
                issue=issue,
                rag_results=search_result["results"],
                **kwargs
            )
    
    def lint_with_context(
        self,
        file_path: str,
        fix: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Lint a file with RAG context.
        
        Args:
            file_path: Path to the file to lint
            fix: Whether to fix issues
            **kwargs: Additional arguments to pass to lint_file
            
        Returns:
            Linting result
        """
        # Perform regular linting
        lint_result = lint_file(file_path, **kwargs)
        
        # If there are issues and fix is True, enhance with RAG
        if lint_result.get("issues") and fix:
            enhanced_issues = []
            
            for issue in lint_result["issues"]:
                # Construct a query for this issue
                query = f"fix {issue['code']} {issue['message']}"
                
                # Search for similar issues and fixes
                search_result = self.rag_agent.search_codebase(query, k=3)
                
                if search_result["status"] == "success" and search_result["results"]:
                    # Add fix suggestions to the issue
                    issue["fix_suggestions"] = [
                        {
                            "source": result["path"],
                            "code": result["content"],
                            "relevance": result["score"]
                        }
                        for result in search_result["results"]
                    ]
                
                enhanced_issues.append(issue)
            
            # Update the issues in the result
            lint_result["issues"] = enhanced_issues
            lint_result["rag_enhanced"] = True
        
        # Trigger lint_complete event
        trigger(
            "lint_complete",
            file_path=file_path,
            result=lint_result,
            fix=fix,
            **kwargs
        )
        
        return lint_result
    
    def suggest_fixes(
        self,
        file_path: str,
        issues: List[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, Any]:
        """Suggest fixes for linting issues with RAG.
        
        Args:
            file_path: Path to the file with issues
            issues: List of linting issues
            **kwargs: Additional arguments
            
        Returns:
            Dictionary with fix suggestions
        """
        suggestions = []
        
        for issue in issues:
            # Construct a query for this issue
            query = f"fix {issue['code']} {issue['message']} in {os.path.basename(file_path)}"
            
            # Process the task with RAG
            rag_result = self.rag_agent.process_task(query)
            
            if rag_result["rag_used"] and rag_result["rag_results"]:
                # Create a suggestion
                suggestion = {
                    "issue": issue,
                    "rag_results": rag_result["rag_results"],
                    "context": rag_result["enhanced_context"],
                    "fix": self._generate_fix_from_context(issue, rag_result["enhanced_context"])
                }
                
                suggestions.append(suggestion)
        
        result = {
            "file_path": file_path,
            "suggestions": suggestions,
            "status": "success" if suggestions else "no_suggestions"
        }
        
        # Trigger fix_suggestions event
        trigger(
            "fix_suggestions",
            file_path=file_path,
            issues=issues,
            suggestions=suggestions,
            **kwargs
        )
        
        return result
    
    def _generate_fix_from_context(
        self,
        issue: Dict[str, Any],
        context: str
    ) -> str:
        """Generate a fix for an issue based on RAG context.
        
        Args:
            issue: Linting issue
            context: RAG context
            
        Returns:
            Suggested fix
        """
        # In a real implementation, this would use an LLM to generate a fix
        # based on the issue and context. For now, we'll just return a placeholder.
        return f"# Suggested fix for {issue['code']}: {issue['message']}\n# See examples in context"


# Convenience functions that use an instance of EnhancedLinter
_linter_instance = None

def get_linter_instance(
    repo_path: Optional[str] = None,
    save_dir: Optional[str] = None,
    auto_initialize: Optional[bool] = None
) -> EnhancedLinter:
    """Get the global linter instance.
    
    Args:
        repo_path: Path to the repository
        save_dir: Directory to save the search index
        auto_initialize: Whether to automatically initialize the index
        
    Returns:
        Global linter instance
    """
    global _linter_instance
    
    if _linter_instance is None:
        if repo_path is None:
            # Try to determine repo path from current directory
            repo_path = os.getcwd()
        
        _linter_instance = EnhancedLinter(
            repo_path=repo_path,
            save_dir=save_dir,
            auto_initialize=auto_initialize
        )
    
    return _linter_instance

def lint_with_context(
    file_path: str,
    fix: bool = False,
    **kwargs
) -> Dict[str, Any]:
    """Lint a file with RAG context using the global linter instance."""
    linter = get_linter_instance()
    return linter.lint_with_context(file_path, fix, **kwargs)

def suggest_fixes(
    file_path: str,
    issues: List[Dict[str, Any]],
    **kwargs
) -> Dict[str, Any]:
    """Suggest fixes for linting issues with RAG using the global linter instance."""
    linter = get_linter_instance()
    return linter.suggest_fixes(file_path, issues, **kwargs)