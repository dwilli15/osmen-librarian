"""
Librarian Agent Application.

Main application entry point that provides:
- FastAPI REST endpoints
- WebSocket support for streaming
- Integration with LangGraph agent
- OpenAI Assistants API compatibility

Usage:
    uvicorn app:app --reload
    python -m app
"""

from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager
import logging
import os

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("librarian.app")

# Lazy imports for optional dependencies
try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    logger.warning("FastAPI not installed. REST API unavailable.")


# --------------------------------------------------------------------------
# Pydantic Models
# --------------------------------------------------------------------------

if FASTAPI_AVAILABLE:
    class QueryRequest(BaseModel):
        """Request model for queries."""
        query: str
        mode: str = "foundation"
        k: int = 5
    
    class QueryResponse(BaseModel):
        """Response model for queries."""
        query: str
        answer: Optional[str] = None
        sources: List[Dict[str, Any]] = []
        mode: str = "foundation"
    
    class AssistantCreate(BaseModel):
        """Request to create an assistant."""
        name: str
        instructions: str = ""
        search_mode: str = "foundation"
        enable_lateral: bool = False
    
    class ThreadCreate(BaseModel):
        """Request to create a thread."""
        assistant_id: Optional[str] = None
    
    class MessageCreate(BaseModel):
        """Request to add a message."""
        content: str
        role: str = "user"
    
    class RunCreate(BaseModel):
        """Request to create a run."""
        assistant_id: Optional[str] = None
        query: Optional[str] = None
    
    class IngestRequest(BaseModel):
        """Request to ingest documents."""
        path: str = "./data"
        force: bool = False


# --------------------------------------------------------------------------
# Application Setup
# --------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app):
    """Application lifespan handler."""
    logger.info("Starting Librarian application...")
    
    # Initialize on startup
    try:
        from retrieval import get_retriever
        retriever = get_retriever()
        logger.info(f"Retriever initialized: {retriever.count()} documents")
    except Exception as e:
        logger.warning(f"Retriever init failed: {e}")
    
    # Setup tracing
    try:
        from tracing import setup_tracing
        setup_tracing()
        logger.info("Tracing initialized")
    except Exception as e:
        logger.warning(f"Tracing init failed: {e}")
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down Librarian application...")


if FASTAPI_AVAILABLE:
    app = FastAPI(
        title="Librarian Agent",
        description="Research assistant with RAG and lateral thinking",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app = None


# --------------------------------------------------------------------------
# Health Endpoints
# --------------------------------------------------------------------------

if FASTAPI_AVAILABLE:
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "librarian"}
    
    @app.get("/status")
    async def status():
        """Detailed status endpoint."""
        status_info = {"status": "healthy"}
        
        # Check retriever
        try:
            from retrieval import get_retriever
            retriever = get_retriever()
            health = retriever.health_check()
            status_info["retriever"] = health
        except Exception as e:
            status_info["retriever"] = {"status": "error", "error": str(e)}
        
        # Check assistants
        try:
            from assistants import get_assistant_store, get_thread_store
            status_info["assistants"] = len(get_assistant_store().list())
            status_info["threads"] = len(get_thread_store().list())
        except Exception as e:
            status_info["assistants_error"] = str(e)
        
        return status_info


# --------------------------------------------------------------------------
# Query Endpoints
# --------------------------------------------------------------------------

if FASTAPI_AVAILABLE:
    @app.post("/query", response_model=QueryResponse)
    async def query(request: QueryRequest):
        """
        Query the knowledge base.
        
        Modes:
        - foundation: Basic concept search
        - lateral: Creative cross-domain connections
        - factcheck: Evidence-based verification
        """
        try:
            from rag_manager import query_knowledge_base
            
            results = query_knowledge_base(
                request.query,
                mode=request.mode
            )
            
            return QueryResponse(
                query=request.query,
                answer=results.get("answer"),
                sources=results.get("context", [])[:request.k],
                mode=request.mode
            )
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/ingest")
    async def ingest(
        request: IngestRequest,
        background_tasks: BackgroundTasks
    ):
        """
        Ingest documents into the knowledge base.
        
        Runs in background for large datasets.
        """
        def run_ingest():
            from rag_manager import ingest_data
            ingest_data(data_directory=request.path, force=request.force)
        
        background_tasks.add_task(run_ingest)
        return {"status": "ingestion_started", "path": request.path}


