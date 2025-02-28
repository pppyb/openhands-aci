"""
Workflow module for OpenHands ACI.

This module provides integrated workflows that combine multiple components
of OpenHands ACI, including RAG, editing, linting, and more.
"""

import os
import logging
from typing import Any, Dict, List, Optional, Union

from openhands_aci.agent import RAGAgent
from openhands_aci.config import get_config
from openhands_aci.editor.enhanced_editor import EnhancedEditor
from openhands_aci.linter.enhanced_linter import EnhancedLinter
from openhands_aci.events import subscribe, trigger
from openhands_aci.utils.shell import run_command
from openhands_aci.visualization import format_task_result

# Configure logging
logger = logging.getLogger(__name__)


class IntegratedWorkflow:
    """Integrated workflow that combines multiple OpenHands components.
    
    This class provides methods for executing common development workflows
    with RAG integration.
    """
    
    def __init__(
        self,
        repo_path: str,
        save_dir: Optional[str] = None,
        auto_initialize: Optional[bool] = None,
        register_events: bool = True
    ):
        """Initialize the integrated workflow.
        
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
        
        # Initialize components
        self.repo_path = repo_path
        self.rag_agent = RAGAgent(
            repo_path=repo_path,
            save_dir=save_dir,
            auto_initialize=auto_initialize
        )
        self.editor = EnhancedEditor(
            repo_path=repo_path,
            save_dir=save_dir,
            auto_initialize=auto_initialize,
            register_events=register_events
        )
        self.linter = EnhancedLinter(
            repo_path=repo_path,
            save_dir=save_dir,
            auto_initialize=auto_initialize,
            register_events=register_events
        )
        
        # Register event handlers
        if register_events:
            self._register_event_handlers()
    
    def _register_event_handlers(self):
        """Register event handlers."""
        # Register for task_request event
        subscribe("task_request", self._on_task_request)
        
        # Register for workflow_complete event
        subscribe("workflow_complete", self._on_workflow_complete)
    
    def _on_task_request(self, event_name: str, task: str, **kwargs) -> None:
        """Handle task_request event.
        
        Args:
            event_name: Name of the event
            task: Task description
            **kwargs: Additional arguments
        """
        # Execute the task
        result = self.execute_task(task, **kwargs)
        
        # Trigger task_result event
        trigger(
            "task_result",
            task=task,
            result=result,
            **kwargs
        )
    
    def _on_workflow_complete(self, event_name: str, workflow: str, result: Dict[str, Any], **kwargs) -> None:
        """Handle workflow_complete event.
        
        Args:
            event_name: Name of the event
            workflow: Workflow name
            result: Workflow result
            **kwargs: Additional arguments
        """
        logger.info(f"Workflow {workflow} completed with status: {result.get('status')}")
    
    def execute_task(
        self,
        task: str,
        file_paths: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute a development task.
        
        Args:
            task: Task description
            file_paths: Optional list of file paths to work with
            **kwargs: Additional arguments
            
        Returns:
            Task execution result
        """
        # Process the task with RAG
        rag_result = self.rag_agent.process_task(task)
        
        # If file paths are not provided, try to identify them from the task
        if file_paths is None:
            file_paths = self._identify_files(task, rag_result)
        
        # If still no file paths, return an error
        if not file_paths:
            return {
                "status": "error",
                "message": "Could not identify files to work with",
                "task": task,
                "rag_used": rag_result["rag_used"],
                "rag_results": rag_result.get("rag_results")
            }
        
        # Execute the task on each file
        file_results = []
        for file_path in file_paths:
            # Check if the file exists
            file_exists = os.path.exists(file_path)
            
            if file_exists:
                # Edit existing file
                edit_result = self.editor.edit_with_context(
                    file_path=file_path,
                    task=task,
                    context=rag_result.get("enhanced_context"),
                    **kwargs
                )
                
                # Lint the file
                lint_result = self.linter.lint_with_context(
                    file_path=file_path,
                    fix=True,
                    **kwargs
                )
                
                file_results.append({
                    "file_path": file_path,
                    "action": "edit",
                    "edit_result": edit_result,
                    "lint_result": lint_result
                })
            else:
                # Create new file
                create_result = self.editor.create_with_context(
                    file_path=file_path,
                    task=task,
                    context=rag_result.get("enhanced_context"),
                    **kwargs
                )
                
                # Lint the file if creation was successful
                lint_result = None
                if create_result.get("status") == "success":
                    lint_result = self.linter.lint_with_context(
                        file_path=file_path,
                        fix=True,
                        **kwargs
                    )
                
                file_results.append({
                    "file_path": file_path,
                    "action": "create",
                    "create_result": create_result,
                    "lint_result": lint_result
                })
        
        # Run tests if applicable
        test_result = self._run_tests(file_paths, **kwargs)
        
        # Prepare the result
        result = {
            "status": "success",
            "task": task,
            "rag_used": rag_result["rag_used"],
            "rag_results": rag_result.get("rag_results"),
            "file_results": file_results,
            "test_result": test_result
        }
        
        # Trigger workflow_complete event
        trigger(
            "workflow_complete",
            workflow="execute_task",
            task=task,
            result=result,
            **kwargs
        )
        
        return result
    
    def _identify_files(
        self,
        task: str,
        rag_result: Dict[str, Any]
    ) -> List[str]:
        """Identify files to work with based on the task and RAG results.
        
        Args:
            task: Task description
            rag_result: RAG result
            
        Returns:
            List of file paths
        """
        file_paths = []
        
        # Extract file paths from RAG results
        if rag_result["rag_used"] and rag_result.get("rag_results"):
            # Get file paths from the top 3 results
            for result in rag_result["rag_results"][:3]:
                if "path" in result:
                    file_path = os.path.join(self.repo_path, result["path"])
                    if file_path not in file_paths:
                        file_paths.append(file_path)
        
        # If no files were found, try to extract from the task
        if not file_paths:
            # Look for file paths in the task
            # This is a simple implementation; in a real system, this would be more sophisticated
            words = task.split()
            for word in words:
                if "." in word and not word.startswith(("http:", "https:")):
                    # Check if it's a file with a supported extension
                    _, ext = os.path.splitext(word)
                    if ext in get_config("rag").get("default_extensions", []):
                        file_path = os.path.join(self.repo_path, word)
                        if file_path not in file_paths:
                            file_paths.append(file_path)
        
        return file_paths
    
    def _run_tests(
        self,
        file_paths: List[str],
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Run tests for the modified files.
        
        Args:
            file_paths: List of file paths
            **kwargs: Additional arguments
            
        Returns:
            Test result, or None if tests were not run
        """
        # Check if tests should be run
        run_tests = kwargs.get("run_tests", True)
        if not run_tests:
            return None
        
        # Determine test files
        test_files = []
        for file_path in file_paths:
            # Skip test files themselves
            if "test" in file_path:
                continue
            
            # Try to find a corresponding test file
            base_name = os.path.basename(file_path)
            name, ext = os.path.splitext(base_name)
            
            # Check for test_*.py pattern
            test_file = os.path.join(os.path.dirname(file_path), f"test_{name}{ext}")
            if os.path.exists(test_file):
                test_files.append(test_file)
            
            # Check for *_test.py pattern
            test_file = os.path.join(os.path.dirname(file_path), f"{name}_test{ext}")
            if os.path.exists(test_file):
                test_files.append(test_file)
            
            # Check for tests/test_*.py pattern
            test_file = os.path.join(self.repo_path, "tests", f"test_{name}{ext}")
            if os.path.exists(test_file):
                test_files.append(test_file)
        
        # If no test files were found, return None
        if not test_files:
            return None
        
        # Run tests
        test_results = []
        for test_file in test_files:
            # Run the test
            command_result = run_command(f"pytest {test_file} -v")
            
            test_results.append({
                "test_file": test_file,
                "command_result": command_result
            })
        
        return {
            "status": "success",
            "test_files": test_files,
            "test_results": test_results
        }
    
    def format_result(
        self,
        result: Dict[str, Any],
        format_type: str = "markdown"
    ) -> str:
        """Format a task result for display.
        
        Args:
            result: Task result
            format_type: Format type (markdown, html, json, text)
            
        Returns:
            Formatted result
        """
        task = result.get("task", "")
        rag_used = result.get("rag_used", False)
        rag_results = result.get("rag_results", [])
        
        # Create a summary of the result
        summary = []
        
        # Add file results
        file_results = result.get("file_results", [])
        for file_result in file_results:
            file_path = file_result.get("file_path", "")
            action = file_result.get("action", "")
            
            if action == "edit":
                edit_result = file_result.get("edit_result", {})
                status = edit_result.get("status", "unknown")
                summary.append(f"Edited {file_path}: {status}")
            elif action == "create":
                create_result = file_result.get("create_result", {})
                status = create_result.get("status", "unknown")
                summary.append(f"Created {file_path}: {status}")
            
            # Add lint result
            lint_result = file_result.get("lint_result", {})
            if lint_result:
                issues = lint_result.get("issues", [])
                summary.append(f"Linted {file_path}: {len(issues)} issues found")
        
        # Add test result
        test_result = result.get("test_result", {})
        if test_result:
            test_results = test_result.get("test_results", [])
            for test in test_results:
                test_file = test.get("test_file", "")
                command_result = test.get("command_result", {})
                status = command_result.get("status", "unknown")
                summary.append(f"Tested {test_file}: {status}")
        
        # Format the summary
        response = "\n".join(summary)
        
        return format_task_result(task, rag_used, rag_results, response, format_type)


# Convenience functions that use an instance of IntegratedWorkflow
_workflow_instance = None

def get_workflow_instance(
    repo_path: Optional[str] = None,
    save_dir: Optional[str] = None,
    auto_initialize: Optional[bool] = None
) -> IntegratedWorkflow:
    """Get the global workflow instance.
    
    Args:
        repo_path: Path to the repository
        save_dir: Directory to save the search index
        auto_initialize: Whether to automatically initialize the index
        
    Returns:
        Global workflow instance
    """
    global _workflow_instance
    
    if _workflow_instance is None:
        if repo_path is None:
            # Try to determine repo path from current directory
            repo_path = os.getcwd()
        
        _workflow_instance = IntegratedWorkflow(
            repo_path=repo_path,
            save_dir=save_dir,
            auto_initialize=auto_initialize
        )
    
    return _workflow_instance

def execute_task(
    task: str,
    file_paths: Optional[List[str]] = None,
    **kwargs
) -> Dict[str, Any]:
    """Execute a development task using the global workflow instance."""
    workflow = get_workflow_instance()
    return workflow.execute_task(task, file_paths, **kwargs)

def format_result(
    result: Dict[str, Any],
    format_type: str = "markdown"
) -> str:
    """Format a task result for display using the global workflow instance."""
    workflow = get_workflow_instance()
    return workflow.format_result(result, format_type)