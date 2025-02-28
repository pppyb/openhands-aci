"""
Visualization module for OpenHands ACI.

This module provides functions for formatting and visualizing results from
various components of OpenHands ACI.
"""

import json
import os
from typing import Any, Dict, List, Optional, Union

from openhands_aci.config import get_config


def format_search_results(
    results: List[Dict[str, Any]], 
    format_type: str = "markdown",
    max_results: Optional[int] = None,
    max_content_length: Optional[int] = None
) -> str:
    """Format search results for visualization.
    
    Args:
        results: List of search results
        format_type: Format type (markdown, html, json, text)
        max_results: Maximum number of results to include
        max_content_length: Maximum length of content to display
        
    Returns:
        Formatted search results
    """
    # Get configuration
    rag_config = get_config("rag")
    
    # Set defaults from config if not provided
    if max_results is None:
        max_results = rag_config.get("max_results", 5)
    
    if max_content_length is None:
        max_content_length = rag_config.get("max_content_length", 500)
    
    # Limit number of results
    results = results[:max_results]
    
    if format_type == "markdown":
        return _format_markdown(results, max_content_length)
    elif format_type == "html":
        return _format_html(results, max_content_length)
    elif format_type == "json":
        return _format_json(results)
    elif format_type == "text":
        return _format_text(results, max_content_length)
    else:
        raise ValueError(f"Unsupported format type: {format_type}")


def _format_markdown(results: List[Dict[str, Any]], max_content_length: int) -> str:
    """Format search results as Markdown.
    
    Args:
        results: List of search results
        max_content_length: Maximum length of content to display
        
    Returns:
        Markdown-formatted search results
    """
    output = "## Code Search Results\n\n"
    
    for i, result in enumerate(results, 1):
        path = result.get("path", "unknown")
        score = result.get("score", 0.0)
        content = result.get("content", "")
        
        # Truncate content if too long
        if len(content) > max_content_length:
            content = content[:max_content_length] + "..."
        
        # Determine language for syntax highlighting
        ext = os.path.splitext(path)[1].lstrip('.')
        lang = ext if ext else "text"
        
        output += f"### Result {i}: {path} (Score: {score:.2f})\n\n"
        output += f"```{lang}\n{content}\n```\n\n"
    
    return output


def _format_html(results: List[Dict[str, Any]], max_content_length: int) -> str:
    """Format search results as HTML.
    
    Args:
        results: List of search results
        max_content_length: Maximum length of content to display
        
    Returns:
        HTML-formatted search results
    """
    output = "<div class='search-results'>\n"
    output += "<h2>Code Search Results</h2>\n"
    
    for i, result in enumerate(results, 1):
        path = result.get("path", "unknown")
        score = result.get("score", 0.0)
        content = result.get("content", "")
        
        # Truncate content if too long
        if len(content) > max_content_length:
            content = content[:max_content_length] + "..."
        
        # Escape HTML special characters
        content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        # Determine language for syntax highlighting
        ext = os.path.splitext(path)[1].lstrip('.')
        
        output += f"<div class='result' data-score='{score:.2f}'>\n"
        output += f"<h3>Result {i}: {path} (Score: {score:.2f})</h3>\n"
        output += f"<pre><code class='language-{ext}'>{content}</code></pre>\n"
        output += "</div>\n"
    
    output += "</div>"
    return output


def _format_json(results: List[Dict[str, Any]]) -> str:
    """Format search results as JSON.
    
    Args:
        results: List of search results
        
    Returns:
        JSON-formatted search results
    """
    return json.dumps(results, indent=2)


def _format_text(results: List[Dict[str, Any]], max_content_length: int) -> str:
    """Format search results as plain text.
    
    Args:
        results: List of search results
        max_content_length: Maximum length of content to display
        
    Returns:
        Text-formatted search results
    """
    output = "CODE SEARCH RESULTS\n" + "=" * 20 + "\n\n"
    
    for i, result in enumerate(results, 1):
        path = result.get("path", "unknown")
        score = result.get("score", 0.0)
        content = result.get("content", "")
        
        # Truncate content if too long
        if len(content) > max_content_length:
            content = content[:max_content_length] + "..."
        
        output += f"Result {i}: {path} (Score: {score:.2f})\n"
        output += "-" * 40 + "\n"
        output += content + "\n\n"
    
    return output


def format_rag_context(
    context: str,
    format_type: str = "markdown",
    include_header: bool = True
) -> str:
    """Format RAG context for inclusion in prompts or responses.
    
    Args:
        context: RAG context to format
        format_type: Format type (markdown, html, text)
        include_header: Whether to include a header
        
    Returns:
        Formatted RAG context
    """
    if format_type == "markdown":
        if include_header:
            return f"## Relevant Code Context\n\n{context}"
        return context
    elif format_type == "html":
        if include_header:
            return f"<h2>Relevant Code Context</h2>\n<div class='rag-context'>{context}</div>"
        return f"<div class='rag-context'>{context}</div>"
    elif format_type == "text":
        if include_header:
            return f"RELEVANT CODE CONTEXT\n{'=' * 20}\n\n{context}"
        return context
    else:
        raise ValueError(f"Unsupported format type: {format_type}")


def format_task_result(
    task: str,
    rag_used: bool,
    rag_results: Optional[List[Dict[str, Any]]],
    response: str,
    format_type: str = "markdown"
) -> str:
    """Format task result for visualization.
    
    Args:
        task: Task description
        rag_used: Whether RAG was used
        rag_results: RAG results (if used)
        response: Response to the task
        format_type: Format type (markdown, html, json, text)
        
    Returns:
        Formatted task result
    """
    if format_type == "markdown":
        output = f"## Task\n\n{task}\n\n"
        
        if rag_used and rag_results:
            output += f"## RAG Results\n\n"
            output += f"Found {len(rag_results)} relevant code snippets.\n\n"
            output += _format_markdown(rag_results, 300)  # Shorter snippets
        
        output += f"## Response\n\n{response}"
        return output
    
    elif format_type == "html":
        output = f"<h2>Task</h2>\n<p>{task}</p>\n"
        
        if rag_used and rag_results:
            output += f"<h2>RAG Results</h2>\n"
            output += f"<p>Found {len(rag_results)} relevant code snippets.</p>\n"
            output += _format_html(rag_results, 300)  # Shorter snippets
        
        output += f"<h2>Response</h2>\n<div class='response'>{response}</div>"
        return output
    
    elif format_type == "json":
        return json.dumps({
            "task": task,
            "rag_used": rag_used,
            "rag_results": rag_results if rag_used and rag_results else None,
            "response": response
        }, indent=2)
    
    elif format_type == "text":
        output = f"TASK\n{'=' * 20}\n{task}\n\n"
        
        if rag_used and rag_results:
            output += f"RAG RESULTS\n{'=' * 20}\n"
            output += f"Found {len(rag_results)} relevant code snippets.\n\n"
            output += _format_text(rag_results, 300)  # Shorter snippets
        
        output += f"RESPONSE\n{'=' * 20}\n{response}"
        return output
    
    else:
        raise ValueError(f"Unsupported format type: {format_type}")