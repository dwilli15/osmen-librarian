import sys
import os
import unittest
from langchain_core.tools import Tool

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from middleware.filesystem import FilesystemMiddleware
from middleware.todo import TodoListMiddleware
from middleware.subagent import SubAgentMiddleware
from middleware.hitl import HITLMiddleware

class TestMiddleware(unittest.TestCase):
    
    def test_filesystem(self):
        print("\nTesting FilesystemMiddleware...")
        # Use a safe temp dir
        root = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(root, exist_ok=True)
        fs = FilesystemMiddleware(root_dir=root)
        
        # Write
        fs.write_file("test.txt", "Hello Middleware")
        # Read
        content = fs.read_file("test.txt")
        self.assertEqual(content, "Hello Middleware")
        # List
        files = fs.list_files()
        self.assertIn("test.txt", files)
        print("Filesystem tests passed.")

    def test_todo(self):
        print("\nTesting TodoListMiddleware...")
        todo = TodoListMiddleware()
        res = todo.add_todo("Refactor graph")
        self.assertIn("TODO ADDED", res)
        print("Todo tests passed.")

    def test_subagent(self):
        print("\nTesting SubAgentMiddleware...")
        sa = SubAgentMiddleware()
        res = sa.spawn_subagent("fact_checker", "Verify this claim")
        self.assertIn("spawned", res)
        print("Subagent tests passed.")

    def test_hitl(self):
        print("\nTesting HITLMiddleware...")
        hitl = HITLMiddleware()
        from langgraph.errors import GraphInterrupt
        with self.assertRaises(GraphInterrupt):
            hitl.request_approval("Deploy to prod")
        print("HITL tests passed.")

if __name__ == "__main__":
    unittest.main()
