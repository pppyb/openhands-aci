"""
Enhanced editor module with RAG integration.

This module extends the basic editor functionality with RAG capabilities,
providing context-aware code editing.
"""

import os
from typing import Any, Dict, List, Optional, Union

from openhands_aci.agent import RAGAgent
from openhands_aci.config import get_config
from openhands_aci.editor import edit_file, create_file, str_replace
from openhands_aci.events import subscribe, trigger
from openhands_aci.visualization import format_rag_context


class EnhancedEditor:
    """Enhanced editor with RAG integration.
    
    This class extends the basic editor functionality with RAG capabilities,
    providing context-aware code editing.
    """
    
    def __init__(
        self,
        repo_path: str,
        save_dir: Optional[str] = None,
        auto_initialize: Optional[bool] = None,
        register_events: bool = True
    ):
        """Initialize the enhanced editor.
        
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
        # Register for file_save event
        subscribe("file_save", self._on_file_save)
        
        # Register for edit_request event
        subscribe("edit_request", self._on_edit_request)
    
    def _on_file_save(self, event_name: str, file_path: str, content: str, **kwargs) -> None:
        """Handle file_save event.
        
        Args:
            event_name: Name of the event
            file_path: Path to the saved file
            content: Content of the saved file
            **kwargs: Additional arguments
        """
        # Only process certain file types
        if not self._should_process_file(file_path):
            return
        
        # Trigger a code search for similar files
        search_result = self.rag_agent.search_codebase(content, k=3)
        
        if search_result["status"] == "success" and search_result["results"]:
            # Trigger a search_results event
            trigger(
                "search_results",
                query=content,
                results=search_result["results"],
                source="file_save",
                file_path=file_path
            )
    
    def _on_edit_request(self, event_name: str, file_path: str, task: str, **kwargs) -> None:
        """Handle edit_request event.
        
        Args:
            event_name: Name of the event
            file_path: Path to the file to edit
            task: Edit task description
            **kwargs: Additional arguments
        """
        # Process the task with RAG
        rag_result = self.rag_agent.process_task(task)
        
        if rag_result["rag_used"] and rag_result["rag_results"]:
            # Add RAG context to kwargs
            kwargs["context"] = rag_result["enhanced_context"]
            
            # Trigger edit_with_context event
            trigger(
                "edit_with_context",
                file_path=file_path,
                task=task,
                rag_results=rag_result["rag_results"],
                **kwargs
            )
    
    def _should_process_file(self, file_path: str) -> bool:
        """Determine if a file should be processed.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the file should be processed, False otherwise
        """
        # Get configuration
        rag_config = get_config("rag")
        extensions = rag_config.get("default_extensions", [])
        
        # Check if file has a supported extension
        _, ext = os.path.splitext(file_path)
        return ext in extensions
    
    def edit_with_context(
        self,
        file_path: str,
        task: str,
        context: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Edit a file with RAG context.
        
        Args:
            file_path: Path to the file to edit
            task: Edit task description
            context: Optional context to use (if not provided, will be generated from RAG)
            **kwargs: Additional arguments to pass to edit_file
            
        Returns:
            Edit result
        """
        # If context is not provided, generate it from RAG
        if context is None:
            rag_result = self.rag_agent.process_task(task)
            
            if rag_result["rag_used"] and rag_result["rag_results"]:
                context = rag_result["enhanced_context"]
        
        # Format the context for inclusion in the edit
        if context:
            # Format the task with context
            enhanced_task = f"{task}\n\n{format_rag_context(context)}"
        else:
            enhanced_task = task
        
        # Edit the file
        edit_result = edit_file(file_path, enhanced_task, **kwargs)
        
        # Trigger file_edited event
        trigger(
            "file_edited",
            file_path=file_path,
            task=task,
            context=context,
            result=edit_result
        )
        
        return edit_result
    
    def create_with_context(
        self,
        file_path: str,
        task: str,
        context: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a file with RAG context.
        
        Args:
            file_path: Path to the file to create
            task: Creation task description
            context: Optional context to use (if not provided, will be generated from RAG)
            **kwargs: Additional arguments to pass to create_file
            
        Returns:
            Creation result
        """
        # If context is not provided, generate it from RAG
        if context is None:
            # For file creation, search for similar files based on the task and file name
            file_name = os.path.basename(file_path)
            search_query = f"create {file_name} {task}"
            
            rag_result = self.rag_agent.process_task(search_query)
            
            if rag_result["rag_used"] and rag_result["rag_results"]:
                context = rag_result["enhanced_context"]
        
        # Format the context for inclusion in the creation
        if context:
            # Format the task with context
            enhanced_task = f"{task}\n\n{format_rag_context(context)}"
        else:
            enhanced_task = task
        
        # Create the file
        create_result = create_file(file_path, enhanced_task, **kwargs)
        
        # Trigger file_created event
        trigger(
            "file_created",
            file_path=file_path,
            task=task,
            context=context,
            result=create_result
        )
        
        return create_result
    
    def str_replace_with_context(
        self,
        file_path: str,
        old_str: str,
        task: str,
        context: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Replace a string in a file with RAG context.
        
        Args:
            file_path: Path to the file
            old_str: String to replace
            task: Replacement task description
            context: Optional context to use (if not provided, will be generated from RAG)
            **kwargs: Additional arguments to pass to str_replace
            
        Returns:
            Replacement result
        """
        # If context is not provided, generate it from RAG
        if context is None:
            # For string replacement, include the old string in the search query
            search_query = f"replace code: {old_str} with {task}"
            
            rag_result = self.rag_agent.process_task(search_query)
            
            if rag_result["rag_used"] and rag_result["rag_results"]:
                context = rag_result["enhanced_context"]
        
        # Format the context for inclusion in the replacement
        if context:
            # Format the task with context
            enhanced_task = f"{task}\n\n{format_rag_context(context)}"
        else:
            enhanced_task = task
        
        # Replace the string
        replace_result = str_replace(file_path, old_str, enhanced_task, **kwargs)
        
        # Trigger string_replaced event
        trigger(
            "string_replaced",
            file_path=file_path,
            old_str=old_str,
            task=task,
            context=context,
            result=replace_result
        )
        
        return replace_result


# Convenience functions that use an instance of EnhancedEditor
_editor_instance = None

def get_editor_instance(
    repo_path: Optional[str] = None,
    save_dir: Optional[str] = None,
    auto_initialize: Optional[bool] = None
) -> EnhancedEditor:
    """Get the global editor instance.
    
    Args:
        repo_path: Path to the repository
        save_dir: Directory to save the search index
        auto_initialize: Whether to automatically initialize the index
        
    Returns:
        Global editor instance
    """
    global _editor_instance
    
    if _editor_instance is None:
        if repo_path is None:
            # Try to determine repo path from current directory
            repo_path = os.getcwd()
        
        _editor_instance = EnhancedEditor(
            repo_path=repo_path,
            save_dir=save_dir,
            auto_initialize=auto_initialize
        )
    
    return _editor_instance

def edit_with_context(
    file_path: str,
    task: str,
    context: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """Edit a file with RAG context using the global editor instance."""
    editor = get_editor_instance()
    return editor.edit_with_context(file_path, task, context, **kwargs)

def create_with_context(
    file_path: str,
    task: str,
    context: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """Create a file with RAG context using the global editor instance."""
    editor = get_editor_instance()
    return editor.create_with_context(file_path, task, context, **kwargs)

def str_replace_with_context(
    file_path: str,
    old_str: str,
    task: str,
    context: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """Replace a string in a file with RAG context using the global editor instance."""
    editor = get_editor_instance()
    return editor.str_replace_with_context(file_path, old_str, task, context, **kwargs)