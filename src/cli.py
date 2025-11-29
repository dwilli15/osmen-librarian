"""
CLI for Librarian Agent.

Provides command-line interface for:
- Running queries against the knowledge base
- Ingesting documents
- Managing assistants and threads
- Interactive chat mode

Usage:
    python -m cli query "What is lateral thinking?"
    python -m cli ingest ./data
    python -m cli chat
    python -m cli serve
"""

import argparse
import sys
import json
import logging
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("librarian.cli")


def cmd_query(args):
    """Execute a query against the knowledge base."""
    from rag_manager import query_knowledge_base
    
    logger.info(f"Query: {args.query} (mode={args.mode})")
    
    try:
        results = query_knowledge_base(args.query, mode=args.mode)
        
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            # Pretty print
            print(f"\n{'='*60}")
            print(f"Query: {args.query}")
            print(f"Mode: {args.mode}")
            print(f"{'='*60}\n")
            
            if "answer" in results:
                print("Answer:")
                print(results["answer"])
                print()
            
            if "context" in results:
                print("Context sources:")
                for i, ctx in enumerate(results["context"][:5], 1):
                    source = ctx.get("source", "unknown")
                    print(f"  [{i}] {source}")
                print()
                
    except Exception as e:
        logger.error(f"Query failed: {e}")
        sys.exit(1)


def cmd_ingest(args):
    """Ingest documents into the knowledge base."""
    from rag_manager import ingest_data
    
    logger.info(f"Ingesting from: {args.path} (force={args.force})")
    
    try:
        ingest_data(
            data_directory=args.path,
            force=args.force
        )
        print("Ingestion complete.")
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)


