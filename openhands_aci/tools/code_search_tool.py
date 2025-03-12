"""Code search tool for OpenHands ACI.

This module provides a tool for semantic code search in a repository.
"""

import os
import glob
import json
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import logging

# Configure logging
# logging.basicConfig(level=logging.INFO, 
#                     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to import required libraries
try:
    import faiss
    import numpy as np
    import torch
    from sentence_transformers import SentenceTransformer
    from git import Repo
    from git.exc import InvalidGitRepositoryError
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Required dependency not available: {e}. Using mock mode.")
    DEPENDENCIES_AVAILABLE = False

class CodeSearchIndex:
    def __init__(self, embedding_model: Optional[str] = None):
        """Initialize the code search index.

        Args:
            embedding_model: Name or path of the sentence transformer model to use.
                           If None, will use the model specified in EMBEDDING_MODEL env var.
        """
        if not DEPENDENCIES_AVAILABLE:
            logger.warning("Dependencies not available. CodeSearchIndex will operate in mock mode.")
            return
            
        self.embedding_model = embedding_model or os.getenv(
            'EMBEDDING_MODEL', 'BAAI/bge-base-en-v1.5'
        )
        self.model = SentenceTransformer(self.embedding_model)
        self.index: Optional[faiss.IndexFlatIP] = None
        self.documents: List[Dict[str, Any]] = []
        self.doc_ids: List[str] = []

    def _embed_text(self, text: str) -> np.ndarray:
        """Embed a single text string."""
        if not DEPENDENCIES_AVAILABLE:
            # Return mock embedding if dependencies aren't available
            return np.zeros(768)  # Mock embedding
            
        with torch.no_grad():
            embedding = self.model.encode(text, convert_to_tensor=True)
            return embedding.cpu().numpy()

    def _embed_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Embed a batch of text strings."""
        if not DEPENDENCIES_AVAILABLE:
            # Return mock embeddings if dependencies aren't available
            return np.zeros((len(texts), 768))  # Mock embeddings
            
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            with torch.no_grad():
                batch_embeddings = self.model.encode(batch, convert_to_tensor=True)
                embeddings.append(batch_embeddings.cpu().numpy())
        return np.vstack(embeddings)

    def add_documents(self, documents: List[Dict[str, Any]], batch_size: int = 32):
        """Add documents to the index.

        Args:
            documents: List of document dictionaries with 'id' and 'content' keys
            batch_size: Batch size for embedding generation
        """
        if not DEPENDENCIES_AVAILABLE:
            self.documents.extend(documents)
            self.doc_ids.extend([doc['id'] for doc in documents])
            return
            
        texts = [doc['content'] for doc in documents]
        embeddings = self._embed_batch(texts, batch_size)

        if self.index is None:
            self.index = faiss.IndexFlatIP(embeddings.shape[1])

        self.index.add(embeddings)
        self.documents.extend(documents)
        self.doc_ids.extend([doc['id'] for doc in documents])

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search the index with a query string.

        Args:
            query: The search query
            k: Number of results to return

        Returns:
            List of document dictionaries with scores
        """
        if not DEPENDENCIES_AVAILABLE or not self.documents:
            # Return mock results or empty list if no documents
            return []
            
        if self.index is None:
            raise ValueError('Index is not initialized. Add documents first.')
            
        query_embedding = self._embed_text(query)
        scores, indices = self.index.search(query_embedding.reshape(1, -1), k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.documents):
                continue
            doc = self.documents[idx].copy()
            doc['score'] = float(score)
            results.append(doc)

        return results

    def save(self, directory: str):
        """Save the index and documents to disk.

        Args:
            directory: Directory to save the index in
        """
        if not DEPENDENCIES_AVAILABLE:
            logger.warning("Dependencies not available. Cannot save index.")
            return
            
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)

        # Save the Faiss index
        if self.index is not None:
            faiss.write_index(self.index, str(dir_path / 'index.faiss'))

        # Save documents and metadata
        with open(dir_path / 'documents.pkl', 'wb') as f:
            pickle.dump(
                {
                    'documents': self.documents,
                    'doc_ids': self.doc_ids,
                    'embedding_model': self.embedding_model,
                },
                f,
            )

    @classmethod
    def load(cls, directory: str) -> 'CodeSearchIndex':
        """Load an index from disk.

        Args:
            directory: Directory containing the saved index

        Returns:
            Loaded CodeSearchIndex instance
        """
        if not DEPENDENCIES_AVAILABLE:
            logger.warning("Dependencies not available. Returning empty index instance.")
            return cls()
            
        dir_path = Path(directory)

        # Load metadata
        with open(dir_path / 'documents.pkl', 'rb') as f:
            data = pickle.load(f)

        # Create instance with same model
        instance = cls(embedding_model=data['embedding_model'])
        instance.documents = data['documents']
        instance.doc_ids = data['doc_ids']

        # Load Faiss index
        instance.index = faiss.read_index(str(dir_path / 'index.faiss'))

        return instance

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

