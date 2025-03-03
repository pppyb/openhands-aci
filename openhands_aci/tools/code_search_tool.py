import os
from typing import Any, Dict, List, Optional

from openhands_aci.code_search import initialize_code_search, search_code


def code_search_tool(
    query: str,
    repo_path: Optional[str] = None,
    save_dir: Optional[str] = None,
    extensions: Optional[List[str]] = None,
    k: int = 5,
) -> Dict[str, Any]:
    """Search code in a repository using semantic search.

    This tool uses Retrieval Augmented Generation (RAG) to find relevant code
    based on natural language queries. It first indexes the repository (if needed)
    and then performs a semantic search.

    Args:
        query: The search query in natural language
        repo_path: Path to the git repository to search (optional if save_dir exists)
        save_dir: Directory to save/load the search index (defaults to .code_search_index)
        extensions: List of file extensions to include (e.g. [".py", ".js"])
        k: Number of results to return

    Returns:
        Dictionary with status and search results
    """
    # Set default save_dir if not provided
    if save_dir is None:
        save_dir = os.path.join(os.getcwd(), '.code_search_index')

    # Check if index exists
    index_exists = os.path.exists(
        os.path.join(save_dir, 'index.faiss')
    ) and os.path.exists(os.path.join(save_dir, 'documents.pkl'))

    # Initialize index if it doesn't exist or repo_path is provided
    if not index_exists and repo_path is not None:
        init_result = initialize_code_search(
            repo_path=repo_path,
            save_dir=save_dir,
            extensions=extensions,
        )
        if init_result['status'] == 'error':
            return init_result

    # Return error if index doesn't exist and repo_path is not provided
    elif not index_exists:
        return {
            'status': 'error',
            'message': 'No index found. Please provide repo_path to create an index.',
        }

    # Perform search
    search_result = search_code(save_dir=save_dir, query=query, k=k)

    # Format results for better readability
    if search_result['status'] == 'success':
        formatted_results = []
        for result in search_result['results']:
            formatted_results.append(
                {
                    'file': result['path'],
                    'score': round(result['score'], 3),
                    'content': result['content'][:500] + '...'
                    if len(result['content']) > 500
                    else result['content'],
                }
            )
        search_result['results'] = formatted_results

    return search_result