def cmd_chat(args):
    """Interactive chat mode."""
    from assistants import get_assistant_store, get_thread_store, MessageRole
    from rag_manager import query_knowledge_base
    
    print("\n" + "="*60)
    print("Librarian Interactive Chat")
    print("Type 'exit' or 'quit' to end, 'help' for commands")
    print("="*60 + "\n")
    
    # Setup
    asst_store = get_assistant_store()
    thread_store = get_thread_store()
    
    assistant = asst_store.get_or_create_default(args.assistant)
    thread = thread_store.create()
    thread.assistant_id = assistant.id
    thread_store.update(thread)
    
    print(f"Assistant: {assistant.name}")
    print(f"Thread: {thread.id}")
    print(f"Mode: {assistant.config.search_mode}\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ("exit", "quit"):
                print("\nGoodbye!")
                break
            
            if user_input.lower() == "help":
                print("\nCommands:")
                print("  exit/quit - Exit chat")
                print("  mode <mode> - Change search mode")
                print("  clear - Clear thread history")
                print("  history - Show message history\n")
                continue
            
            if user_input.lower().startswith("mode "):
                new_mode = user_input[5:].strip()
                if new_mode in ("foundation", "lateral", "factcheck"):
                    assistant.config.search_mode = new_mode
                    asst_store.update(assistant)
                    print(f"Mode changed to: {new_mode}\n")
                else:
                    print("Invalid mode. Use: foundation, lateral, factcheck\n")
                continue
            
            if user_input.lower() == "clear":
                thread = thread_store.create()
                thread.assistant_id = assistant.id
                thread_store.update(thread)
                print(f"New thread: {thread.id}\n")
                continue
            
            if user_input.lower() == "history":
                print("\nMessage history:")
                for msg in thread.messages:
                    role = msg.role.value.upper()
                    print(f"  [{role}] {msg.content[:100]}...")
                print()
                continue
            
            # Process query
            thread_store.add_message(thread.id, MessageRole.USER, user_input)
            
            results = query_knowledge_base(
                user_input,
                mode=assistant.config.search_mode
            )
            
            response = results.get("answer", json.dumps(results, indent=2))
            thread_store.add_message(thread.id, MessageRole.ASSISTANT, response)
            
            print(f"\nLibrarian: {response}\n")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            print(f"\nError: {e}\n")


def cmd_serve(args):
    """Start the MCP server."""
    logger.info(f"Starting MCP server on port {args.port}")
    
    try:
        # Import and run MCP server
        import mcp_server
        mcp_server.mcp.run()
    except Exception as e:
        logger.error(f"Server failed: {e}")
        sys.exit(1)


def cmd_graph(args):
    """Run the LangGraph agent."""
    from graph import compile_graph, AgentState
    from langchain_core.messages import HumanMessage
    
    logger.info(f"Running graph: {args.query}")
    
    try:
        # Compile graph
        graph = compile_graph(
            checkpointer_type=args.memory,
            interrupt_before=["response"] if args.hitl else None
        )
        
        # Create initial state
        config = {"configurable": {"thread_id": args.thread or "cli-thread"}}
        
        initial_state = {
            "messages": [HumanMessage(content=args.query)],
            "query": args.query,
            "mode": args.mode
        }
        
        # Run graph
        result = graph.invoke(initial_state, config)
        
        if args.json:
            # Convert messages for JSON serialization
            output = {
                "query": result.get("query"),
                "answer": result.get("answer"),
                "mode": result.get("mode"),
                "documents": result.get("documents", [])[:3]
            }
            print(json.dumps(output, indent=2))
        else:
            print(f"\nAnswer: {result.get('answer', 'No answer generated')}\n")
            
    except Exception as e:
        logger.error(f"Graph execution failed: {e}")
        sys.exit(1)


def cmd_status(args):
    """Show system status."""
    from retrieval import get_retriever
    from tracing import TracingConfig
    
    print("\n" + "="*60)
    print("Librarian System Status")
    print("="*60 + "\n")
    
    # Retrieval status
    try:
        retriever = get_retriever()
        health = retriever.health_check()
        print("Retrieval Layer:")
        print(f"  Status: {health.get('status', 'unknown')}")
        print(f"  Collection: {health.get('collection', 'N/A')}")
        print(f"  Documents: {health.get('document_count', 'N/A')}")
        print(f"  Embedding: {health.get('embedding_model', 'N/A')}")
        print()
    except Exception as e:
        print(f"Retrieval Layer: Error - {e}\n")
    
    # Tracing status
    try:
        config = TracingConfig.from_env()
        print("Tracing:")
        print(f"  Backend: {config.backend.value}")
        print(f"  Project: {config.project_name}")
        print()
    except Exception as e:
        print(f"Tracing: Error - {e}\n")
    
    # Assistants status
    try:
        from assistants import get_assistant_store, get_thread_store
        asst_store = get_assistant_store()
        thread_store = get_thread_store()
        
        print("Assistants:")
        print(f"  Assistants: {len(asst_store.list())}")
        print(f"  Threads: {len(thread_store.list())}")
        print()
    except Exception as e:
        print(f"Assistants: Error - {e}\n")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="librarian",
        description="Librarian Agent - Research assistant with RAG and lateral thinking"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Query the knowledge base")
    query_parser.add_argument("query", help="Query text")
    query_parser.add_argument(
        "-m", "--mode",
        choices=["foundation", "lateral", "factcheck"],
        default="foundation",
        help="Search mode"
    )
    query_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )
    query_parser.set_defaults(func=cmd_query)
    
    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest documents")
    ingest_parser.add_argument(
        "path",
        nargs="?",
        default="./data",
        help="Path to data directory"
    )
    ingest_parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="Force rebuild database"
    )
    ingest_parser.set_defaults(func=cmd_ingest)
    
    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Interactive chat mode")
    chat_parser.add_argument(
        "-a", "--assistant",
        default="librarian",
        help="Assistant preset (librarian, scholar, fact_checker)"
    )
    chat_parser.set_defaults(func=cmd_chat)
    
    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start MCP server")
    serve_parser.add_argument(
        "-p", "--port",
        type=int,
        default=8000,
        help="Server port"
    )
    serve_parser.set_defaults(func=cmd_serve)
    
    # Graph command
    graph_parser = subparsers.add_parser("graph", help="Run LangGraph agent")
    graph_parser.add_argument("query", help="Query text")
    graph_parser.add_argument(
        "-m", "--mode",
        choices=["foundation", "lateral", "factcheck"],
        default="foundation",
        help="Search mode"
    )
    graph_parser.add_argument(
        "--memory",
        choices=["memory", "sqlite", "postgres"],
        default="memory",
        help="Checkpointer type"
    )
    graph_parser.add_argument(
        "--thread",
        help="Thread ID for persistence"
    )
    graph_parser.add_argument(
        "--hitl",
        action="store_true",
        help="Enable human-in-the-loop"
    )
    graph_parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )
    graph_parser.set_defaults(func=cmd_graph)
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show system status")
    status_parser.set_defaults(func=cmd_status)
    
    # Parse and execute
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