# --------------------------------------------------------------------------
# Assistant Endpoints (OpenAI Assistants API compatible)
# --------------------------------------------------------------------------

if FASTAPI_AVAILABLE:
    @app.get("/assistants")
    async def list_assistants():
        """List all assistants."""
        try:
            from assistants import get_assistant_store
            store = get_assistant_store()
            return [a.to_dict() for a in store.list()]
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/assistants")
    async def create_assistant(request: AssistantCreate):
        """Create a new assistant."""
        try:
            from assistants import (
                get_assistant_store, Assistant, AssistantConfig
            )
            
            config = AssistantConfig(
                search_mode=request.search_mode,
                enable_lateral_thinking=request.enable_lateral
            )
            
            assistant = Assistant(
                name=request.name,
                instructions=request.instructions,
                config=config
            )
            
            store = get_assistant_store()
            created = store.create(assistant)
            return created.to_dict()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/assistants/{assistant_id}")
    async def get_assistant(assistant_id: str):
        """Get assistant by ID."""
        try:
            from assistants import get_assistant_store
            store = get_assistant_store()
            assistant = store.get(assistant_id)
            if not assistant:
                raise HTTPException(status_code=404, detail="Assistant not found")
            return assistant.to_dict()
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.delete("/assistants/{assistant_id}")
    async def delete_assistant(assistant_id: str):
        """Delete an assistant."""
        try:
            from assistants import get_assistant_store
            store = get_assistant_store()
            if store.delete(assistant_id):
                return {"status": "deleted"}
            raise HTTPException(status_code=404, detail="Assistant not found")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


# --------------------------------------------------------------------------
# Thread Endpoints
# --------------------------------------------------------------------------

if FASTAPI_AVAILABLE:
    @app.post("/threads")
    async def create_thread(request: ThreadCreate):
        """Create a new thread."""
        try:
            from assistants import get_thread_store, Thread
            
            thread = Thread(assistant_id=request.assistant_id)
            store = get_thread_store()
            created = store.create(thread)
            return created.to_dict()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/threads/{thread_id}")
    async def get_thread(thread_id: str):
        """Get thread with messages."""
        try:
            from assistants import get_thread_store
            store = get_thread_store()
            thread = store.get(thread_id)
            if not thread:
                raise HTTPException(status_code=404, detail="Thread not found")
            return thread.to_dict()
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/threads/{thread_id}/messages")
    async def add_message(thread_id: str, request: MessageCreate):
        """Add a message to a thread."""
        try:
            from assistants import get_thread_store, MessageRole
            
            store = get_thread_store()
            role = MessageRole(request.role)
            msg = store.add_message(thread_id, role, request.content)
            
            if not msg:
                raise HTTPException(status_code=404, detail="Thread not found")
            return msg.to_dict()
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/threads/{thread_id}/messages")
    async def get_messages(thread_id: str):
        """Get all messages in a thread."""
        try:
            from assistants import get_thread_store
            store = get_thread_store()
            messages = store.get_messages(thread_id)
            return [m.to_dict() for m in messages]
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


# --------------------------------------------------------------------------
# Run Endpoints
# --------------------------------------------------------------------------

