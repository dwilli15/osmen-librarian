import os
from langsmith import traceable as ls_traceable
from functools import wraps

def configure_tracing():
    """Configures LangSmith tracing from environment variables."""
    # In a real app, we might load .env here
    api_key = os.getenv("LANGCHAIN_API_KEY")
    if not api_key:
        print("Warning: LANGCHAIN_API_KEY not set. Tracing may not work.")
    
    project = os.getenv("LANGCHAIN_PROJECT", "librarian-agent")
    os.environ["LANGCHAIN_PROJECT"] = project
    print(f"Tracing configured for project: {project}")

def traceable(run_type="chain", name=None):
    """
    Wrapper around langsmith.traceable to allow for central configuration 
    and potential future swappability (e.g. to Langfuse).
    """
    def decorator(func):
        # If name is not provided, use function name
        run_name = name or func.__name__
        return ls_traceable(func, run_type=run_type, name=run_name)
    return decorator
