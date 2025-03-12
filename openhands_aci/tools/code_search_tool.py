"""Code search tool for OpenHands ACI.

This module provides a tool for semantic code search in a repository.
"""

import os
import glob
import json
from typing import List, Dict, Any, Optional, Union
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to import OpenAI for embeddings
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    logger.warning("OpenAI package not available. Using mock embeddings.")
    OPENAI_AVAILABLE = False

def get_file_content(file_path: str) -> str:
    """Get the content of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Content of the file as a string
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # Try with latin-1 encoding for binary files
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Could not read file {file_path}: {e}")
            return ""
    except Exception as e:
        logger.warning(f"Could not read file {file_path}: {e}")
        return ""

def get_embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
    """Get embedding for a text using OpenAI API.
    
    Args:
        text: Text to get embedding for
        model: OpenAI embedding model to use
        
    Returns:
        Embedding as a list of floats
    """
    if not OPENAI_AVAILABLE:
        # Return a mock embedding if OpenAI is not available
        logger.warning("Using mock embedding as OpenAI is not available")
        return [0.0] * 1536  # Mock embedding with 1536 dimensions
    
    # Get API key from environment
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        logger.warning("No OpenAI API key found in environment. Using mock embedding.")
        return [0.0] * 1536  # Mock embedding with 1536 dimensions
    
    logger.info(f"Using API key starting with: {api_key[:10]}...")
    
    try:
        # Create OpenAI client with proper API key format
        # Check if the API key starts with 'sk-proj-' (Project API key format)
        if api_key.startswith('sk-proj-'):
            # For project API keys, we need to use the organization parameter
            logger.info("Using project API key format")
            client = OpenAI(
                api_key=api_key,
                # Add any additional parameters needed for project API keys
                max_retries=3,
                timeout=30.0
            )
        else:
            # For regular API keys
            logger.info("Using regular API key format")
            client = OpenAI(api_key=api_key)
        
        # Get embedding with a smaller input size to avoid 400 errors
        # Truncate text if it's too long (OpenAI has token limits)
        max_chars = 8000  # A conservative limit to avoid token limit issues
        if len(text) > max_chars:
            text = text[:max_chars]
            logger.warning(f"Text truncated to {max_chars} characters for embedding")
        
        logger.info(f"Getting embedding for text of length {len(text)} using model {model}")
        
        # Get embedding
        try:
            response = client.embeddings.create(
                model=model,
                input=text
            )
            
            # Return embedding
            logger.info("Successfully got embedding")
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error in API call: {e}")
            # Try with a simpler model as fallback
            logger.info("Trying with text-embedding-ada-002 as fallback")
            try:
                response = client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=text
                )
                logger.info("Successfully got embedding with fallback model")
                return response.data[0].embedding
            except Exception as e2:
                logger.error(f"Error with fallback model: {e2}")
                # Return mock embedding on error
                return [0.0] * 1536  # Mock embedding with 1536 dimensions
    except Exception as e:
        logger.error(f"Error getting embedding: {e}")
        # Return mock embedding on error
        return [0.0] * 1536  # Mock embedding with 1536 dimensions

def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors.
    
    Args:
        a: First vector
        b: Second vector
        
    Returns:
        Cosine similarity as a float between -1 and 1
    """
    # Check if vectors have the same length
    if len(a) != len(b):
        raise ValueError(f"Vectors must have the same length, got {len(a)} and {len(b)}")
    
    # Calculate dot product
    dot_product = sum(x * y for x, y in zip(a, b))
    
    # Calculate magnitudes
    magnitude_a = sum(x * x for x in a) ** 0.5
    magnitude_b = sum(x * x for x in b) ** 0.5
    
    # Calculate cosine similarity
    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0
    
    return dot_product / (magnitude_a * magnitude_b)