if FASTAPI_AVAILABLE:
    @app.post("/threads/{thread_id}/runs")
    async def create_run(thread_id: str, request: RunCreate):
        """
        Create and execute a run on a thread.
        
        This will:
        1. Get the thread and assistant
        2. Optionally add a new message
        3. Execute the query
        4. Store and return results
        """
        try:
            from assistants import (
                get_thread_store, get_assistant_store,
                Run, MessageRole
            )
            from assistants.storage import get_run_store
            from rag_manager import query_knowledge_base
            
            thread_store = get_thread_store()
            asst_store = get_assistant_store()
            run_store = get_run_store()
            
            # Get thread
            thread = thread_store.get(thread_id)
            if not thread:
                raise HTTPException(status_code=404, detail="Thread not found")
            
            # Resolve assistant
            aid = request.assistant_id or thread.assistant_id
            if aid:
                assistant = asst_store.get(aid)
            else:
                assistant = asst_store.get_or_create_default()
                aid = assistant.id
            
            # Add query if provided
            if request.query:
                thread_store.add_message(thread_id, MessageRole.USER, request.query)
                thread = thread_store.get(thread_id)
            
            # Create run
            run = Run(thread_id=thread_id, assistant_id=aid)
            run.start()
            run_store.create(run)
            
            try:
                # Get last user message
                user_msgs = [m for m in thread.messages if m.role == MessageRole.USER]
                if not user_msgs:
                    raise HTTPException(
                        status_code=400,
                        detail="No user message in thread"
                    )
                
                last_query = user_msgs[-1].content
                mode = assistant.config.search_mode if assistant else "foundation"
                
                # Execute query
                results = query_knowledge_base(last_query, mode=mode)
                output = results.get("answer", str(results))
                
                # Complete run
                run.complete(output)
                run_store.update(run)
                
                # Add response to thread
                thread_store.add_message(thread_id, MessageRole.ASSISTANT, output)
                
                return run.to_dict()
                
            except HTTPException:
                raise
            except Exception as e:
                run.fail(str(e))
                run_store.update(run)
                raise HTTPException(status_code=500, detail=str(e))
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/threads/{thread_id}/runs")
    async def list_runs(thread_id: str):
        """List runs for a thread."""
        try:
            from assistants.storage import get_run_store
            store = get_run_store()
            runs = store.list_by_thread(thread_id)
            return [r.to_dict() for r in runs]
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/threads/{thread_id}/runs/{run_id}")
    async def get_run(thread_id: str, run_id: str):
        """Get a specific run."""
        try:
            from assistants.storage import get_run_store
            store = get_run_store()
            run = store.get(run_id)
            if not run or run.thread_id != thread_id:
                raise HTTPException(status_code=404, detail="Run not found")
            return run.to_dict()
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


# --------------------------------------------------------------------------
# Graph Endpoints
# --------------------------------------------------------------------------

if FASTAPI_AVAILABLE:
    @app.post("/graph/invoke")
    async def invoke_graph(
        query: str,
        mode: str = "foundation",
        thread_id: Optional[str] = None,
        memory_type: str = "memory"
    ):
        """
        Invoke the LangGraph agent directly.
        
        Args:
            query: The query text
            mode: Search mode (foundation/lateral/factcheck)
            thread_id: Thread ID for persistence
            memory_type: Checkpointer type (memory/sqlite/postgres)
        """
        try:
            from graph import compile_graph
            from langchain_core.messages import HumanMessage
            
            graph = compile_graph(checkpointer_type=memory_type)
            
            config = {
                "configurable": {
                    "thread_id": thread_id or "api-thread"
                }
            }
            
            initial_state = {
                "messages": [HumanMessage(content=query)],
                "query": query,
                "mode": mode
            }
            
            result = graph.invoke(initial_state, config)
            
            return {
                "query": result.get("query"),
                "answer": result.get("answer"),
                "mode": result.get("mode"),
                "documents": result.get("documents", [])[:5]
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    """Run the application."""
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"Starting Librarian on {host}:{port}")
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=os.getenv("RELOAD", "false").lower() == "true"
    )


if __name__ == "__main__":
    main()