def _get_files_from_repo(
    repo_path: str, extensions: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Get all files from a git repository.

    Args:
        repo_path: Path to the git repository
        extensions: List of file extensions to include (e.g. ['.py', '.js'])
                  If None, includes all files

    Returns:
        List of document dictionaries with 'id' and 'content' keys
    """
    if DEPENDENCIES_AVAILABLE:
        try:
            # Verify it's a git repo
            _ = Repo(repo_path)
        except InvalidGitRepositoryError:
            logger.warning(f'{repo_path} is not a valid git repository, proceeding without git validation')
    
    documents = []
    repo_path_obj = Path(repo_path)

    for root, _, files in os.walk(repo_path_obj):
        if '.git' in root:
            continue

        for file in files:
            if extensions and not any(file.endswith(ext) for ext in extensions):
                continue

            file_path = Path(root) / file
            try:
                content = get_file_content(str(file_path))
                if not content.strip():
                    continue
            except Exception:
                continue

            rel_path = str(file_path.relative_to(repo_path_obj))
            documents.append(
                {'id': rel_path, 'content': content, 'path': rel_path}
            )

    return documents

def initialize_code_search(
    repo_path: str,
    save_dir: str,
    extensions: Optional[List[str]] = None,
    embedding_model: Optional[str] = None,
    batch_size: int = 32,
) -> Dict[str, Any]:
    """Initialize code search for a repository.

    Args:
        repo_path: Path to the git repository
        save_dir: Directory to save the search index
        extensions: List of file extensions to include
        embedding_model: Name or path of the embedding model to use
        batch_size: Batch size for embedding generation

    Returns:
        Dictionary with status and message
    """
    try:
        # Get all files from repo
        documents = _get_files_from_repo(repo_path, extensions)
        if not documents:
            return {
                'status': 'error',
                'message': f'No files found in repository {repo_path}',
            }

        # Create and save index
        index = CodeSearchIndex(embedding_model=embedding_model)
        index.add_documents(documents, batch_size=batch_size)
        index.save(save_dir)

        return {
            'status': 'success',
            'message': f'Successfully indexed {len(documents)} files from {repo_path}',
            'num_documents': len(documents),
        }

    except Exception as e:
        logger.error(f"Error initializing code search: {e}")
        return {
            'status': 'error',
            'message': f'Error initializing code search: {str(e)}',
        }

def search_code(save_dir: str, query: str, k: int = 5) -> Dict[str, Any]:
    """Search code in an indexed repository.

    Args:
        save_dir: Directory containing the search index
        query: Search query
        k: Number of results to return

    Returns:
        Dictionary with status and search results
    """
    try:
        # Load index
        index = CodeSearchIndex.load(save_dir)

        # Search
        results = index.search(query, k=k)

        return {'status': 'success', 'results': results}

    except Exception as e:
        logger.error(f"Error searching code: {e}")
        return {'status': 'error', 'message': f'Error searching code: {str(e)}'}

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
        mock_mode: If True, returns mock results without actually searching
        
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
    
    # Create a temporary directory for the index
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize code search (this will create and save the index)
        init_result = initialize_code_search(
            repo_path=repo_path,
            save_dir=temp_dir,
            extensions=extensions,
            batch_size=32
        )
        
        if init_result['status'] == 'error':
            return {
                "query": query,
                "repo_path": repo_path,
                "extensions": extensions,
                "error": init_result['message']
            }
        
        # Search the code
        search_result = search_code(
            save_dir=temp_dir,
            query=query,
            k=k
        )
        
        if search_result['status'] == 'error':
            return {
                "query": query,
                "repo_path": repo_path,
                "extensions": extensions,
                "error": search_result['message']
            }
        
        # Transform results to match the expected output format
        formatted_results = []
        for result in search_result['results']:
            formatted_results.append({
                "file": result['path'],
                "score": result['score'],
                "content": result['content']
            })
        
        return {
            "query": query,
            "repo_path": repo_path,
            "extensions": extensions,
            "results": formatted_results
        }