"""
Configuration module for OpenHands ACI.

This module provides configuration settings for various components of OpenHands ACI.
"""

import os
from typing import Dict, Any, List

# RAG configuration
RAG_CONFIG: Dict[str, Any] = {
    # Embedding model settings
    "default_embedding_model": os.getenv("OPENHANDS_RAG_MODEL", "BAAI/bge-base-en-v1.5"),
    "embedding_dimension": 768,  # Default dimension for the embedding model
    
    # Indexing settings
    "auto_initialize": True,
    "default_extensions": [".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".hpp"],
    "exclude_dirs": [".git", "__pycache__", "node_modules", "venv", ".venv", "env"],
    "batch_size": 32,  # Batch size for embedding generation
    
    # Search settings
    "rag_threshold": 0.6,  # Threshold for deciding when to use RAG (0.0-1.0)
    "max_results": 5,  # Maximum number of results to return
    "min_score": 0.5,  # Minimum score for a result to be considered relevant
    
    # Caching settings
    "cache_results": True,
    "cache_ttl": 3600,  # Cache time-to-live in seconds
    
    # Event settings
    "event_triggers": ["file_save", "task_start", "error_occur", "code_review"],
    
    # Integration settings
    "auto_enhance_editor": True,
    "auto_enhance_linter": True,
    "auto_enhance_tests": True,
    
    # Visualization settings
    "default_format": "markdown",  # Default format for result visualization
    "max_content_length": 500,  # Maximum length of content to display
}

# Editor configuration
EDITOR_CONFIG: Dict[str, Any] = {
    "default_indent": 4,
    "max_line_length": 88,
    "auto_format": True,
}

# Linter configuration
LINTER_CONFIG: Dict[str, Any] = {
    "auto_fix": True,
    "strict_mode": False,
    "ignore_rules": [],
}

# Utility configuration
UTILS_CONFIG: Dict[str, Any] = {
    "shell_timeout": 30,  # Timeout for shell commands in seconds
    "max_output_length": 1000,  # Maximum length of command output to capture
}

def get_config(section: str) -> Dict[str, Any]:
    """Get configuration for a specific section.
    
    Args:
        section: The configuration section to retrieve
        
    Returns:
        Configuration dictionary for the specified section
    """
    config_map = {
        "rag": RAG_CONFIG,
        "editor": EDITOR_CONFIG,
        "linter": LINTER_CONFIG,
        "utils": UTILS_CONFIG,
    }
    
    return config_map.get(section, {})

def update_config(section: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update configuration for a specific section.
    
    Args:
        section: The configuration section to update
        updates: Dictionary of configuration updates
        
    Returns:
        Updated configuration dictionary
    """
    config = get_config(section)
    
    if not config:
        return {}
    
    # Update the configuration
    for key, value in updates.items():
        if key in config:
            config[key] = value
    
    return config