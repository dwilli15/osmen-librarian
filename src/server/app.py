from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import asyncio

try:
    from assistants.schema import AssistantConfig
    from graph import app as agent_app
except ImportError:
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from assistants.schema import AssistantConfig
    from graph import app as agent_app

app = FastAPI(title="Librarian Agent API")

# In-memory storage for demo
assistants: Dict[str, AssistantConfig] = {}
threads: Dict[str, List[Dict[str, Any]]] = {}

class ThreadCreate(BaseModel):
    thread_id: str

class RunCreate(BaseModel):
    assistant_id: str
    message: str

@app.post("/assistants", response_model=AssistantConfig)
async def create_assistant(config: AssistantConfig):
    if config.id in assistants:
        raise HTTPException(status_code=400, detail="Assistant ID already exists")
    assistants[config.id] = config
    return config

@app.get("/assistants", response_model=List[AssistantConfig])
async def list_assistants():
    return list(assistants.values())

@app.post("/threads")
async def create_thread(thread: ThreadCreate):
    if thread.thread_id in threads:
        raise HTTPException(status_code=400, detail="Thread ID already exists")
    threads[thread.thread_id] = []
    return {"status": "created", "thread_id": thread.thread_id}

@app.post("/threads/{thread_id}/runs")
async def create_run(thread_id: str, run: RunCreate):
    if thread_id not in threads:
        raise HTTPException(status_code=404, detail="Thread not found")
    if run.assistant_id not in assistants:
        raise HTTPException(status_code=404, detail="Assistant not found")
    
    # Execute Agent
    inputs = {"messages": [("user", run.message)]}
    config = {"configurable": {"thread_id": thread_id}}
    
    # In a real app, this would be backgrounded or streamed
    # For now, we wait for the result
    final_state = agent_app.invoke(inputs, config=config)
    
    # Extract answer
    answer = final_state.get("answer", "No answer generated.")
    
    # Update thread history (mock)
    threads[thread_id].append({"role": "user", "content": run.message})
    threads[thread_id].append({"role": "assistant", "content": answer})
    
    return {"run_id": "run-1", "status": "completed", "answer": answer}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