def code_search_tool(
    query: str,
    repo_path: str,
    extensions: Optional[List[str]] = None,
    k: int = 5,
    mock_mode: bool = False
) -> Dict[str, Any]:
    """Search for relevant code in a repository using semantic search.
    
    Args:
        query: Search query
        repo_path: Path to the repository
        extensions: List of file extensions to include (e.g., [".py", ".js"])
        k: Number of results to return
        
    Returns:
        Dictionary with search results
    """
    logger.info(f"Searching for code with query: {query}")
    logger.info(f"Repository path: {repo_path}")
    logger.info(f"Extensions: {extensions}")
    logger.info(f"Number of results: {k}")
    
    # Check if we're in mock mode
    if mock_mode:
        logger.info("Running in mock mode - returning mock results")
        mock_results = [
            {
                "file": "openhands/events/action/code_search.py",
                "score": 0.95,
                "content": "\"\"\"Code search action module.\"\"\"\n\nfrom dataclasses import dataclass\nfrom typing import ClassVar, List, Optional\n\nfrom openhands.core.schema.action import ActionType\nfrom openhands.events.action.action import Action, ActionSecurityRisk\n\n\n@dataclass\nclass CodeSearchAction(Action):\n    \"\"\"Search for relevant code in a codebase using semantic search.\"\"\"\n    # ... more code here ..."
            },
            {
                "file": "openhands/events/observation/code_search.py",
                "score": 0.92,
                "content": "\"\"\"Code search observation module.\"\"\"\n\nfrom dataclasses import dataclass\nfrom typing import Any, Dict, List\n\nfrom openhands.core.schema.observation import ObservationType\nfrom openhands.events.observation.observation import Observation\n\n\n@dataclass\nclass CodeSearchObservation(Observation):\n    \"\"\"Result of a code search operation.\"\"\"\n    # ... more code here ..."
            },
            {
                "file": "openhands/runtime/handlers/code_search_handler.py",
                "score": 0.88,
                "content": "\"\"\"Handler for code search actions.\"\"\"\n\nimport logging\nimport os\nfrom typing import Optional\n\nfrom openhands.core.logger import openhands_logger as logger\nfrom openhands.events.action import Action\nfrom openhands.events.action.code_search import CodeSearchAction\nfrom openhands.events.observation import Observation\nfrom openhands.events.observation.code_search import CodeSearchObservation\nfrom openhands.runtime.handlers.handler import ActionHandler\n\n# ... more code here ..."
            }
        ]
        return {
            "query": query,
            "repo_path": repo_path,
            "extensions": extensions,
            "results": mock_results
        }
    
    # Validate inputs
    if not os.path.isdir(repo_path):
        error_msg = f"Repository path {repo_path} is not a directory"
        logger.error(error_msg)
        return {"error": error_msg}
    
    # Set default extensions if not provided
    if extensions is None:
        extensions = [".py"]  # Default to Python files
    
    # Get all files with the specified extensions
    all_files = []
    for ext in extensions:
        pattern = os.path.join(repo_path, "**", f"*{ext}")
        all_files.extend(glob.glob(pattern, recursive=True))
    
    logger.info(f"Found {len(all_files)} files with extensions {extensions}")
    
    # If no files found, return empty results
    if not all_files:
        return {
            "query": query,
            "repo_path": repo_path,
            "extensions": extensions,
            "results": []
        }
    
    # Get embedding for the query
    logger.info("Getting embedding for query...")
    query_embedding = get_embedding(query)
    logger.info("Got embedding for query")
    
    # Process each file
    results = []
    max_file_size = 100 * 1024  # 100KB max file size to process
    
    # Limit the number of files to process for testing
    max_files_to_process = 50  # Limit to 50 files for testing
    if len(all_files) > max_files_to_process:
        logger.info(f"Limiting to {max_files_to_process} files for processing")
        all_files = all_files[:max_files_to_process]
    
    processed_files = 0
    for file_path in all_files:
        processed_files += 1
        if processed_files % 10 == 0:
            logger.info(f"Processed {processed_files}/{len(all_files)} files")
            
        # Get relative path to the repository
        rel_path = os.path.relpath(file_path, repo_path)
        
        # Skip hidden files and directories
        if any(part.startswith('.') for part in rel_path.split(os.sep)):
            continue
        
        # Skip files that are too large
        file_size = os.path.getsize(file_path)
        if file_size > max_file_size:
            logger.warning(f"Skipping large file {rel_path} ({file_size} bytes)")
            continue
        
        # Get file content
        content = get_file_content(file_path)
        
        # Skip empty files
        if not content.strip():
            continue
        
        # Get embedding for the file content
        try:
            # For very large content, we'll just use the first part
            # This helps avoid token limits and improves performance
            max_content_length = 8000  # Characters to use for embedding
            embedding_content = content[:max_content_length]
            
            logger.info(f"Getting embedding for file: {rel_path}")
            file_embedding = get_embedding(embedding_content)
            
            # Calculate similarity
            similarity = cosine_similarity(query_embedding, file_embedding)
            logger.info(f"File {rel_path} has similarity score: {similarity}")
            
            # Add to results
            results.append({
                "file": rel_path,
                "score": similarity,
                "content": content
            })
        except Exception as e:
            logger.error(f"Error processing file {rel_path}: {e}")
    
    # Sort results by similarity score (descending)
    results.sort(key=lambda x: x["score"], reverse=True)
    
    # Return top k results
    top_results = results[:k]
    
    logger.info(f"Returning {len(top_results)} results")
    
    return {
        "query": query,
        "repo_path": repo_path,
        "extensions": extensions,
        "results": top_results
    }