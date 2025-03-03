import tempfile
from pathlib import Path

import pytest
from git import Repo

from openhands_aci.tools.code_search_tool import code_search_tool


@pytest.fixture
def test_repo():
    """Create a temporary git repository with some test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize git repo
        repo = Repo.init(temp_dir)

        # Create test files
        files = {
            'main.py': 'def hello():\n    print("Hello, World!")',
            'utils/helper.py': 'def add(a, b):\n    return a + b',
            'README.md': '# Test Repository\nThis is a test.',
        }

        for path, content in files.items():
            file_path = Path(temp_dir) / path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(content)

        # Add and commit files
        repo.index.add('*')
        repo.index.commit('Initial commit')

        yield temp_dir


def test_code_search_tool(test_repo):
    """Test the code_search_tool function."""
    with tempfile.TemporaryDirectory() as save_dir:
        # First search without indexing should fail
        result = code_search_tool(query='function that adds numbers', save_dir=save_dir)
        assert result['status'] == 'error'
        assert 'No index found' in result['message']

        # Initialize search
        result = code_search_tool(
            query='function that adds numbers',
            repo_path=test_repo,
            save_dir=save_dir,
            extensions=['.py'],
        )

        assert result['status'] == 'success'
        assert len(result['results']) > 0

        # The add function should be in the results
        found_add = False
        for doc in result['results']:
            if 'add' in doc['content']:
                found_add = True
                break
        assert found_add

        # Search again without repo_path (should use existing index)
        result = code_search_tool(query='print hello world', save_dir=save_dir)

        assert result['status'] == 'success'
        assert len(result['results']) > 0

        # The hello function should be in the results
        found_hello = False
        for doc in result['results']:
            if 'hello' in doc['content'].lower():
                found_hello = True
                break
        assert found_hello
