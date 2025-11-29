from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_community.utilities import PythonREPL
from langchain_core.tools import Tool

# Initialize REPL
repl = PythonREPL()

class ExecutorState(TypedDict):
    task: str
    result: str

def execution_node(state: ExecutorState):
    """Executes a task using PythonREPL."""
    task = state['task']
    print(f"--- Executor: Running task '{task}' ---")
    
    # In a real agent, 'task' might be natural language that needs to be converted to code first.
    # For this subagent, let's assume 'task' IS the code or we use an LLM to generate it.
    # To be safe and "production ready", we should probably have an LLM step to generate code from the task description.
    # But for the "Executor" pattern, often it receives code. 
    # Let's assume the input IS code for now, or add a generation step.
    
    # If it's not code, we'd need an LLM. Let's assume it's code for this "Executor" primitive.
    # Or better, let's make it a "Code Interpreter" agent.
    
    try:
        # Simple heuristic: if it looks like python, run it.
        # Otherwise, just return it (or fail).
        result = repl.run(task)
        output = f"Executed Code:\n{task}\n\nResult:\n{result}"
    except Exception as e:
        output = f"Execution Failed: {e}"
    
    return {"result": output}

workflow = StateGraph(ExecutorState)
workflow.add_node("execute", execution_node)
workflow.set_entry_point("execute")
workflow.add_edge("execute", END)

executor_app = workflow.compile()
