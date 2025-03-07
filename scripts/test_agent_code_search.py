#!/usr/bin/env python3
"""
Test script for evaluating how agents use the code search tool.

This script sets up scenarios where an agent needs to find and understand code,
and evaluates whether it effectively uses the code search tool.
"""

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from openhands_aci.code_search import initialize_code_search


# Sample tasks that require code search
TASKS = [
    {
        "name": "find_file_editor",
        "description": "Find the code that handles file editing in the repository.",
        "expected_query": "file editor",
        "expected_files": ["editor/__init__.py", "editor/editor.py"],
    },
    {
        "name": "find_linting_code",
        "description": "Find how code linting is implemented in the repository.",
        "expected_query": "linting code",
        "expected_files": ["linter/base.py", "linter/linter.py"],
    },
    {
        "name": "find_error_handling",
        "description": "Find how error handling is implemented in the tools.",
        "expected_query": "error handling",
        "expected_files": ["editor/exceptions.py"],
    },
]


def setup_code_search(repo_path, save_dir):
    """Initialize code search for the repository."""
    print(f"Initializing code search for {repo_path}...")
    result = initialize_code_search(
        repo_path=repo_path,
        save_dir=save_dir,
        extensions=[".py"],
    )
    
    if result["status"] == "success":
        print(f"Successfully indexed {result['num_documents']} files.")
        return True
    else:
        print(f"Error initializing code search: {result['message']}")
        return False


def create_agent_prompt(task, save_dir, with_tool_instructions=True):
    """Create a prompt for the agent with or without tool instructions."""
    base_prompt = f"""
You are a helpful coding assistant working on the OpenHands ACI repository.

Your task is: {task['description']}

You need to find the relevant code to complete this task.
"""

    if with_tool_instructions:
        tool_instructions = f"""
When you need to find specific code but don't know where it's located, use the code_search_tool.
For example:

code_search_tool(
    command="search",
    save_dir="{save_dir}",
    query="description of what you're looking for",
    k=5
)

This will help you locate the right files and understand how the code works.
"""
        return base_prompt + tool_instructions
    else:
        return base_prompt


def evaluate_agent_response(response, task):
    """Evaluate if the agent's response effectively used code search and found the right files."""
    # This is a placeholder for actual agent evaluation logic
    # In a real implementation, you would:
    # 1. Check if the agent used code_search_tool
    # 2. Analyze the query used
    # 3. Check if the agent found the expected files
    # 4. Evaluate the agent's understanding of the code
    
    # For now, we'll just print what we'd be checking
    print(f"\nEvaluating agent response for task: {task['name']}")
    print(f"Expected the agent to search for: {task['expected_query']}")
    print(f"Expected the agent to find files: {', '.join(task['expected_files'])}")
    
    # In a real implementation, return metrics like:
    return {
        "used_code_search": True,  # Did the agent use the tool?
        "query_quality": 0.8,  # How good was the query? (0-1)
        "found_expected_files": True,  # Did it find the expected files?
        "understanding_score": 0.7,  # How well did it understand the code? (0-1)
        "task_completion": 0.9,  # Did it complete the task? (0-1)
    }


def main():
    parser = argparse.ArgumentParser(description="Test agent's use of code search tool")
    parser.add_argument("repo_path", help="Path to the repository to search")
    parser.add_argument("--save-dir", default=None, help="Directory to save the search index")
    parser.add_argument("--task", choices=[t["name"] for t in TASKS], help="Specific task to run")
    
    args = parser.parse_args()
    
    # Use a temporary directory for the index if not specified
    if args.save_dir is None:
        temp_dir = tempfile.mkdtemp()
        save_dir = temp_dir
    else:
        save_dir = args.save_dir
        os.makedirs(save_dir, exist_ok=True)
    
    # Initialize code search
    if not setup_code_search(args.repo_path, save_dir):
        return 1
    
    # Run tasks
    tasks_to_run = [t for t in TASKS if args.task is None or t["name"] == args.task]
    
    for task in tasks_to_run:
        print(f"\n{'='*50}")
        print(f"Running task: {task['name']}")
        print(f"{'='*50}")
        
        # Create prompts for both conditions
        with_tool_prompt = create_agent_prompt(task, save_dir, True)
        without_tool_prompt = create_agent_prompt(task, save_dir, False)
        
        print("\nPrompt WITH tool instructions:")
        print(f"{with_tool_prompt}\n")
        
        print("\nPrompt WITHOUT tool instructions:")
        print(f"{without_tool_prompt}\n")
        
        # In a real implementation, you would:
        # 1. Send these prompts to the agent
        # 2. Record the agent's responses
        # 3. Evaluate the responses
        
        # For now, we'll just simulate an evaluation
        print("\nThis is where you would run the agent with these prompts.")
        print("After getting the agent's responses, you would evaluate them.")
        
        # Simulate evaluation
        metrics = evaluate_agent_response("Simulated agent response", task)
        print(f"\nEvaluation metrics: {json.dumps(metrics, indent=2)}")
    
    # Clean up if using a temporary directory
    if args.save_dir is None:
        print(f"\nCleaning up temporary directory: {temp_dir}")
        # In a real implementation: shutil.rmtree(temp_dir)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())