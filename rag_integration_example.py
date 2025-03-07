import os
from openhands_aci.tools.code_search_tool import code_search_tool
from openhands_aci.editor import OHEditor

class CodeAssistant:
    """Example Code Assistant"""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.editor = OHEditor()
        self.index_dir = os.path.join(repo_path, ".code_search_index")
        self._ensure_index()

    def _ensure_index(self):
        """Ensure that the index exists"""
        index_exists = (
            os.path.exists(os.path.join(self.index_dir, "index.faiss"))
            and os.path.exists(os.path.join(self.index_dir, "documents.pkl"))
        )

        if not index_exists:
            print(f"Indexing repository: {self.repo_path}")
            code_search_tool(
                query="Initialize index",
                repo_path=self.repo_path,
                save_dir=self.index_dir,
                extensions=[".py", ".js", ".html"]
            )

    def search_code(self, query: str):
        """Search code"""
        print(f"Searching: '{query}'")
        result = code_search_tool(
            query=query,
            save_dir=self.index_dir,
            k=5,
            remove_duplicates=True,
            min_score=0.5
        )

        if result["status"] == "error":
            print(f"Search error: {result['message']}")
            return

        print(f"\nFound {len(result['results'])} result(s):")
        for i, res in enumerate(result["results"], 1):
            print(f"\nResult {i}: {res['file']} (Similarity: {res['score']:.3f})")
            print("-" * 80)
            print(res["content"])

    def search_and_edit(self, query: str):
        """Search and edit code"""
        # Search code
        result = code_search_tool(
            query=query,
            save_dir=self.index_dir,
            k=3,
            remove_duplicates=True
        )

        if result["status"] == "error" or not result["results"]:
            print("Search error or no results found")
            return

        # Display results
        for i, res in enumerate(result["results"], 1):
            print(f"\nResult {i}: {res['file']} (Similarity: {res['score']:.3f})")
            print("-" * 40)
            print(res["content"][:200] + "..." if len(res["content"]) > 200 else res["content"])

        # Select a file
        choice = input("\nPlease select a file to edit (1-3): ")
        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(result["results"]):
                print("Invalid selection")
                return
        except ValueError:
            print("Please enter a number")
            return

        # Get the file path
        file_path = os.path.join(self.repo_path, result["results"][idx]["file"])

        # View the full file
        print(f"\nViewing file: {file_path}")
        view_result = self.editor(
            command="view",
            path=file_path
        )
        print(view_result.output)

        # Get edit information
        print("\nPlease enter the section to edit:")
        old_str = input("Original code: ")
        new_str = input("New code: ")

        # Perform the edit
        edit_result = self.editor(
            command="str_replace",
            path=file_path,
            old_str=old_str,
            new_str=new_str
        )
        print("\nEdit result:")
        print(edit_result.output)

# Example usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python rag_integration_example.py <repo_path> [query]")
        sys.exit(1)

    repo_path = sys.argv[1]
    assistant = CodeAssistant(repo_path)

    if len(sys.argv) > 2:
        query = sys.argv[2]
        assistant.search_code(query)
    else:
        # Interactive mode
        while True:
            print("\nOptions:")
            print("1. Search code")
            print("2. Search and edit code")
            print("3. Exit")
            choice = input("Please select (1-3): ")

            if choice == "1":
                query = input("Enter search query: ")
                assistant.search_code(query)
            elif choice == "2":
                query = input("Enter search query: ")
                assistant.search_and_edit(query)
            elif choice == "3":
                break
            else:
                print("Invalid selection")
