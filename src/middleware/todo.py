from typing import List, Dict, Any
from langchain_core.tools import Tool
from .base import BaseMiddleware

class TodoListMiddleware(BaseMiddleware):
    """Middleware for managing a todo list in the agent state."""

    def add_todo(self, task: str) -> str:
        """Adds a task to the todo list."""
        # In a real implementation, this would update the state via a reducer or direct access if possible
        # For now, we return a string that the agent can use to update its internal thought process
        return f"TODO ADDED: {task}"

    def list_todos(self) -> str:
        """Lists all current todos."""
        # Placeholder: In real graph, this would read from state['todos']
        return "Current Todos: [Placeholder]"

    def complete_todo(self, task_index: int) -> str:
        """Marks a todo as complete."""
        return f"TODO COMPLETED: {task_index}"

    def register_tools(self) -> List[Tool]:
        return [
            Tool(name="todo_add", func=self.add_todo, description="Add a task to the todo list"),
            Tool(name="todo_list", func=self.list_todos, description="List all current todos"),
            Tool(name="todo_complete", func=self.complete_todo, description="Mark a todo as complete by index")
        ]
