import os
from typing import List
from langchain_core.tools import Tool
from .base import BaseMiddleware

class FilesystemMiddleware(BaseMiddleware):
    """Middleware for safe filesystem operations."""
    
    def __init__(self, root_dir: str):
        self.root_dir = os.path.abspath(root_dir)

    def _validate_path(self, path: str) -> str:
        """Ensures path is within root_dir."""
        full_path = os.path.abspath(os.path.join(self.root_dir, path))
        if not full_path.startswith(self.root_dir):
            raise ValueError(f"Access denied: Path {path} is outside root {self.root_dir}")
        return full_path

    def list_files(self, path: str = ".") -> str:
        """Lists files in a directory."""
        try:
            target = self._validate_path(path)
            items = os.listdir(target)
            return "\n".join(items)
        except Exception as e:
            return f"Error listing files: {str(e)}"

    def read_file(self, path: str) -> str:
        """Reads content of a file."""
        try:
            target = self._validate_path(path)
            with open(target, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"

    def write_file(self, path: str, content: str) -> str:
        """Writes content to a file."""
        try:
            target = self._validate_path(path)
            with open(target, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully wrote to {path}"
        except Exception as e:
            return f"Error writing file: {str(e)}"

    def register_tools(self) -> List[Tool]:
        return [
            Tool(name="fs_ls", func=self.list_files, description="List files in a directory"),
            Tool(name="fs_read", func=self.read_file, description="Read file content"),
            Tool(name="fs_write", func=self.write_file, description="Write content to a file")
        ]
