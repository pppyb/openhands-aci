"""
Example demonstrating the enhanced workflow with RAG integration.

This example shows how to use the integrated workflow with RAG capabilities
to perform common development tasks.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import openhands_aci
sys.path.append(str(Path(__file__).parent.parent))

from openhands_aci.editor import edit_with_context, create_with_context
from openhands_aci.linter import lint_with_context, suggest_fixes
from openhands_aci.workflow import execute_task, format_result
from openhands_aci.events import subscribe, trigger
from openhands_aci.visualization import format_search_results


# Event handler for search results
def handle_search_results(event_name, query, results, **kwargs):
    """Handle search results event."""
    print(f"\n{'='*80}")
    print(f"Search results for query: {query}")
    print(f"{'='*80}")
    print(format_search_results(results, format_type="text"))


# Event handler for file editing
def handle_file_edited(event_name, file_path, task, context, result, **kwargs):
    """Handle file edited event."""
    print(f"\n{'='*80}")
    print(f"File edited: {file_path}")
    print(f"Task: {task}")
    print(f"{'='*80}")
    print(f"Status: {result.get('status', 'unknown')}")
    if context:
        print(f"\nContext used:\n{context[:200]}...")


# Register event handlers
subscribe("search_results", handle_search_results)
subscribe("file_edited", handle_file_edited)


def example_edit_with_context():
    """Example of editing a file with RAG context."""
    print("\n\nEXAMPLE: EDIT WITH CONTEXT")
    print("="*80)
    
    # Create a temporary file
    temp_file = Path(__file__).parent / "temp_example.py"
    with open(temp_file, "w") as f:
        f.write("# This is a temporary file for the example\n\n")
    
    # Edit the file with RAG context
    edit_result = edit_with_context(
        file_path=str(temp_file),
        task="Implement a function to calculate the Fibonacci sequence",
    )
    
    # Print the result
    print(f"Edit result: {edit_result.get('status', 'unknown')}")
    
    # Print the file content
    print("\nFile content:")
    with open(temp_file, "r") as f:
        print(f.read())
    
    # Clean up
    os.remove(temp_file)


def example_lint_with_context():
    """Example of linting a file with RAG context."""
    print("\n\nEXAMPLE: LINT WITH CONTEXT")
    print("="*80)
    
    # Create a temporary file with some linting issues
    temp_file = Path(__file__).parent / "temp_lint_example.py"
    with open(temp_file, "w") as f:
        f.write("""# This file has some linting issues
def bad_function( ):
    x=1
    y= 2
    return x+y
""")
    
    # Lint the file with RAG context
    lint_result = lint_with_context(
        file_path=str(temp_file),
        fix=True,
    )
    
    # Print the result
    print(f"Lint result: {lint_result.get('status', 'unknown')}")
    print(f"Issues found: {lint_result.get('count', 0)}")
    
    # Print the issues
    if lint_result.get("issues"):
        print("\nIssues:")
        for issue in lint_result["issues"]:
            print(f"  Line {issue['line']}: {issue['message']} ({issue['code']})")
            if "fix_suggestions" in issue:
                print("  Fix suggestions:")
                for suggestion in issue["fix_suggestions"]:
                    print(f"    From {suggestion['source']} (relevance: {suggestion['relevance']:.2f})")
    
    # Clean up
    os.remove(temp_file)


def example_integrated_workflow():
    """Example of using the integrated workflow."""
    print("\n\nEXAMPLE: INTEGRATED WORKFLOW")
    print("="*80)
    
    # Create a temporary directory for the example
    temp_dir = Path(__file__).parent / "temp_workflow"
    temp_dir.mkdir(exist_ok=True)
    
    # Create a temporary file
    temp_file = temp_dir / "example_module.py"
    with open(temp_file, "w") as f:
        f.write("# This is a temporary file for the workflow example\n\n")
    
    # Execute a task
    task_result = execute_task(
        task="Implement a utility function to convert temperature between Celsius and Fahrenheit",
        file_paths=[str(temp_file)],
        run_tests=False,
    )
    
    # Print the formatted result
    print(format_result(task_result, format_type="text"))
    
    # Print the file content
    print("\nFile content:")
    with open(temp_file, "r") as f:
        print(f.read())
    
    # Clean up
    import shutil
    shutil.rmtree(temp_dir)


def main():
    """Run the examples."""
    # Example of editing a file with RAG context
    example_edit_with_context()
    
    # Example of linting a file with RAG context
    example_lint_with_context()
    
    # Example of using the integrated workflow
    example_integrated_workflow()


if __name__ == "__main__":
    main()